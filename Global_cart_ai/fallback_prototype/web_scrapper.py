from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import urlparse
from webdriver_manager.chrome import ChromeDriverManager


def scrape(url):

    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    try:
        driver.get(url)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")

        data = {}

        domain = urlparse(url).netloc

        # -----------------------
        # iHerb scraper
        # -----------------------
        if "iherb" in domain:

            title = soup.select_one("h1")
            data["product_name"] = title.text.strip() if title else None

            price = soup.select_one("b.discount-price")

            if price:
                price_text = price.text.replace("₹", "").replace(",", "").strip()
                data["price"] = float(price_text)
                data["currency"] = "INR"

            data["website"] = "iherb"

        # -----------------------
        # SHEIN scraper
        # -----------------------
        elif "shein" in domain:

            title = soup.select_one("h1")
            data["product_name"] = title.text.strip() if title else None

            price = soup.select_one("div.prod-sp")

            if price:
                price_text = (
                    price.get_text()
                    .replace("MRP", "")
                    .replace("₹", "")
                    .replace(",", "")
                    .strip()
                )

                try:
                    data["price"] = float(price_text)
                    data["currency"] = "INR"
                except:
                    data["price"] = None
                    data["currency"] = "INR"

            # --- UPDATED CODE FOR ALL DETAIL-LIST OBJECTS ---
            # .select() finds ALL elements matching the class '.detail-list'
            all_detail_lists = soup.select(".detail-list")
            
            extracted_details = []
            for detail_list in all_detail_lists:
                # Get text chunks inside this specific detail-list object
                items = [
                    item.get_text(strip=True)
                    for item in detail_list.find_all(text=True)
                    if item.strip()
                ]
                if items:
                    # Join them together with commas
                    extracted_details.append(", ".join(items))

            # Store the resulting strings inside the final data dictionary
            data["product_details"] = extracted_details if extracted_details else None
            # ------------------------------------------------

            data["website"] = "shein"

        else:
            data["error"] = "Website not supported"

        return data

    finally:
        driver.quit()