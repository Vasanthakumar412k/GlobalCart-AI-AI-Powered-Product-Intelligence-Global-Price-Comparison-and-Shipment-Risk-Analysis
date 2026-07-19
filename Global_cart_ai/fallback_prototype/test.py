import os
import streamlit as st
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import urlparse
from webdriver_manager.chrome import ChromeDriverManager
import google.generativeai as genai

# Configure Gemini API
API_KEY = "AIzaSyDnf4Ft6hpx4dLGD45AkQ5mCaXFCuZ_VKI"
genai.configure(api_key=API_KEY)

# --- SCRAPER FUNCTION ---
def scrape(url):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless") # Run headless for smoother UX in Streamlit
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

        # iHerb scraper
        if "iherb" in domain:
            title = soup.select_one("h1")
            data["product_name"] = title.text.strip() if title else "Unknown Product"
            price = soup.select_one("b.discount-price")
            if price:
                price_text = price.text.replace("₹", "").replace(",", "").strip()
                data["price"] = float(price_text)
                data["currency"] = "INR"
            data["website"] = "iherb"

        # SHEIN scraper
        elif "shein" in domain:
            title = soup.select_one("h1")
            data["product_name"] = title.text.strip() if title else "Unknown Product"
            price = soup.select_one("div.prod-sp")
            if price:
                price_text = price.get_text().replace("MRP", "").replace("₹", "").replace(",", "").strip()
                try:
                    data["price"] = float(price_text)
                    data["currency"] = "INR"
                except:
                    data["price"] = None
                    data["currency"] = "INR"

            all_detail_lists = soup.select(".detail-list")
            extracted_details = []
            for detail_list in all_detail_lists:
                items = [item.get_text(strip=True) for item in detail_list.find_all(text=True) if item.strip()]
                if items:
                    extracted_details.append(", ".join(items))
            data["product_details"] = extracted_details if extracted_details else None
            data["website"] = "shein"
        
        else:
            data["website"] = "unsupported"
            data["domain"] = domain

        return data

    except Exception as e:
        return {"error": f"Scraping failed: {str(e)}"}
    finally:
        driver.quit()

# --- GEMINI AI ANALYSIS FUNCTION ---
def analyze_with_gemini(product_name, website_context="", is_fallback=False):
    # Utilizing gemini-2.5-flash for rapid, analytical processing
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    if is_fallback:
        prompt = f"""
        The user wants to analyze a product from an e-commerce platform (like Amazon, Flipkart, or AliExpress).
        Product Name: {product_name}
        
        Please act as an e-commerce strategy consultant. Perform a deep critical analysis on why this specific type of product might fail to sell or drop in sales velocity.
        
        Provide your analysis using the following strict structure:
        ## 📊 Market Resistance & Sales Blockers
        (Explain why customers hesitate to buy this item or why it might not sell well)
        
        ## ❌ Core Disadvantages & Product Flaws
        (List specific weaknesses, typical consumer complaints, or competitive disadvantages)
        
        ## 💡 Recommended Fixes
        (Actionable advice to turn the sales around)
        """
    else:
        prompt = f"""
        Analyze the following scraped product data from {product_name}:
        Context Details: {website_context}
        
        Act as an e-commerce marketing analyst. Determine why this specific product might not be selling effectively or what barriers to purchase exist based on its details, disadvantages, and typical market reception.
        
        Provide your analysis using the following strict structure:
        ## 📊 Market Resistance & Sales Blockers
        ## ❌ Core Disadvantages & Product Flaws
        ## 💡 Recommended Fixes
        """

    response = model.generate_content(prompt)
    return response.text

# --- STREAMLIT UI ---
st.set_page_config(page_title="Product Sales Velocity Analyzer", page_icon="🛍️", layout="wide")

st.title("🛍️ Product Sales Performance & Disadvantage Analyzer")
st.write("Paste a product link from iHerb or SHEIN to parse data automatically, or analyze products from Amazon, Flipkart, and AliExpress via AI market intelligence.")

url_input = st.text_input("Enter Product URL:", placeholder="https://example.com/product-page")

if url_input:
    # Basic URL parsing to check what flow to route to
    domain = urlparse(url_input).netloc
    
    if "iherb" in domain or "shein" in domain:
        st.info(f"Detected supported direct scraper for {domain}. Extracting page components...")
        
        with st.spinner("Running Selenium web crawler..."):
            scraped_data = scrape(url_input)
            
        if "error" in scraped_data:
            st.error(scraped_data["error"])
        else:
            st.success("Data successfully extracted!")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Raw Extracted Metrics")
                st.write(scraped_data)
                
            with col2:
                st.subheader("Gemini AI Sales Friction Analysis")
                prod_name = scraped_data.get("product_name", "Scraped Product")
                context = str(scraped_data.get("product_details", "")) + f" Price: {scraped_data.get('price','')}"
                
                with st.spinner("Generating marketing friction report..."):
                    analysis = analyze_with_gemini(prod_name, website_context=context, is_fallback=False)
                    st.markdown(analysis)
                    
    else:
        # Fallback manual text injection for larger platforms (Amazon, Flipkart, AliExpress)
        st.warning(f"Direct scraper does not natively support '{domain}'. Switching to AI Market Search flow.")
        product_name_input = st.text_input("Please enter the exact Product Name / Model to trigger the search pipeline:")
        
        if product_name_input:
            if st.button("Run Global Market Intelligence Analysis"):
                with st.spinner(f"Querying Gemini AI for e-commerce trends regarding '{product_name_input}'..."):
                    analysis = analyze_with_gemini(product_name_input, is_fallback=True)
                    st.success("Analysis Compiled!")
                    st.markdown(analysis)