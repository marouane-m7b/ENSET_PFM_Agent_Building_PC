import os
import pandas as pd
from langchain_community.document_loaders import DataFrameLoader
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

# Define our paths
DATA_DIR = "data"
CHROMA_PATH = "rag/chroma_db"

def ingest_market_data():
    print("Starting data ingestion from CSVs...")
    documents = []
    
    # 1. Read and format all CSVs in the data folder
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".csv"):
            file_path = os.path.join(DATA_DIR, filename)
            df = pd.read_csv(file_path)
            
            # Combine all columns into a single descriptive string for the AI to read
            # Example output: "Brand: AMD, Model: Ryzen 7 5700X, Price_MAD: 2100, Availability: In Stock"
            df['text_content'] = df.apply(lambda row: ', '.join([f"{col}: {val}" for col, val in row.items()]), axis=1)
            
            # Add metadata so the agent knows which category it is looking at
            category = filename.replace('.csv', '').upper()
            df['category'] = category
            
            # Load into LangChain document format
            loader = DataFrameLoader(df, page_content_column="text_content")
            docs = loader.load()
            
            # Ensure metadata carries over
            for doc in docs:
                doc.metadata['category'] = category
                
            documents.extend(docs)
            print(f"Loaded {len(df)} items from {filename}")

    # 2. Initialize our local Ollama Embeddings
    print("\nInitializing local embeddings (nomic-embed-text)...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    # 3. Create and save the Chroma Vector Database
    print("Embedding data into ChromaDB... this might take a minute depending on your GPU.")
    vector_db = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    
    print(f"\nSuccess! {len(documents)} total components embedded and saved to {CHROMA_PATH}")

if __name__ == "__main__":
    ingest_market_data()