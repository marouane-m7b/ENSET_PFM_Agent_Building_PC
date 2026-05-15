// AI Hardware Architect - Agent-Driven Wizard
const socket = io();

let state = {
    useCase: null, budget: 15000, performance: 'medium',
    chatId: null, threadId: null,
    buildData: null, // from agent
    selectedComponents: {}, // current build (may be modified)
    totalPrice: 0
};

const ICONS = { CPU:'🔲', GPU:'🎮', Motherboard:'🔧', RAM:'💾', Storage:'💿', Cooler:'❄️', PSU:'⚡', Case:'🖥️' };
const $ = id => document.getElementById(id);

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {
    setupWelcome();
    setupSocket();
    createSession();
});

// ===== WELCOME =====
function setupWelcome() {
    document.querySelectorAll('.usecase-card').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('.usecase-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            state.useCase = card.dataset.usecase;
            $('budgetSection').style.display = 'block';
            $('budgetSection').scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    });

    // Budget slider → input sync
    const budgetInput = $('budgetInput');
    const budgetSlider = $('budgetSlider');

    function updateBudget(val) {
        val = Math.max(5000, Math.min(80000, val));
        state.budget = val;
        const b = val;
        $('budgetTier').textContent = b >= 50000 ? 'Ultra High-End' : b >= 30000 ? 'High-End' : b >= 15000 ? 'Mid-Range' : b >= 8000 ? 'Entry-Level' : 'Budget';
    }

    budgetSlider.addEventListener('input', () => {
        const val = parseInt(budgetSlider.value);
        budgetInput.value = val.toLocaleString();
        updateBudget(val);
    });

    // Select all on focus so typing replaces value
    budgetInput.addEventListener('focus', () => {
        budgetInput.select();
    });

    // Budget input → slider sync (no formatting while typing)
    budgetInput.addEventListener('input', () => {
        const raw = budgetInput.value.replace(/[^0-9]/g, '');
        const val = parseInt(raw) || 5000;
        budgetSlider.value = Math.max(5000, Math.min(80000, val));
        updateBudget(val);
    });

    // Format with commas when done typing
    budgetInput.addEventListener('blur', () => {
        const raw = budgetInput.value.replace(/[^0-9]/g, '');
        let val = parseInt(raw) || 5000;
        val = Math.max(5000, Math.min(80000, val));
        budgetInput.value = val.toLocaleString();
        budgetSlider.value = val;
        updateBudget(val);
    });

    // Format initial value
    budgetInput.value = '15,000';

    document.querySelectorAll('.perf-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.perf-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.performance = btn.dataset.perf;
        });
    });

    $('startBuildBtn').addEventListener('click', startAIBuild);
}

// ===== SESSION =====
async function createSession() {
    try {
        const res = await fetch('/api/chat/new', { method: 'POST', headers: { 'Content-Type': 'application/json' } });
        const data = await res.json();
        if (!data.error) { state.chatId = data.chat_id; state.threadId = data.thread_id; }
    } catch (e) { console.log('Session will be created on demand'); }
}

// ===== START AI BUILD =====
function startAIBuild() {
    if (!state.useCase) { showNotif('Please select a use case', 'error'); return; }

    showScreen('screenBuilding');
    // Reset workflow nodes
    setNode('wfArchitect', 'active', 'Analyzing requirements...');
    setNode('wfProcurement', '', 'Waiting...');
    setNode('wfApproval', '', 'Waiting...');
    $('wfArchitectDetail').textContent = '';
    $('wfProcurementDetail').textContent = '';
    $('wfConn1').className = 'wf-connector';
    $('wfConn2').className = 'wf-connector';
    animateLoader();

    // Send to agent pipeline
    const msg = `Build me a ${state.useCase.replace('_',' ')} PC with a budget of ${state.budget} MAD, ${state.performance} performance`;

    if (!state.chatId) {
        createSession().then(() => {
            socket.emit('send_message', { chat_id: state.chatId, message: msg });
        });
    } else {
        socket.emit('send_message', { chat_id: state.chatId, message: msg });
    }
}

