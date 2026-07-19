import os
import json
import streamlit as st
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from google import genai

# --- STREAMLIT PAGE CONFIG ---
st.set_page_config(page_title="Global Logistics & E-Commerce AI Engine", page_icon="📦", layout="wide")

# Initialize Gemini Client
if "GEMINI_API_KEY" in os.environ:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
else:
    st.warning("⚠️ Gemini API Key not found. Please ensure GEMINI_API_KEY is configured in your system environment.")
    client = None

# --- YOUR SCRAPER (VISIBLE WINDOW MODE) ---
def scrape(url):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        data = {}
        domain = urlparse(url).netloc

        if "iherb" in domain:
            title = soup.select_one("h1")
            data["product_name"] = title.text.strip() if title else None
            price = soup.select_one("b.discount-price")
            if price:
                price_text = price.text.replace("₹", "").replace(",", "").strip()
                data["price"] = float(price_text)
                data["currency"] = "INR"
            data["website"] = "iherb"

        elif "shein" in domain:
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
            data["website"] = "shein"

        elif "aliexpress" in domain:
            title = soup.select_one("h1")
            data["product_name"] = title.text.strip() if title else None
            price_element = soup.select_one('[class*="price"], [id*="price"]')
            if price_element:
                try:
                    clean_p = price_element.text.replace("$", "").replace("₹", "").replace(",", "").strip()
                    data["price"] = float(clean_p)
                except:
                    data["price"] = None
            else:
                data["price"] = None
            data["website"] = "aliexpress"
        else:
            data["error"] = "Website not supported"

        if "error" not in data:
            for junk in soup(["script", "style", "noscript"]):
                junk.extract()
            data["raw_page_dump"] = soup.get_text(separator="\n", strip=True)[:5000]

        return data
    finally:
        driver.quit()

# --- INITIALIZE UI SESSION STATES ---
if "parsed_json" not in st.session_state:
    st.session_state.parsed_json = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_website" not in st.session_state:
    st.session_state.current_website = ""

st.title("📦 Global Logistics & Import Intelligence Engine")

# --- STAGE 1: MULTI-MODE INPUT BAR ---
user_input = st.text_input("🔗 Paste an item link OR type a generic product name (e.g., 'iphone 12'):", 
                           placeholder="https://... OR 'iphone 12'")

