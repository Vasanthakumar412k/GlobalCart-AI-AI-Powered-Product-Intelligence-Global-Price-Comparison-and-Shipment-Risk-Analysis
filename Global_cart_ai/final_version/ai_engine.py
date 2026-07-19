import os
import json
from google import genai

def get_client():
    api_key = os.environ.get("GEMINI_API_KEY2") or os.environ.get("GEMINI_API_KEY")
    if api_key:
        return genai.Client(api_key=api_key)
    return None

def fetch_product_comparison(client, search_input):
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
    response = client.models.generate_content(
        model='gemini-2.5-flash', 
        contents=search_prompt,
        config={"tools": [{"google_search": {}}]}
    )
    clean_json_str = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(clean_json_str)

def process_scraped_data(client, scraped_data):
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
    clean_json_str = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(clean_json_str)

def chat_with_assistant(client, context_json, user_query):
    chat_context_prompt = f"Context payload block: {json.dumps(context_json)}. User question: {user_query}"
    response = client.models.generate_content(model='gemini-2.5-flash', contents=chat_context_prompt)
    return response.text