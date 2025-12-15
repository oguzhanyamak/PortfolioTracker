# config.py
# Configuration constants for TEFAS scraping

TEFAS_URL = "https://www.tefas.gov.tr/FonAnaliz.aspx"
XPATH_PRICE = '//*[@id="MainContent_PanelInfo"]/div[1]/ul[1]/li[1]/span'
XPATH_DAILY_RETURN = '//*[@id="MainContent_PanelInfo"]/div[1]/ul[1]/li[2]/span'
XPATH_CATEGORY = '//*[@id="MainContent_PanelInfo"]/div[1]/ul[1]/li[5]/span'
HISTORY_FILE = "portfolio_history.csv"

