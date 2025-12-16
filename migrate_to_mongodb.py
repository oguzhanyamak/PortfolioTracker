"""
Migration script to transfer existing JSON/CSV data to MongoDB.
Run this once after setting up MongoDB connection in secrets.toml
"""

import json
import os
import pandas as pd
from db_manager import (
    get_mongo_connection,
    save_all_funds_to_db,
    save_daily_total_to_db
)

def migrate_funds():
    """Migrate funds from funds.json to MongoDB."""
    funds_file = "funds.json"
    
    if not os.path.exists(funds_file):
        print("⚠️  funds.json not found, skipping funds migration")
        return
    
    try:
        with open(funds_file, "r", encoding="utf-8") as f:
            funds = json.load(f)
        
        if funds:
            print(f"📦 Migrating {len(funds)} funds to MongoDB...")
            save_all_funds_to_db(funds)
            print("✅ Funds migrated successfully!")
        else:
            print("ℹ️  No funds to migrate")
            
    except Exception as e:
        print(f"❌ Error migrating funds: {e}")

def migrate_history():
    """Migrate portfolio history from CSV to MongoDB."""
    history_file = "portfolio_history.csv"
    
    if not os.path.exists(history_file):
        print("⚠️  portfolio_history.csv not found, skipping history migration")
        return
    
    try:
        df = pd.read_csv(history_file)
        
        if df.empty:
            print("ℹ️  No history to migrate")
            return
        
        print(f"📊 Migrating {len(df)} history records to MongoDB...")
        
        db = get_mongo_connection()
        history_collection = db.portfolio_history
        
        # Convert DataFrame to list of documents
        records = []
        for _, row in df.iterrows():
            records.append({
                "date": row["Date"],
                "total_value": float(row["TotalValue"])
            })
        
        # Bulk insert
        if records:
            history_collection.insert_many(records)
            print(f"✅ {len(records)} history records migrated successfully!")
            
    except Exception as e:
        print(f"❌ Error migrating history: {e}")

def main():
    print("🚀 Starting MongoDB migration...\n")
    
    try:
        # Test connection
        db = get_mongo_connection()
        print(f"✅ Connected to MongoDB: {db.name}\n")
        
        # Migrate data
        migrate_funds()
        print()
        migrate_history()
        
        print("\n✨ Migration completed!")
        print("\n💡 Tip: You can now safely delete funds.json and portfolio_history.csv")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\n🔧 Make sure:")
        print("  1. MongoDB connection is configured in .streamlit/secrets.toml")
        print("  2. MongoDB cluster is accessible")
        print("  3. Database user has write permissions")

if __name__ == "__main__":
    main()
