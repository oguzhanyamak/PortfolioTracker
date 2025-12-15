import requests
from lxml import html
import pandas as pd
import os
import json
from datetime import datetime
from config import TEFAS_URL, XPATH_PRICE, XPATH_DAILY_RETURN, XPATH_CATEGORY, HISTORY_FILE

FUNDS_FILE = "funds.json"

def load_funds():
    """Loads funds from the JSON file."""
    if not os.path.exists(FUNDS_FILE):
        return []
    with open(FUNDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_fund(code, qty):
    """Adds or updates a fund in the JSON file."""
    funds = load_funds()
    code = code.upper()
    
    # Check if exists, update if so
    found = False
    for f in funds:
        if f["kod"] == code:
            f["adet"] = qty
            found = True
            break
    
    if not found:
        funds.append({"kod": code, "adet": qty})
        
    with open(FUNDS_FILE, "w", encoding="utf-8") as f:
        json.dump(funds, f, indent=4)

def delete_fund(code):
    """Deletes a fund from the JSON file."""
    funds = load_funds()
    code = code.upper()
    funds = [f for f in funds if f["kod"] != code]
    
    with open(FUNDS_FILE, "w", encoding="utf-8") as f:
        json.dump(funds, f, indent=4)

def save_all_funds(funds_list):
    """Overwrites the JSON file with the provided list of funds."""
    # Ensure standard format (upper case codes, float quantities)
    clean_list = []
    for f in funds_list:
        if f.get("kod") and f.get("adet", 0) > 0:
            clean_list.append({
                "kod": f["kod"].upper(),
                "adet": float(f["adet"])
            })
            
    with open(FUNDS_FILE, "w", encoding="utf-8") as f:
        json.dump(clean_list, f, indent=4)


def fetch_fund_price(fund_code):
    """Fetches the latest price, daily return and category for a single fund code from TEFAS."""
    try:
        response = requests.get(TEFAS_URL, params={"FonKod": fund_code}, timeout=10)
        response.encoding = "utf-8"
        response.raise_for_status()
        
        # TEFAS typically sends UTF-8 but sometimes metadata is missing. 
        # Explicitly decoding confirms we treat bytes as UTF-8.
        html_content = response.content.decode("utf-8")
        tree = html.fromstring(html_content)
        price_result = tree.xpath(XPATH_PRICE)
        return_result = tree.xpath(XPATH_DAILY_RETURN)
        category_result = tree.xpath(XPATH_CATEGORY)
        
        price_val = None
        return_val = 0.0
        category_val = "Diğer"
        
        if price_result:
            text_value = price_result[0].text_content().strip()
            # Turkish locale formatting: 1.234,56 -> float
            price_val = float(text_value.replace(".", "").replace(",", "."))
            
        if return_result:
            text_return = return_result[0].text_content().strip()
            # Format: %0,3999 or %-1,23 -> remove %, replace comma
            clean_return = text_return.replace("%", "").replace(".", "").replace(",", ".")
            return_val = float(clean_return)
            
        if category_result:
            category_val = category_result[0].text_content().strip()

        if price_val is None:
            print(f"Warn: Price not found for {fund_code}")
            return None, None, None
            
        return price_val, return_val, category_val

    except Exception as e:
        print(f"Error fetching {fund_code}: {e}")
        return None, None, None

from concurrent.futures import ThreadPoolExecutor, as_completed

def get_portfolio_data(funds_config):
    """
    Iterates over funds, fetches prices in parallel, and calculates values.
    Returns a DataFrame with details and the total portfolio value.
    """
    data = []
    
    # 1. Identify unique codes to avoid redundant fetching
    unique_codes = list(set(f["kod"] for f in funds_config))
    # Cache stores tuple: (price, daily_return_percent, category)
    price_cache = {}

    # 2. Fetch data in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Map future to fund code
        future_to_code = {executor.submit(fetch_fund_price, code): code for code in unique_codes}
        
        for future in as_completed(future_to_code):
            code = future_to_code[future]
            try:
                price, rate, cat = future.result()
                if price is not None:
                    price_cache[code] = (price, rate, cat)
            except Exception as e:
                print(f"Parallel fetch error for {code}: {e}")

    # 3. Build DataFrame
    for fund in funds_config:
        kod = fund["kod"]
        adet = fund["adet"]
        
        if kod in price_cache:
            fiyat, gunluk_getiri_yuzde, kategori = price_cache[kod]
            
            tutar = fiyat * adet
            
            # Calculate daily gain/loss value
            rate = gunluk_getiri_yuzde
            yesterday_price = fiyat / (1 + rate/100)
            daily_gain = (fiyat - yesterday_price) * adet
            
            data.append({
                "Fon Kodu": kod,
                "Adet": adet,
                "Birim Fiyat": fiyat,
                "Toplam Değer": tutar,
                "Günlük Getiri (%)": rate,
                "Günlük Kazanç (TL)": daily_gain,
                "Kategori": kategori
            })

    return pd.DataFrame(data)

def save_daily_total(total_value):
    """Saves the today's total value to a CSV file for historical tracking."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Check if file exists to read it first
    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
    else:
        df = pd.DataFrame(columns=["Date", "TotalValue"])
    
    # Check if we already have an entry for today, update it if so
    if today in df["Date"].values:
        df.loc[df["Date"] == today, "TotalValue"] = total_value
    else:
        new_row = pd.DataFrame([{"Date": today, "TotalValue": total_value}])
        df = pd.concat([df, new_row], ignore_index=True)
    
    df.to_csv(HISTORY_FILE, index=False)
    return df

def get_history_df():
    if os.path.exists(HISTORY_FILE):
        return pd.read_csv(HISTORY_FILE)
    return pd.DataFrame(columns=["Date", "TotalValue"])
