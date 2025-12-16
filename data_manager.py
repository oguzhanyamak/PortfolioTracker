import requests
from lxml import html
import pandas as pd
import os
import json
from datetime import datetime
from config import TEFAS_URL, XPATH_PRICE, XPATH_DAILY_RETURN, XPATH_CATEGORY, HISTORY_FILE
from db_manager import (
    load_funds_from_db,
    save_fund_to_db,
    save_all_funds_to_db,
    delete_fund_from_db,
    save_daily_total_to_db,
    get_history_from_db
)

FUNDS_FILE = "funds.json"  # Kept for backward compatibility, not used

def load_funds():
    """Loads funds from MongoDB."""
    return load_funds_from_db()

def save_fund(code, qty):
    """Adds or updates a fund in MongoDB."""
    return save_fund_to_db(code, qty)

def save_all_funds(funds_list):
    """Overwrites funds in MongoDB with the provided list."""
    return save_all_funds_to_db(funds_list)

def delete_fund(code):
    """Deletes a fund from MongoDB."""
    return delete_fund_from_db(code)


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
    # Normalize codes: handle cases where data_editor returns lists
    normalized_codes = []
    for f in funds_config:
        kod = f.get("kod")
        # If kod is a list, take first element; otherwise use as-is
        if isinstance(kod, list):
            kod = kod[0] if kod else None
        if kod:
            normalized_codes.append(str(kod).strip().upper())
    
    unique_codes = list(set(normalized_codes))
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
        kod = fund.get("kod")
        adet = fund.get("adet")
        
        # Normalize kod (handle list values from data_editor)
        if isinstance(kod, list):
            kod = kod[0] if kod else None
        if kod:
            kod = str(kod).strip().upper()
        else:
            continue
            
        # Normalize adet
        if isinstance(adet, list):
            adet = adet[0] if adet else 0
        
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
    """Saves today's total value to MongoDB for historical tracking."""
    return save_daily_total_to_db(total_value)

def get_history_df():
    """Get portfolio history from MongoDB."""
    return get_history_from_db()

