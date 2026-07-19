import pandas as pd
import streamlit as st
from urllib.parse import urlparse

# Import modules
import ai_engine
import storage
from scrapers import iherb, shein, aliexpress

# --- STREAMLIT PAGE CONFIG ---
st.set_page_config(page_title="Global Logistics & E-Commerce AI Engine", page_icon="📦", layout="wide")

# --- LOAD CSS ---
try:
    with open("styles/main_theme.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    st.warning("⚠️ styles/main_theme.css not found. Falling back to default Streamlit theme.")

# --- INITIALIZE GEMINI ---
client = ai_engine.get_client()
if not client:
    st.warning("⚠️ Gemini API Key not found. Please ensure GEMINI_API_KEY is configured in your system environment.")

# --- SHARED RENDER ENGINE ---
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
    target_filepath = query_params["view_history"]
    loaded_payload = storage.load_json(target_filepath)
    
    if loaded_payload:
        st.markdown(f"### 📑 Historical Isolation Record View")
        st.caption(f"📍 Sourced directly from tracking point data node: `{target_filepath}`")
        render_styled_dashboard(loaded_payload)
        
        with st.expander("🛠️ View Raw Data Blueprint"):
            st.json(loaded_payload)
        st.stop()
    else:
        st.error("The requested archival log coordinates do not exist inside runtime workspace context.")
        st.stop()


# --- MAIN WORKSPACE UI HEADER ---
st.title("📦 Global Logistics & Import Intelligence Engine")

tab1, tab2, tab3 = st.tabs(["🔍 Product Name Search", "🔗 Analyze URL Link", "📊 Saved Insights History"])

# --- TAB 1: PRODUCT SEARCH ROUTE ---
with tab1:
    search_input = st.text_input("Type a generic product name (e.g., 'mechanical keyboard'):", key="search_mode_input", placeholder="mechanical keyboard")
    if st.button("🚀 Process Sourcing Comparison", width="stretch", key="search_submit"):
        if not client:
            st.error("Please configure your Gemini API Key first.")
        elif search_input:
            st.session_state.parsed_json = None
            st.session_state.current_website = "search_mode"
            with st.spinner(f"🔍 Crawling real-time Indian retail listings for '{search_input}'..."):
                try:
                    st.session_state.parsed_json = ai_engine.fetch_product_comparison(client, search_input)
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
            
            with st.spinner("🌐 URL detected. Routing to correct scraper..."):
                domain = urlparse(target_url).netloc
                scraped_data = {}
                
                if "iherb" in domain:
                    scraped_data = iherb.scrape(target_url)
                elif "shein" in domain:
                    scraped_data = shein.scrape(target_url)
                elif "aliexpress" in domain:
                    scraped_data = aliexpress.scrape(target_url)
                else:
                    st.error("Website domain not currently supported by modules.")
                
            if scraped_data and "error" not in scraped_data and scraped_data.get("product_name"):
                st.session_state.current_website = scraped_data["website"]
                
                with st.spinner("🤖 Scrape complete! Processing with Gemini..."):
                    try:
                        st.session_state.parsed_json = ai_engine.process_scraped_data(client, scraped_data)
                        st.session_state.chat_history = []
                    except Exception as json_err:
                        st.error("Failed to parse metrics framework.")
            elif not scraped_data:
                pass # Error handled above
            else:
                st.error(f"Scraper error: Could not locate elements.")


# --- TAB 3: DATA RETENTION ---
with tab3:
    st.header("Stored Analytics Profiles")
    
    options_map = storage.get_history_files()
    
    if not options_map:
        st.info("No saved snapshot files found in the 'database' folder yet.")
    else:
        selected_profile = st.selectbox("Select a historical footprint layer:", options=list(options_map.keys()))
        target_file = options_map[selected_profile]
        
        new_tab_url = f"/?view_history={target_file}"
        
        st.markdown(f"""
            <a href="{new_tab_url}" target="_blank" class="tab-link-btn">
                📖 Open '{selected_profile}' in a New Browser Tab
            </a>
        """, unsafe_allow_html=True)
        
        with st.expander("🔍 Quick Local JSON Preview"):
            loaded_data = storage.load_json(target_file)
            if loaded_data:
                st.json(loaded_data)
            else:
                st.error("Failed to read targeted disk segment data preview.")


# ==========================================
# STAGE 4: RUNTIME PRESENTATION LAYER
# ==========================================
if st.session_state.parsed_json:
    render_styled_dashboard(st.session_state.parsed_json)

    # --- ACTION MANAGEMENT ENGINE ---
    if st.button("💾 Save Current Results to History Database", width="stretch", key="save_results_data"):
        try:
            saved_path = storage.save_json(st.session_state.parsed_json)
            st.success(f"✓ Snapshot data committed safely to `{saved_path}`!")
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
            reply = ai_engine.chat_with_assistant(client, st.session_state.parsed_json, user_chat_query)
            st.markdown(reply)
        st.session_state.chat_history.append(("assistant", reply))