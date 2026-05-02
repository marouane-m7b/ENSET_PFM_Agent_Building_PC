"""
Metrics Dashboard for Prompt Evaluation
Provides real-time monitoring and visualization of prompt performance
"""

import json
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import glob

class MetricsDashboard:
    """Dashboard for visualizing prompt evaluation metrics"""
    
    def __init__(self):
        self.results_dir = "evaluation"
        
    def load_evaluation_data(self):
        """Load all evaluation results from files"""
        results_files = glob.glob(f"{self.results_dir}/*results*.json")
        
        if not results_files:
            return None
            
        all_data = []
        for file in results_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    data['file'] = file
                    all_data.append(data)
            except Exception as e:
                st.error(f"Error loading {file}: {e}")
                
        return all_data
    
    def create_performance_comparison(self, data):
        """Create performance comparison chart"""
        if not data:
            return None
            
        # Extract metrics for comparison
        comparison_data = []
        
        for dataset in data:
            if 'results' in dataset:
                for result in dataset['results']:
                    comparison_data.append({
                        'Strategy': result.get('variant_id', 'Unknown'),
                        'Overall Score': result.get('overall_score', 0),
                        'Accuracy': result.get('accuracy_score', 0),
                        'Budget Adherence': result.get('budget_adherence', 0),
                        'Response Time': result.get('response_time', 0),
                        'Timestamp': dataset.get('timestamp', '')
                    })
        
        if not comparison_data:
            return None
            
        df = pd.DataFrame(comparison_data)
        
        # Create grouped bar chart
        fig = px.bar(
            df, 
            x='Strategy', 
            y='Overall Score',
            title='📊 Prompt Strategy Performance Comparison',
            color='Strategy',
            text='Overall Score'
        )
        
        fig.update_traces(texttemplate='%{text:.3f}', textposition='outside')
        fig.update_layout(
            xaxis_title="Prompt Strategy",
            yaxis_title="Overall Performance Score",
            showlegend=False,
            height=500
        )
        
        return fig
    
    def create_metrics_radar(self, data):
        """Create radar chart for multi-dimensional metrics"""
        if not data or not data[0].get('results'):
            return None
            
        # Get the latest results
        latest_results = data[-1]['results']
        
        strategies = []
        metrics = ['accuracy_score', 'budget_adherence', 'component_compatibility', 'user_satisfaction']
        metric_labels = ['Accuracy', 'Budget Adherence', 'Compatibility', 'User Satisfaction']
        
        fig = go.Figure()
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        
        for i, result in enumerate(latest_results):
            strategy_name = result.get('variant_id', f'Strategy {i+1}')
            values = [result.get(metric, 0) for metric in metrics]
            values.append(values[0])  # Close the radar chart
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=metric_labels + [metric_labels[0]],
                fill='toself',
                name=strategy_name,
                line_color=colors[i % len(colors)]
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="🎯 Multi-Dimensional Performance Analysis",
            height=600
        )
        
        return fig
    
    def create_time_series(self, data):
        """Create time series of performance over time"""
        if not data:
            return None
            
        time_data = []
        
        for dataset in data:
            timestamp = dataset.get('timestamp', '')
            if timestamp and 'results' in dataset:
                for result in dataset['results']:
                    time_data.append({
                        'Timestamp': pd.to_datetime(timestamp),
                        'Strategy': result.get('variant_id', 'Unknown'),
                        'Score': result.get('overall_score', 0)
                    })
        
        if not time_data:
            return None
            
        df = pd.DataFrame(time_data)
        
        fig = px.line(
            df, 
            x='Timestamp', 
            y='Score', 
            color='Strategy',
            title='📈 Performance Trends Over Time',
            markers=True
        )
        
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Performance Score",
            height=400
        )
        
        return fig
    
    def create_summary_metrics(self, data):
        """Create summary metrics cards"""
        if not data:
            return None, None, None, None
            
        # Calculate summary statistics
        all_scores = []
        all_times = []
        total_tests = 0
        
        for dataset in data:
            if 'results' in dataset:
                for result in dataset['results']:
                    all_scores.append(result.get('overall_score', 0))
                    all_times.append(result.get('response_time', 0))
                    total_tests += 1
        
        if not all_scores:
            return 0, 0, 0, 0
            
        avg_score = sum(all_scores) / len(all_scores)
        best_score = max(all_scores)
        avg_time = sum(all_times) / len(all_times) if all_times else 0
        
        return avg_score, best_score, avg_time, total_tests

def main():
    """Main dashboard application"""
    st.set_page_config(
        page_title="Prompt Evaluation Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Prompt Evaluation Dashboard")
    st.markdown("Real-time monitoring of prompt performance and A/B testing results")
    
    dashboard = MetricsDashboard()
    
    # Load data
    with st.spinner("Loading evaluation data..."):
        data = dashboard.load_evaluation_data()
    
    if not data:
        st.warning("⚠️ No evaluation data found. Run the evaluation scripts first!")
        st.markdown("""
        To generate data, run:
        ```bash
        python evaluation/prompt_evaluation.py
        python evaluation/ab_testing.py
        ```
        """)
        return
    
    # Summary metrics
    st.subheader("📈 Summary Metrics")
    
    avg_score, best_score, avg_time, total_tests = dashboard.create_summary_metrics(data)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Average Score",
            value=f"{avg_score:.3f}",
            delta=f"{(avg_score - 0.5):.3f}" if avg_score > 0.5 else None
        )
    
    with col2:
        st.metric(
            label="Best Score",
            value=f"{best_score:.3f}",
            delta=f"{(best_score - avg_score):.3f}" if best_score > avg_score else None
        )
    
    with col3:
        st.metric(
            label="Avg Response Time",
            value=f"{avg_time:.2f}s",
            delta=f"{(2.0 - avg_time):.2f}s" if avg_time < 2.0 else None
        )
    
    with col4:
        st.metric(
            label="Total Tests",
            value=str(total_tests),
            delta=None
        )
    
    st.divider()
    
    # Performance comparison
    st.subheader("🏆 Strategy Performance Comparison")
    perf_chart = dashboard.create_performance_comparison(data)
    if perf_chart:
        st.plotly_chart(perf_chart, use_container_width=True)
    else:
        st.info("No performance data available for comparison")
    
    # Multi-dimensional analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Multi-Dimensional Analysis")
        radar_chart = dashboard.create_metrics_radar(data)
        if radar_chart:
            st.plotly_chart(radar_chart, use_container_width=True)
        else:
            st.info("No radar chart data available")
    
    with col2:
        st.subheader("📈 Performance Trends")
        time_chart = dashboard.create_time_series(data)
        if time_chart:
            st.plotly_chart(time_chart, use_container_width=True)
        else:
            st.info("No time series data available")
    
    # Raw data viewer
    st.subheader("📋 Raw Data")
    
    if st.checkbox("Show detailed results"):
        for i, dataset in enumerate(data):
            with st.expander(f"Dataset {i+1} - {dataset.get('timestamp', 'Unknown time')}"):
                st.json(dataset)
    
    # Refresh button
    if st.button("🔄 Refresh Data"):
        st.rerun()
    
    # Footer
    st.divider()
    st.markdown("""
    **📊 Dashboard Features:**
    - Real-time performance monitoring
    - A/B testing results visualization  
    - Multi-dimensional metric analysis
    - Historical trend tracking
    - Detailed data inspection
    """)

if __name__ == "__main__":
    main()