if st.button("🚀 Process Intelligence Analysis", use_container_width=True):
    if not client:
        st.error("Please configure your Gemini API Key first.")
    elif user_input:
        st.session_state.parsed_json = None
        st.session_state.current_website = ""
        
        is_url = user_input.strip().startswith(("http://", "https://", "www."))
        
        if is_url:
            target_url = user_input if user_input.strip().startswith(("http://", "https://")) else f"https://{user_input.strip()}"
            with st.spinner("🌐 URL detected. Launching browser scraper..."):
                scraped_data = scrape(target_url)
                
            if "error" not in scraped_data and scraped_data.get("product_name"):
                st.session_state.current_website = scraped_data["website"]
                
                with st.spinner("🤖 Scrape complete! Processing with Gemini..."):
                    master_prompt = f"""
                    You are an international logistics intelligence engine. A local scraper extracted these details:
                    - Store Source: {scraped_data['website'].upper()}
                    - Product Title: {scraped_data['product_name']}
                    - Scraped Base Price: {scraped_data.get('price', '0')} INR
                    
                    Format your response ONLY with this JSON template:
                    {{
                      "is_search_mode": false,
                      "product_name": "{scraped_data.get('product_name')}",
                      "why_used": "Explain the purpose of this product",
                      "benefits": "List 3 core functional benefits",
                      "worth_buying": "YES or NO - followed by justification",
                      "common_complaints": "List common user complaints associated with this category",
                      "base_price": "{scraped_data.get('price', '0')}",
                      "shipping_price": "Estimated shipping to India in INR as an integer",
                      "import_charges": "Calculated customs/GST fee in INR as an integer",
                      "transit_risks": "List potential clearance bottlenecks or tracking risks",
                      "eta": "Basic delivery timeframe range",
                      "cheaper_alternative": "Compare value vs importing alternative channels"
                    }}
                    """
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=master_prompt)
            else:
                st.error(f"Scraper error: {scraped_data.get('error', 'Could not locate elements.')}")
                
        else:
            # 🌟 ROUTE 2: KEYWORD SEARCH TO SPLIT E-COMMERCE COMPARISON
            st.session_state.current_website = "search_mode"
            with st.spinner(f"🔍 Compiling multi-platform data arrays for '{user_input}'..."):
                search_prompt = f"""
                The user wants a localized e-commerce pricing analysis for this specific product: "{user_input}".
                Estimate the approximate local market metrics for India across Amazon India, Flipkart, and cross-border AliExpress.
                
                Respond ONLY with a raw JSON object matching this exact structure (no markdown code blocks):
                {{
                  "is_search_mode": true,
                  "product_name": "{user_input}",
                  "why_used": "Explain the core purpose of this product",
                  "benefits": "List 3 functional advantages or hardware specifications of this item",
                  "worth_buying": "YES or NO - provide a clear value evaluation considering current technology or trends",
                  "common_complaints": "List common historical user defects or hardware performance complaints",
                  
                  "amazon": {{
                    "base_price": "[Estimated average item listing price on Amazon India in INR as an integer, e.g., 34000]",
                    "shipping_price": "[Standard delivery fee for non-prime or base shipping to a tier-1 Indian city in INR, e.g., 40]",
                    "import_charges": "0",
                    "eta": "[Delivery window, e.g., 2-4 Days]"
                  }},
                  "flipkart": {{
                    "base_price": "[Estimated item listing price on Flipkart in INR as an integer, e.g., 33500]",
                    "shipping_price": "[Standard local secure packaging/delivery fee in INR, e.g., 40]",
                    "import_charges": "0",
                    "eta": "[Delivery window, e.g., 2-5 Days]"
                  }},
                  "aliexpress": {{
                    "base_price": "[Estimated product cost converted from USD to INR as an integer, e.g., 26000]",
                    "shipping_price": "[Estimated third-party freight forwarding or specialized transit handler cost into India in INR, e.g., 750]",
                    "import_charges": "[Calculated 2026 personal import duty framework layer of 10% customs + 18% IGST on combined price in INR]",
                    "eta": "[International forwarding arrival range, e.g., 15-30 Days]"
                  }},
                  
                  "cheaper_alternative": "Direct summary analysis of which option yields the highest value vs total risk profile",
                  "transit_risks": "Contrast domestic transport protection vs global delivery clearance seizures"
                }}
                """
                response = client.models.generate_content(model='gemini-2.5-flash', contents=search_prompt)

        if 'response' in locals():
            try:
                clean_json_str = response.text.strip().replace("```json", "").replace("```", "")
                st.session_state.parsed_json = json.loads(clean_json_str)
                st.session_state.chat_history = []
            except Exception as json_err:
                st.error("Failed to parse cross-border pricing matrices.")