function animateLoader() {
    const fill = $('loaderFill');
    fill.style.width = '0%';
    let w = 0;
    const interval = setInterval(() => {
        w += 0.5;
        if (w > 90) { clearInterval(interval); return; }
        fill.style.width = w + '%';
    }, 100);
    window._loaderInterval = interval;
}

function finishLoader() {
    if (window._loaderInterval) clearInterval(window._loaderInterval);
    $('loaderFill').style.width = '100%';
}

// ===== SOCKET =====
function setupSocket() {
    socket.on('agent_status', (data) => {
        if (data.stage === 'architect') {
            if (data.status === 'processing') {
                setNode('wfArchitect', 'active', 'Analyzing...');
            } else if (data.status === 'completed') {
                setNode('wfArchitect', 'done', 'Done ✓');
                $('wfConn1').classList.add('done');
                setNode('wfProcurement', 'active', 'Selecting components...');
                if (data.data) {
                    $('wfArchitectDetail').textContent = 
                        `Budget: ${(data.data.budget||0).toLocaleString()} MAD | Use: ${data.data.use_case||''} | Perf: ${data.data.performance_level||''}`;
                }
            }
        } else if (data.stage === 'procurement') {
            if (data.status === 'processing') {
                setNode('wfProcurement', 'active', 'Optimizing build...');
            } else if (data.status === 'completed') {
                setNode('wfProcurement', 'done', 'Done ✓');
                $('wfConn2').classList.add('done');
                setNode('wfApproval', 'active', 'Your turn!');
                if (data.data) {
                    state.buildData = data.data;
                    state.selectedComponents = JSON.parse(JSON.stringify(data.data.selected_components || {}));
                    state.totalPrice = data.data.total_price || 0;
                    $('wfProcurementDetail').textContent = 
                        `${Object.keys(state.selectedComponents).length} components | Total: ${state.totalPrice.toLocaleString()} MAD`;
                }
            }
        } else if (data.stage === 'approval' && data.status === 'waiting') {
            // Don't auto-approve — show summary for user decision
        } else if (data.stage === 'inventory' || data.stage === 'discord' || data.stage === 'complete') {
            if (data.stage === 'complete') {
                finishLoader();
                setTimeout(() => showResult(true), 500);
            }
        }
    });

    socket.on('approval_needed', (data) => {
        finishLoader();
        // Show the build for user to approve or reject
        setTimeout(() => showSummary(), 500);
    });

    socket.on('message', (data) => {
        // Agent message received (build quote)
        if (data.role === 'assistant' && data.content.includes('approved')) {
            // Approval was processed
        }
    });

    socket.on('discord_sent', (data) => {
        showNotif(data.success ? '✅ Build sent to Discord!' : '❌ Discord failed', data.success ? 'success' : 'error');
    });

    socket.on('error', (data) => {
        showNotif('Error: ' + data.error, 'error');
        // If we have build data, still show summary
        if (state.selectedComponents && Object.keys(state.selectedComponents).length > 0) {
            finishLoader();
            showSummary();
        }
    });
}

// ===== SUMMARY SCREEN =====
function showSummary() {
    showScreen('screenSummary');
    renderBuildList($('buildComponents'), state.selectedComponents);

    const total = calcTotal();
    const pct = ((total / state.budget) * 100).toFixed(1);
    $('totalCost').textContent = total.toLocaleString() + ' MAD';
    $('budgetUsed').textContent = pct + '%';
    $('budgetRemaining').textContent = (state.budget - total).toLocaleString() + ' MAD';

    $('approveBtn').onclick = () => approveAndSend();
    $('rejectBtn').onclick = () => showModifyScreen();
    $('exportBtn').onclick = exportBuild;
    $('shareExportBtn').onclick = shareBuild;
}

function renderBuildList(container, components) {
    container.innerHTML = Object.entries(components).map(([cat, comp]) => `
        <div class="build-item">
            <div class="build-item-icon">${ICONS[cat]||'📦'}</div>
            <div class="build-item-info">
                <div class="build-item-cat">${cat}</div>
                <div class="build-item-name">${comp.Brand} ${comp.Model}</div>
            </div>
            <div class="build-item-price">${(comp.Price_MAD||0).toLocaleString()} MAD</div>
        </div>
    `).join('');
}

