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
        data = {"website": "iherb"}

        title = soup.select_one("h1")
        data["product_name"] = title.text.strip() if title else None
        
        price = soup.select_one("b.discount-price")
        if price:
            price_text = price.text.replace("₹", "").replace(",", "").strip()
            data["price"] = float(price_text)
            data["currency"] = "INR"

        data["raw_page_dump"] = extract_clean_html(soup)
        return data
    finally:
        driver.quit()