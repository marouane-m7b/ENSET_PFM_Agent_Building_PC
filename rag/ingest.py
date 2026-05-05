import os
import pandas as pd
from langchain_community.document_loaders import DataFrameLoader
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
import shutil
from dotenv import load_dotenv

load_dotenv()

# Define our paths
DATA_DIR = "data"
CHROMA_PATH = "rag/chroma_db"

def ingest_market_data():
    print("Starting data ingestion from CSVs...")
    print("=" * 60)
    
    # Clear existing ChromaDB to ensure fresh data
    if os.path.exists(CHROMA_PATH):
        print(f"🗑️  Clearing existing ChromaDB at {CHROMA_PATH}...")
        shutil.rmtree(CHROMA_PATH)
        print("✅ Old database cleared")
    
    documents = []
    
    # 1. Read and format all CSVs in the data folder
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".csv"):
            file_path = os.path.join(DATA_DIR, filename)
            df = pd.read_csv(file_path)
            
            # Enhanced text content with stock information
            def create_rich_content(row):
                parts = []
                for col, val in row.items():
                    if col == 'Stock':
                        # Add stock status description
                        if val == 0:
                            parts.append(f"Stock: OUT OF STOCK (0 units)")
                        elif val < 10:
                            parts.append(f"Stock: LIMITED STOCK ({val} units remaining)")
                        else:
                            parts.append(f"Stock: IN STOCK ({val} units available)")
                    else:
                        parts.append(f"{col}: {val}")
                return ', '.join(parts)
            
            df['text_content'] = df.apply(create_rich_content, axis=1)
            
            # Add metadata so the agent knows which category it is looking at
            category = filename.replace('.csv', '').upper()
            df['category'] = category
            
            # Filter out items with 0 stock for better RAG results
            in_stock_count = len(df[df['Stock'] > 0])
            total_count = len(df)
            
            # Load into LangChain document format
            loader = DataFrameLoader(df, page_content_column="text_content")
            docs = loader.load()
            
            # Ensure metadata carries over
            for i, doc in enumerate(docs):
                doc.metadata['category'] = category
                doc.metadata['stock'] = int(df.iloc[i]['Stock'])
                doc.metadata['availability'] = df.iloc[i]['Availability']
                doc.metadata['price'] = float(df.iloc[i]['Price_MAD'])
                
            documents.extend(docs)
            print(f"📦 {category:15} | {in_stock_count:3}/{total_count:3} in stock | {len(docs):3} items loaded")

    # 2. Initialize Ollama Embeddings
    print("\n" + "=" * 60)
    print("🔄 Initializing Ollama embeddings (nomic-embed-text)...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    # 3. Create and save the Chroma Vector Database
    print("🧠 Embedding data into ChromaDB...")
    print("   (This may take 1-2 minutes)")
    vector_db = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    
    print("\n" + "=" * 60)
    print(f"✅ SUCCESS!")
    print(f"📊 Total components embedded: {len(documents)}")
    print(f"💾 Database saved to: {CHROMA_PATH}")
    print(f"🔍 RAG system ready for semantic search with stock awareness")
    print("=" * 60)

if __name__ == "__main__":
    ingest_market_data()