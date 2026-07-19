from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapers.base_driver import get_driver, extract_clean_html

def scrape(url):
    driver = get_driver()
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        data = {"website": "shein"}

        title = soup.select_one("h1")
        data["product_name"] = title.text.strip() if title else None
        
        price = soup.select_one("div.prod-sp")
        if price:
            price_text = price.get_text().replace("MRP", "").replace("₹", "").replace(",", "").strip()
            try:
                data["price"] = float(price_text)
                data["currency"] = "INR"
            except:
                data["price"] = None
                data["currency"] = "INR"

        data["raw_page_dump"] = extract_clean_html(soup)
        return data
    finally:
        driver.quit()