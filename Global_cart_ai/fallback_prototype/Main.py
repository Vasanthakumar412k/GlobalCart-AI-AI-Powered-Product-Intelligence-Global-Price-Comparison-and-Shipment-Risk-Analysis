import os
import json
import re
import pandas as pd
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

# --- HIGH-END SaaS THEME CUSTOMIZATION (ACCESSIBILITY & SCALE ENHANCEMENTS) ---
st.markdown("""
<style>
    /* Fix Wide Screen Stretch: Apply ~20% side margins */
    @media (min-width: 1200px) {
        .block-container {
            max-width: 65% !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            margin: 0 auto !important;
        }
    }

    /* Strict Light/Dark System Customization - Maximizing Readability */
    :root {
        --base-card-bg: #f8fafc;
        --base-card-border: #cbd5e1;
        --base-text-main: #0f172a;
        --base-text-muted: #475569;
        --info-block-bg: #f1f5f9;
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --base-card-bg: #111827;
            --base-card-border: #1e293b;
            --base-text-main: #f3f4f6;
            --base-text-muted: #9ca3af;
            --info-block-bg: #1e293b;
        }
    }

    /* Global Text & Input Adjustments */
    p, span, label, div {
        font-size: 16px !important;
    }
    
    /* Tabs Component Styling Overrides */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 2px solid var(--base-card-border); }
    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        background-color: var(--base-card-bg);
        border: 1px solid var(--base-card-border);
        border-radius: 6px 6px 0px 0px;
        color: var(--base-text-muted) !important;
        font-weight: 600;
        font-size: 16px !important;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #3b82f6 !important; 
        color: #ffffff !important;
        border-color: #3b82f6 !important;
        font-weight: 700;
        box-shadow: 0px 4px 14px rgba(59, 130, 246, 0.3);
    }
    div[data-baseweb="tab-highlight-bar"] { background-color: transparent !important; }

    /* Custom UI HTML Metric Component Cards */
    .dashboard-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; margin-bottom: 20px; }
    @media (max-width: 768px) {
        .dashboard-grid { grid-template-columns: 1fr; }
    }
    .ui-card {
        background: var(--base-card-bg);
        border: 2px solid var(--base-card-border);
        border-radius: 12px;
        padding: 22px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    .ui-card:hover { border-color: #3b82f6; transform: translateY(-2px); }
    
    .card-title { font-size: 14px !important; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #3b82f6; margin: 0 0 6px 0; }
    .card-model { font-size: 16px !important; font-weight: 700; color: var(--base-text-main); margin: 4px 0; min-height: 44px; }
    .card-value { font-size: 32px !important; font-weight: 800; color: var(--base-text-main); margin: 8px 0; }
    .card-sub { font-size: 15px !important; font-weight: 600; margin: 2px 0; color: var(--base-text-muted); }
    
    /* Brand Platform Card Accents */
    .brand-amz { border-top: 6px solid #ff9900; }
    .brand-flpk { border-top: 6px solid #2874f0; }
    .brand-ali { border-top: 6px solid #ff3860; }
    
    /* Informational & Text Blocks UI */
    .info-block { background: var(--info-block-bg); border: 2px solid var(--base-card-border); padding: 20px; border-radius: 8px; margin-bottom: 18px; }
    .info-label { font-size: 15px !important; font-weight: 800; color: #3b82f6; text-transform: uppercase; margin-bottom: 8px; }
    .info-desc { font-size: 16px !important; line-height: 1.7; color: var(--base-text-main); margin: 0; }

    /* Forms and Buttons Controls Upgrades */
    div[data-baseweb="input"] {
        border-radius: 8px !important;
        border: 2px solid var(--base-card-border) !important;
    }
    .stButton>button {
        border-radius: 8px !important;
        padding: 12px 28px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        background-color: #3b82f6 !important;
        color: white !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        background-color: #2563eb !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* Styled Link Action Button acting as Target Anchor */
    .tab-link-btn {
        display: inline-block;
        width: 100%;
        text-align: center;
        background-color: #10b981 !important;
        color: white !important;
        font-weight: 700;
        font-size: 16px !important;
        padding: 14px 28px;
        border-radius: 8px;
        text-decoration: none;
        transition: all 0.2s ease;
    }
    .tab-link-btn:hover {
        background-color: #059669 !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Gemini Client
if "GEMINI_API_KEY" in os.environ:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY2"))
else:
    st.warning("⚠️ Gemini API Key not found. Please ensure GEMINI_API_KEY is configured in your system environment.")
    client = None

# --- SHARED RENDER ENGINE FOR STYLED DATA ---
def render_styled_dashboard(data):
    st.markdown(f"## 📊 Sourcing Analysis Dashboard: {data.get('product_name', 'UNKNOWN').upper()}")
    
    if data.get("is_search_mode") == True:
        st.markdown(f"""
        <div class="dashboard-grid">
            <div class="ui-card brand-amz">
                <p class="card-title">Amazon India</p>
                <p class="card-model">📋 {data['amazon'].get('model_name', 'Target Model Variant')}</p>
                <p class="card-value">₹{int(data['amazon']['base_price']):,}</p>
                <p class="card-sub">+₹{int(data['amazon']['shipping_price']):,} Delivery</p>
                <p class="card-sub">₹{int(data['amazon']['import_charges']):,} Import Tariff</p>
                <p class="card-sub" style="color: #3b82f6; margin-top: 10px; font-weight: bold;">📦 ETA: {data['amazon']['eta']}</p>
            </div>
            <div class="ui-card brand-flpk">
                <p class="card-title">Flipkart</p>
                <p class="card-model">📋 {data['flipkart'].get('model_name', 'Equivalent Variant')}</p>
                <p class="card-value">₹{int(data['flipkart']['base_price']):,}</p>
                <p class="card-sub">+₹{int(data['flipkart']['shipping_price']):,} Delivery</p>
                <p class="card-sub">₹{int(data['flipkart']['import_charges']):,} Import Tariff</p>
                <p class="card-sub" style="color: #3b82f6; margin-top: 10px; font-weight: bold;">📦 ETA: {data['flipkart']['eta']}</p>
            </div>
            <div class="ui-card brand-ali">
                <p class="card-title">AliExpress Cross-Border</p>
                <p class="card-model">📋 {data['aliexpress'].get('model_name', 'Global Structural Match')}</p>
                <p class="card-value">₹{int(data['aliexpress']['base_price']):,}</p>
                <p class="card-sub">+₹{int(data['aliexpress']['shipping_price']):,} Freight Forwarder</p>
                <p class="card-sub" style="color: #ef4444; font-weight: bold;">+₹{int(data['aliexpress']['import_charges']):,} Customs & IGST</p>
                <p class="card-sub" style="color: #3b82f6; margin-top: 10px; font-weight: bold;">📦 ETA: {data['aliexpress']['eta']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📈 Sourcing Matrix Cost Breakdown Comparison")
        chart_dict = {
            "Platform": ["Amazon India", "Flipkart", "AliExpress"],
            "Base Item Cost": [int(data['amazon']['base_price']), int(data['flipkart']['base_price']), int(data['aliexpress']['base_price'])],
            "Shipping/Freight": [int(data['amazon']['shipping_price']), int(data['flipkart']['shipping_price']), int(data['aliexpress']['shipping_price'])],
            "Import Tariffs": [int(data['amazon']['import_charges']), int(data['flipkart']['import_charges']), int(data['aliexpress']['import_charges'])]
        }
        df = pd.DataFrame(chart_dict).set_index("Platform")
        st.bar_chart(df, stack=True, width="stretch", color=["#3b82f6", "#f59e0b", "#ef4444"])

    else:
        try: base_p = float(data.get('base_price', 0))
        except: base_p = 0.0
        try: ship_p = float(data.get('shipping_price', 0))
        except: ship_p = 0.0
        try: imp_p = float(data.get('import_charges', 0))
        except: imp_p = 0.0
        
        st.markdown(f"""
        <div class="dashboard-grid">
            <div class="ui-card" style="border-left: 6px solid #10b981;">
                <p class="card-title">Base Sourced Price</p>
                <p class="card-value">₹{base_p:,.2f}</p>
            </div>
            <div class="ui-card" style="border-left: 6px solid #f59e0b;">
                <p class="card-title">Logistics & Shipping</p>
                <p class="card-value">₹{ship_p:,.2f}</p>
            </div>
            <div class="ui-card" style="border-left: 6px solid #ef4444;">
                <p class="card-title">Customs Tariffs Surcharges</p>
                <p class="card-value">₹{imp_p:,.2f}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📈 Landed Cost Stack Component Proportions")
        chart_dict = {
            "Cost Segment": ["Base Product Cost", "Logistics Shipping", "Import Duties"],
            "Amount (INR)": [base_p, ship_p, imp_p]
        }
        df = pd.DataFrame(chart_dict).set_index("Cost Segment")
        st.bar_chart(df, width="stretch", color="#3b82f6")

    st.markdown(f"""
    <div class="info-block">
        <p class="info-label">📋 Sourcing Objective & Category Context</p>
        <p class="info-desc">{data.get('why_used')}</p>
    </div>
    <div class="info-block">
        <p class="info-label">💡 Functional Value Specifications</p>
        <p class="info-desc">{data.get('benefits')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    is_worth = data.get('worth_buying', '').upper()
    box_color = "#064e3b" if "YES" in is_worth else "#7f1d1d"
    text_accent = "#34d399" if "YES" in is_worth else "#f87171"
    st.markdown(f"""
    <div style="background-color: {box_color}; border: 1px solid {text_accent}; padding: 24px; border-radius: 8px; margin: 20px 0;">
        <h4 style="margin: 0 0 8px 0; color: #ffffff; text-transform: uppercase; font-size: 14px; letter-spacing:0.05em; font-weight:bold;">Landed Cost Value Verdict</h4>
        <p style="margin: 0; font-size: 18px !important; color: #ffffff; font-weight: 700;">{data.get('worth_buying')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="info-block">
        <p class="info-label">⚠️ Common Supply Defects & Risks</p>
        <p class="info-desc">{data.get('common_complaints')}</p>
    </div>
    <div class="info-block">
        <p class="info-label">🔄 Channel Alternative Routing Analysis</p>
        <p class="info-desc">{data.get('cheaper_alternative')}</p>
    </div>
    <div class="info-block">
        <p class="info-label">🚨 Border Clearance Constraints & Transit Risks</p>
        <p class="info-desc">{data.get('transit_risks')}</p>
    </div>
    """, unsafe_allow_html=True)

# --- SCRAPER ENGINE ---
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

# --- INITIALIZE SESSION STATES ---
if "parsed_json" not in st.session_state:
    st.session_state.parsed_json = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_website" not in st.session_state:
    st.session_state.current_website = ""

# ==========================================
# DEEP ROUTING GATEKEEPER LAYER (NEW TAB ENGINE)
# ==========================================
query_params = st.query_params
if "view_history" in query_params:
    target_filename = query_params["view_history"]
    if os.path.exists(target_filename):
        try:
            with open(target_filename, "r", encoding="utf-8") as f:
                loaded_payload = json.load(f)
            
            st.markdown(f"### 📑 Historical Isolation Record View")
            st.caption(f"📍 Sourced directly from tracking point data node: `{target_filename}`")
            render_styled_dashboard(loaded_payload)
            
            with st.expander("🛠️ View Raw Data Blueprint"):
                st.json(loaded_payload)
            st.stop() 
        except Exception as e:
            st.error(f"Failed to compile target data isolate channel: {e}")
    else:
        st.error("The requested archival log coordinates do not exist inside runtime workspace context.")
        st.stop()

# --- MAIN WORKSPACE UI HEADER ---
st.title("📦 Global Logistics & Import Intelligence Engine")

tab1, tab2, tab3 = st.tabs(["🔍 Product Name Search", "🔗 Analyze URL Link", "📊 Saved Insights History"])

# --- TAB 1: PRODUCT SEARCH ROUTE (WITH GOOGLE SEARCH MODEL MATCHING) ---
with tab1:
    search_input = st.text_input("Type a generic product name (e.g., 'mechanical keyboard'):", key="search_mode_input", placeholder="mechanical keyboard")
    if st.button("🚀 Process Sourcing Comparison", width="stretch", key="search_submit"):
        if not client:
            st.error("Please configure your Gemini API Key first.")
        elif search_input:
            st.session_state.parsed_json = None
            st.session_state.current_website = "search_mode"
            with st.spinner(f"🔍 Crawling real-time Indian retail listings for '{search_input}'..."):
                
                search_prompt = f"""
                The user wants a localized e-commerce pricing analysis for this generic product type: "{search_input}".
                
                EXECUTION FLOW:
                1. Browse current active retail models selling right now in India matching "{search_input}".
                2. Identify a specific, popular retail model and its actual pricing structure on Amazon India.
                3. Search Flipkart for that exact same model. If missing, locate a closely equivalent matched product option.
                4. Match it to its corresponding cross-border listing variant available on global markets (like AliExpress).
                
                CRITICAL DIRECTIVE: Do NOT output hardcoded numbers or templates. Find and use real model variations and authentic calculated market values.
                
                Respond ONLY with a raw JSON object matching this exact structure (no markdown code blocks, values must be string integers):
                {{
                  "is_search_mode": true,
                  "product_name": "Primary specific matched model title found (e.g., Keychron K2 V2 Mechanical Keyboard)",
                  "why_used": "Explain the exact primary utility of this product class",
                  "benefits": "List 3 core hardware advantages or structural features of the identified model",
                  "worth_buying": "YES or NO - complete with direct trend/value reasoning justification",
                  "common_complaints": "List authentic consumer hardware complaints or failure risks for this item class",
                  
                  "amazon": {{
                    "model_name": "Exact specific product title or variation found on Amazon India",
                    "base_price": "Authentic current retail selling cost in INR as a string integer",
                    "shipping_price": "Delivery fee (e.g. 0 or 40)",
                    "import_charges": "0",
                    "eta": "2-4 Days"
                  }},
                  "flipkart": {{
                    "model_name": "Exact identical model title or the alternative matched equivalent model found on Flipkart",
                    "base_price": "Authentic selling cost in INR as a string integer",
                    "shipping_price": "Delivery fee (e.g. 0 or 60)",
                    "import_charges": "0",
                    "eta": "2-5 Days"
                  }},
                  "aliexpress": {{
                    "model_name": "Global equivalent model variation title found on cross-border channels",
                    "base_price": "International base cost before customs/tariffs as a string integer",
                    "shipping_price": "Estimated global freight/forwarder routing cost to India",
                    "import_charges": "Calculated baseline Indian customs import duty markup (approx 42-77% of base cost)",
                    "eta": "15-30 Days"
                  }},
                  
                  "cheaper_alternative": "Granular value analysis contrasting the Amazon vs Flipkart options against the timeline/customs risk of the global cross-border option",
                  "transit_risks": "Compare logistics tracking visibility, domestic transit security, and warranty coverage vs cross-border customs entry blockages"
                }}
                """
                
                try:
                    # Leverage dynamic tool search grounding to fetch live pricing structures
                    response = client.models.generate_content(
                        model='gemini-2.5-flash', 
                        contents=search_prompt,
                        config={"tools": [{"google_search": {}}]}
                    )
                    
                    clean_json_str = response.text.strip().replace("```json", "").replace("```", "")
                    st.session_state.parsed_json = json.loads(clean_json_str)
                    st.session_state.chat_history = []
                except Exception as json_err:
                    st.error(f"Failed to generate structured data matrix: {json_err}")

# --- TAB 2: URL SCRAPE ROUTE ---
with tab2:
    url_input = st.text_input("Paste an item link:", key="url_mode_input", placeholder="https://in.iherb.com/pr/...")
    if st.button("🚀 Process Link Scrape", width="stretch", key="url_submit"):
        if not client:
            st.error("Please configure your Gemini API Key first.")
        elif url_input:
            st.session_state.parsed_json = None
            st.session_state.current_website = ""
            target_url = url_input if url_input.strip().startswith(("http://", "https://")) else f"https://{url_input.strip()}"
            
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
                    try:
                        clean_json_str = response.text.strip().replace("```json", "").replace("```", "")
                        st.session_state.parsed_json = json.loads(clean_json_str)
                        st.session_state.chat_history = []
                    except Exception as json_err:
                        st.error("Failed to parse metrics framework.")
            else:
                st.error(f"Scraper error: {scraped_data.get('error', 'Could not locate elements.')}")

# --- TAB 3: DATA RETENTION & DYNAMIC STYLED ARCHIVE ---
with tab3:
    st.header("Stored Analytics Profiles")
    
    # Read the local workspace folder dynamically
    json_files = [f for f in os.listdir('.') if f.startswith('history_') and f.endswith('.json')]
    
    if not json_files:
        st.info("No saved snapshot files found next to app.py yet.")
    else:
        options_map = {}
        for file in json_files:
            display_name = file.replace("history_", "").replace(".json", "").replace("_", " ").upper()
            options_map[display_name] = file
            
        selected_profile = st.selectbox("Select a historical footprint layer:", options=list(options_map.keys()))
        target_file = options_map[selected_profile]
        
        # Deep Link Parameter String Setup
        new_tab_url = f"/?view_history={target_file}"
        
        st.markdown(f"""
            <a href="{new_tab_url}" target="_blank" class="tab-link-btn">
                📖 Open '{selected_profile}' in a New Browser Tab
            </a>
        """, unsafe_allow_html=True)
        
        with st.expander("🔍 Quick Local JSON Preview"):
            try:
                with open(target_file, "r", encoding="utf-8") as f:
                    st.json(json.load(f))
            except:
                st.error("Failed to read targeted disk segment data preview.")

# ==========================================
# STAGE 4: RUNTIME PRESENTATION LAYER
# ==========================================
if st.session_state.parsed_json:
    render_styled_dashboard(st.session_state.parsed_json)

    # --- ACTION MANAGEMENT ENGINE ---
    if st.button("💾 Save Current Results to History File", width="stretch", key="save_results_data"):
        prod_title = st.session_state.parsed_json.get('product_name', 'unknown_item')
        clean_title = re.sub(r'[^a-z0-9\s-]', '', prod_title.lower()).strip()
        safe_filename = f"history_{clean_title.replace(' ', '_')}.json"
        
        try:
            with open(safe_filename, "w", encoding="utf-8") as f:
                json.dump(st.session_state.parsed_json, f, indent=4, ensure_ascii=False)
            st.success(f"✓ Snapshot data committed safely next to app.py as `{safe_filename}`!")
            st.rerun()
        except Exception as e:
            st.error(f"File system operational breakdown: {e}")

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
            chat_context_prompt = f"Context payload block: {json.dumps(st.session_state.parsed_json)}. User question: {user_chat_query}"
            chat_response = client.models.generate_content(model='gemini-2.5-flash', contents=chat_context_prompt)
            st.markdown(chat_response.text)
        st.session_state.chat_history.append(("assistant", chat_response.text))