import streamlit as st
from web_scrapper import scrape
st.title("Import Product Analyzer")
st.write("Paste a product URL to analyze")
url = st.text_input("Product URL")
if st.button("Analyze"):
    if url:
        with st.spinner("Scraping product data..."):
            data = scrape(url)
        st.success("Product data fetched!")
        st.json(data)
    else:
        st.warning("Please paste a product URL")