# --- STAGE 3: THE STRUCKUI DISPLAY ---
if st.session_state.parsed_json:
    data = st.session_state.parsed_json
    
    # 🌟 TEXT LOOKUP/SEARCH MODE FRONTEND
    if data.get("is_search_mode") == True:
        st.markdown(f"## 📊 Marketplace Cost & Logistics Grid: {data.get('product_name').upper()}")
        
        # Open 3 equal columns for Amazon, Flipkart, and AliExpress side-by-side
        amz_col, flpk_col, ali_col = st.columns(3)
        
        with amz_col:
            st.markdown(
                f"""<div style="background-color:#1E1E1E; padding:20px; border-radius:10px; border-top: 5px solid #FF9900; min-height:360px;">
                    <h3 style="margin:0 0 15px 0; color:#FF9900; text-align:center;">AMAZON INDIA</h3>
                    <hr style="border:0.5px solid #333; margin:10px 0;">
                    <p style="margin:5px 0; font-size:15px; color:#AAA;">BASE ITEM PRICE:</p>
                    <p style="margin:0 0 15px 0; font-size:26px; font-weight:bold; color:#FFF;">₹{int(data['amazon']['base_price']):,}</p>
                    <p style="margin:5px 0; font-size:15px; color:#AAA;">EST. DELIVERY CHARGE:</p>
                    <p style="margin:0 0 15px 0; font-size:22px; font-weight:bold; color:#FFF;">Extra: ₹{int(data['amazon']['shipping_price']):,}</p>
                    <p style="margin:5px 0; font-size:15px; color:#AAA;">IMPORT TARIFFS:</p>
                    <p style="margin:0 0 15px 0; font-size:22px; font-weight:bold; color:#555;">₹{int(data['amazon']['import_charges']):,}</p>
                    <p style="margin:5px 0; font-size:14px; color:#888; font-weight:bold; text-transform:uppercase;">📦 ETA: {data['amazon']['eta']}</p>
                </div>""", unsafe_allow_html=True
            )
            
        with flpk_col:
            st.markdown(
                f"""<div style="background-color:#1E1E1E; padding:20px; border-radius:10px; border-top: 5px solid #2874F0; min-height:360px;">
                    <h3 style="margin:0 0 15px 0; color:#2874F0; text-align:center;">FLIPKART</h3>
                    <hr style="border:0.5px solid #333; margin:10px 0;">
                    <p style="margin:5px 0; font-size:15px; color:#AAA;">BASE ITEM PRICE:</p>
                    <p style="margin:0 0 15px 0; font-size:26px; font-weight:bold; color:#FFF;">₹{int(data['flipkart']['base_price']):,}</p>
                    <p style="margin:5px 0; font-size:15px; color:#AAA;">EST. DELIVERY CHARGE:</p>
                    <p style="margin:0 0 15px 0; font-size:22px; font-weight:bold; color:#FFF;">Extra: ₹{int(data['flipkart']['shipping_price']):,}</p>
                    <p style="margin:5px 0; font-size:15px; color:#AAA;">IMPORT TARIFFS:</p>
                    <p style="margin:0 0 15px 0; font-size:22px; font-weight:bold; color:#555;">₹{int(data['flipkart']['import_charges']):,}</p>
                    <p style="margin:5px 0; font-size:14px; color:#888; font-weight:bold; text-transform:uppercase;">📦 ETA: {data['flipkart']['eta']}</p>
                </div>""", unsafe_allow_html=True
            )
            
        with ali_col:
            st.markdown(
                f"""<div style="background-color:#1E1E1E; padding:20px; border-radius:10px; border-top: 5px solid #FF3860; min-height:360px;">
                    <h3 style="margin:0 0 15px 0; color:#FF3860; text-align:center;">ALIEXPRESS</h3>
                    <hr style="border:0.5px solid #333; margin:10px 0;">
                    <p style="margin:5px 0; font-size:15px; color:#AAA;">BASE ITEM PRICE:</p>
                    <p style="margin:0 0 15px 0; font-size:26px; font-weight:bold; color:#FFF;">₹{int(data['aliexpress']['base_price']):,}</p>
                    <p style="margin:5px 0; font-size:15px; color:#AAA;">EST. DELIVERY / FORWARDING:</p>
                    <p style="margin:0 0 15px 0; font-size:22px; font-weight:bold; color:#FFF;">Extra: ₹{int(data['aliexpress']['shipping_price']):,}</p>
                    <p style="margin:5px 0; font-size:15px; color:#AAA;">IMPORT TARIFFS (UPDATED):</p>
                    <p style="margin:0 0 15px 0; font-size:22px; font-weight:bold; color:#FF3860;">₹{int(data['aliexpress']['import_charges']):,}</p>
                    <p style="margin:5px 0; font-size:14px; color:#888; font-weight:bold; text-transform:uppercase;">📦 ETA: {data['aliexpress']['eta']}</p>
                </div>""", unsafe_allow_html=True
            )
            
        st.markdown("")
        
        # Delivery Hurdle Box Card for Search Mode
        st.markdown(
            f"""<div style="background-color:#1E1E1E; padding:20px; border-radius:10px; border: 1px solid #363636;">
                <p style="margin:0 0 10px 0; font-size:16px; color:#FF3860; text-transform:uppercase; font-weight:bold; letter-spacing:1px;">Delivery Risks & Forwarding Bottlenecks</p>
                <p style="margin:0; font-size:18px; color:#EEEEEE; line-height:1.5;">{data.get('transit_risks')}</p>
            </div>""", unsafe_allow_html=True
        )

    # 🌟 SINGLE PRODUCT URL MODE FRONTEND
    else:
        st.markdown("### 💰 Cost Breakdown Overview")
        price_box_1, price_box_2, price_box_3 = st.columns(3)
        with price_box_1:
            st.markdown(f"""<div style="background-color:#1E1E1E; padding:20px; border-radius:10px; border-left: 5px solid #00D1B2; text-align:center;"><p style="margin:0; font-size:16px; color:#AAAAAA; text-transform:uppercase; font-weight:bold;">Base Product Price</p><p style="margin:5px 0 0 0; font-size:32px; font-weight:bold; color:#FFFFFF;">₹{float(data.get('base_price', 0)):,.2f}</p></div>""", unsafe_allow_html=True)
        with price_box_2:
            st.markdown(f"""<div style="background-color:#1E1E1E; padding:20px; border-radius:10px; border-left: 5px solid #FFDD57; text-align:center;"><p style="margin:0; font-size:16px; color:#AAAAAA; text-transform:uppercase; font-weight:bold;">Shipping Price</p><p style="margin:5px 0 0 0; font-size:32px; font-weight:bold; color:#FFFFFF;">₹{float(data.get('shipping_price', 0)):,.2f}</p></div>""", unsafe_allow_html=True)
        with price_box_3:
            st.markdown(f"""<div style="background-color:#1E1E1E; padding:20px; border-radius:10px; border-left: 5px solid #FF3860; text-align:center;"><p style="margin:0; font-size:16px; color:#AAAAAA; text-transform:uppercase; font-weight:bold;">Import & Customs Charges</p><p style="margin:5px 0 0 0; font-size:32px; font-weight:bold; color:#FFFFFF;">₹{float(data.get('import_charges', 0)):,.2f}</p></div>""", unsafe_allow_html=True)

        st.markdown("") 

        st.markdown("### ⏱️ Delivery Timeline & Risk Assessment")
        logistics_box_1, logistics_box_2 = st.columns([1, 2])
        with logistics_box_1:
            st.markdown(f"""<div style="background-color:#1E1E1E; padding:25px; border-radius:10px; text-align:center; min-height:150px; border: 1px solid #363636;"><p style="margin:0; font-size:18px; color:#00D1B2; text-transform:uppercase; font-weight:bold; letter-spacing:1px;">ETA</p><p style="margin:15px 0 0 0; font-size:38px; font-weight:bold; color:#FFFFFF;">{data.get('eta')}</p></div>""", unsafe_allow_html=True)
        with logistics_box_2:
            st.markdown(f"""<div style="background-color:#1E1E1E; padding:20px; border-radius:10px; min-height:150px; border: 1px solid #363636;"><p style="margin:0; font-size:16px; color:#FF3860; text-transform:uppercase; font-weight:bold; letter-spacing:1px;">Possible Transit Risks</p><p style="margin:10px 0 0 0; font-size:18px; color:#EEEEEE; line-height:1.5;">{data.get('transit_risks')}</p></div>""", unsafe_allow_html=True)

    st.divider()

    # 🌟 CORE DATA ANCHORS (SHARED TEXT SECTIONS)
    st.markdown(f"### 📋 Why it is used\n<p style='font-size:18px;'>{data.get('why_used')}</p>", unsafe_allow_html=True)
    st.markdown(f"### 💡 Benefits of the product\n<p style='font-size:18px;'>{data.get('benefits')}</p>", unsafe_allow_html=True)
    
    is_worth = data.get('worth_buying', '').upper()
    box_color = "#257144" if "YES" in is_worth else "#712525"
    st.markdown(f"""<div style="background-color:{box_color}; padding:20px; border-radius:8px; margin:20px 0;"><h3 style="margin:0; color:#FFFFFF; font-size:22px;">Is this product worth buying?</h3><p style="margin:10px 0 0 0; font-size:20px; color:#FFFFFF; font-weight:bold;">{data.get('worth_buying')}</p></div>""", unsafe_allow_html=True)
    
    st.markdown(f"### ⚠️ Common complaints\n<p style='font-size:18px;'>{data.get('common_complaints')}</p>", unsafe_allow_html=True)
    st.markdown(f"### 🔄 Market Channel Pricing Comparison\n<p style='font-size:18px;'>{data.get('cheaper_alternative')}</p>", unsafe_allow_html=True)

    # --- CHAT ASSISTANT PANEL ---
    st.markdown("---")
    st.markdown("### 💬 Chat Assistant")
    for role, message in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(message)
            
    if user_chat_query := st.chat_input("Ask a question about these platform logistics variables..."):
        with st.chat_message("user"):
            st.markdown(user_chat_query)
        st.session_state.chat_history.append(("user", user_chat_query))
        
        with st.chat_message("assistant"):
            chat_context_prompt = f"Context payload block: {json.dumps(data)}. User question: {user_chat_query}"
            chat_response = client.models.generate_content(model='gemini-2.5-flash', contents=chat_context_prompt)
            st.markdown(chat_response.text)
        st.session_state.chat_history.append(("assistant", chat_response.text))