function calcTotal() {
    state.totalPrice = Object.values(state.selectedComponents).reduce((s, c) => s + (c.Price_MAD || 0), 0);
    return state.totalPrice;
}

// ===== APPROVE & SEND TO DISCORD =====
function approveAndSend() {
    showNotif('Approving build and sending to Discord...', 'info');

    socket.emit('approve_build', {
        chat_id: state.chatId,
        feedback: '',
        build_data: {
            selected_components: state.selectedComponents,
            total_price: calcTotal(),
            budget: state.budget,
            use_case: state.useCase,
            performance_level: state.performance
        }
    });

    // Show result after short delay
    setTimeout(() => showResult(true), 2000);
}

// ===== MODIFY SCREEN =====
function showModifyScreen() {
    showScreen('screenModify');

    $('modifyBackBtn').onclick = () => showSummary();
    $('altClose').onclick = () => { $('alternativesPanel').style.display = 'none'; };
    $('modifyApproveBtn').onclick = () => {
        // Re-approve with modified components
        approveAndSend();
    };

    renderModifyList();
}

function renderModifyList() {
    const container = $('modifyComponents');
    container.innerHTML = Object.entries(state.selectedComponents).map(([cat, comp]) => `
        <div class="modify-item" data-category="${cat}" onclick="loadAlternatives('${cat}')">
            <div class="modify-item-icon">${ICONS[cat]||'📦'}</div>
            <div class="modify-item-info">
                <div class="modify-item-cat">${cat}</div>
                <div class="modify-item-name">${comp.Brand} ${comp.Model}</div>
            </div>
            <div class="modify-item-price">${(comp.Price_MAD||0).toLocaleString()} MAD</div>
            <div class="modify-item-action">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                <span>See 3 alternatives</span>
            </div>
        </div>
    `).join('');
}

// ===== LOAD ALTERNATIVES =====
window.loadAlternatives = async function(category) {
    const comp = state.selectedComponents[category];
    if (!comp) return;

    $('altTitle').textContent = `Alternatives for ${category}`;
    $('alternativesPanel').style.display = 'block';
    $('altCards').innerHTML = '<div class="alt-loading">🤖 Finding alternatives near ' + comp.Price_MAD.toLocaleString() + ' MAD...</div>';

    // Scroll to panel
    $('alternativesPanel').scrollIntoView({ behavior: 'smooth', block: 'center' });

    const catMap = { CPU:'cpus', GPU:'gpus', Motherboard:'motherboards', RAM:'ram', Storage:'storage', Cooler:'coolers', PSU:'psus', Case:'cases' };

    try {
        const res = await fetch('/api/components/alternatives', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                category: catMap[category],
                current_model: comp.Model,
                current_brand: comp.Brand,
                current_price: comp.Price_MAD,
                selected: state.selectedComponents
            })
        });
        const data = await res.json();
        renderAlternatives(category, data.options || []);
    } catch (e) {
        $('altCards').innerHTML = '<div class="alt-loading">Error loading alternatives</div>';
    }
};

function renderAlternatives(category, options) {
    const container = $('altCards');
    if (options.length === 0) {
        container.innerHTML = '<div class="alt-loading">No alternatives found</div>';
        return;
    }

    container.innerHTML = options.map((opt, i) => {
        const specs = getKeySpecs(opt, category);
        const stockClass = opt.Stock <= 0 ? 'stock-out' : opt.Stock < 10 ? 'stock-limited' : 'stock-in';
        return `
        <div class="alt-card" onclick="swapComponent('${category}', ${i})">
            <div class="alt-card-header">
                <div class="alt-card-name">${opt.Brand} ${opt.Model}</div>
                <div class="alt-card-price">${(opt.Price_MAD||0).toLocaleString()} MAD</div>
            </div>
            <div class="alt-card-specs">${specs}</div>
            <div class="alt-card-stock"><span class="stock-dot ${stockClass}"></span>${opt.Stock < 10 ? 'Low Stock ('+opt.Stock+')' : 'In Stock'}</div>
        </div>`;
    }).join('');

    window._altOptions = options;
}

