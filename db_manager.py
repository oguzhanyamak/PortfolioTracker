# db_manager.py
"""MongoDB database manager for portfolio tracking."""

import streamlit as st
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

# Global connection cache
_mongo_client = None
_db = None

def get_mongo_connection():
    """Get or create MongoDB connection using Streamlit secrets."""
    global _mongo_client, _db
    
    if _mongo_client is None:
        try:
            # Get credentials from Streamlit secrets
            username = st.secrets.get("mongo_username", "")
            password = st.secrets.get("mongo_password", "")
            cluster = st.secrets.get("mongo_cluster", "cluster0.n4r0v.mongodb.net")
            db_name = st.secrets.get("mongo_db_name", "haberDB")
            
            # Build connection string
            mongo_uri = f"mongodb+srv://{username}:{password}@{cluster}/{db_name}?retryWrites=true&w=majority"
            
            # Create client with connection pooling
            _mongo_client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                maxPoolSize=10
            )
            
            # Test connection
            _mongo_client.admin.command('ping')
            
            # Get database
            _db = _mongo_client[db_name]
            
            print(f"✅ MongoDB connected: {db_name}")
            
        except ConnectionFailure as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise
        except Exception as e:
            print(f"❌ MongoDB error: {e}")
            raise
    
    return _db

def close_mongo_connection():
    """Close MongoDB connection."""
    global _mongo_client, _db
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        _db = None

# --- FUNDS CRUD OPERATIONS ---

def load_funds_from_db() -> List[Dict]:
    """Load all funds from MongoDB."""
    try:
        db = get_mongo_connection()
        funds_collection = db.funds
        
        # Get all funds, exclude MongoDB _id field
        funds = list(funds_collection.find({}, {"_id": 0, "kod": 1, "adet": 1}))
        
        return funds
    except Exception as e:
        print(f"Error loading funds: {e}")
        return []

def save_fund_to_db(code: str, quantity: float) -> bool:
    """Save or update a single fund in MongoDB."""
    try:
        db = get_mongo_connection()
        funds_collection = db.funds
        
        code = code.upper().strip()
        
        # Upsert: update if exists, insert if not
        result = funds_collection.update_one(
            {"kod": code},
            {
                "$set": {
                    "kod": code,
                    "adet": float(quantity),
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        return True
    except Exception as e:
        print(f"Error saving fund {code}: {e}")
        return False

def save_all_funds_to_db(funds_list: List[Dict]) -> bool:
    """Bulk save/update funds to MongoDB."""
    try:
        db = get_mongo_connection()
        funds_collection = db.funds
        
        # Clear existing funds
        funds_collection.delete_many({})
        
        # Prepare documents
        documents = []
        for f in funds_list:
            kod = f.get("kod")
            adet = f.get("adet")
            
            # Normalize kod
            if isinstance(kod, list):
                kod = kod[0] if kod else None
            if not kod or pd.isna(kod):
                continue
                
            # Normalize adet
            if isinstance(adet, list):
                adet = adet[0] if adet else 0
            
            try:
                adet_float = float(adet) if not pd.isna(adet) else 0
                if adet_float > 0:
                    documents.append({
                        "kod": str(kod).upper().strip(),
                        "adet": adet_float,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    })
            except (ValueError, TypeError):
                continue
        
        # Bulk insert
        if documents:
            funds_collection.insert_many(documents)
        
        return True
    except Exception as e:
        print(f"Error bulk saving funds: {e}")
        return False

def delete_fund_from_db(code: str) -> bool:
    """Delete a fund from MongoDB."""
    try:
        db = get_mongo_connection()
        funds_collection = db.funds
        
        code = code.upper().strip()
        result = funds_collection.delete_one({"kod": code})
        
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting fund {code}: {e}")
        return False

# --- PORTFOLIO HISTORY OPERATIONS ---

def save_daily_total_to_db(total_value: float) -> pd.DataFrame:
    """Save today's total value to MongoDB."""
    try:
        db = get_mongo_connection()
        history_collection = db.portfolio_history
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Upsert today's value
        history_collection.update_one(
            {"date": today},
            {
                "$set": {
                    "date": today,
                    "total_value": float(total_value),
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        # Return all history as DataFrame
        return get_history_from_db()
        
    except Exception as e:
        print(f"Error saving daily total: {e}")
        return pd.DataFrame(columns=["Date", "TotalValue"])

def get_history_from_db() -> pd.DataFrame:
    """Get portfolio history from MongoDB."""
    try:
        db = get_mongo_connection()
        history_collection = db.portfolio_history
        
        # Get all history, sorted by date
        history = list(history_collection.find(
            {},
            {"_id": 0, "date": 1, "total_value": 1}
        ).sort("date", 1))
        
        if not history:
            return pd.DataFrame(columns=["Date", "TotalValue"])
        
        # Convert to DataFrame
        df = pd.DataFrame(history)
        df.columns = ["Date", "TotalValue"]
        
        return df
        
    except Exception as e:
        print(f"Error getting history: {e}")
        return pd.DataFrame(columns=["Date", "TotalValue"])