function getKeySpecs(item, cat) {
    switch(cat) {
        case 'CPU': return `${item.Cores}C/${item.Threads}T • ${(item.Boost_Clock_MHz/1000).toFixed(1)}GHz • ${item.Socket}`;
        case 'GPU': return `${item.VRAM_GB}GB ${item.Memory_Type} • ${item.Series}`;
        case 'Motherboard': return `${item.Chipset} • ${item.Socket} • ${item.Form_Factor}`;
        case 'RAM': return `${item.Capacity} • ${item.Speed_MHz}MHz • ${item.Type}`;
        case 'Storage': return `${item.Capacity} • ${item.Type} • ${item.Gen}`;
        case 'Cooler': return `${item.Type} • ${item.Size}`;
        case 'PSU': return `${item.Wattage} • ${item.Efficiency}`;
        case 'Case': return `${item.Form_Factor} • ${item.Brand}`;
        default: return '';
    }
}

// ===== SWAP COMPONENT =====
window.swapComponent = function(category, index) {
    const opts = window._altOptions;
    if (!opts || !opts[index]) return;

    state.selectedComponents[category] = opts[index];
    showNotif(`${category} swapped to ${opts[index].Brand} ${opts[index].Model}`, 'success');

    $('alternativesPanel').style.display = 'none';
    renderModifyList();
};

// ===== RESULT =====
function showResult(success) {
    showScreen('screenResult');
    $('resultIcon').textContent = success ? '🎉' : '❌';
    $('resultTitle').textContent = success ? 'Build Approved & Sent!' : 'Build Failed';
    $('resultMessage').textContent = success
        ? 'Your PC build has been approved, inventory updated, and details sent to Discord.'
        : 'Something went wrong. Please try again.';
    $('resultNewBuild').onclick = resetBuild;
}

// ===== UTILS =====
function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => { s.style.display = 'none'; s.classList.remove('active'); });
    $(id).style.display = 'flex'; $(id).classList.add('active');
    window.scrollTo(0, 0);
}

function setNode(id, cls, status) {
    const node = $(id);
    node.classList.remove('active', 'done');
    if (cls) node.classList.add(cls);
    node.querySelector('.wf-node-status').textContent = status;
}

function resetBuild() {
    state = { useCase: null, budget: 15000, performance: 'medium', chatId: null, threadId: null, buildData: null, selectedComponents: {}, totalPrice: 0 };
    document.querySelectorAll('.usecase-card').forEach(c => c.classList.remove('selected'));
    $('budgetSection').style.display = 'none';
    $('budgetSlider').value = 15000;
    $('budgetInput').value = '15,000';
    showScreen('screenWelcome');
    createSession();
}

function exportBuild() {
    const blob = new Blob([JSON.stringify({ use_case: state.useCase, budget: state.budget, performance: state.performance, total: state.totalPrice, components: state.selectedComponents }, null, 2)], { type: 'application/json' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `pc-build-${Date.now()}.json`; a.click();
    showNotif('Build exported', 'success');
}

function shareBuild() {
    let text = `🖥️ My PC Build (${state.totalPrice.toLocaleString()} MAD)\n\n`;
    for (const [c, comp] of Object.entries(state.selectedComponents)) text += `${c}: ${comp.Brand} ${comp.Model}\n`;
    text += `\nBuilt with AI Hardware Architect`;
    if (navigator.share) { navigator.share({ title: 'My PC Build', text }); }
    else { navigator.clipboard.writeText(text).then(() => showNotif('Copied!', 'success')); }
}

function showNotif(msg, type = 'info') {
    const el = document.createElement('div');
    el.className = `notification notif-${type}`;
    el.textContent = msg;
    $('notificationContainer').appendChild(el);
    setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 300); }, 3500);
}
