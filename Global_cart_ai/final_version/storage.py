import os
import json
import re

DB_FOLDER = "database"

def ensure_db():
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)

def save_json(data):
    ensure_db()
    prod_title = data.get('product_name', 'unknown_item')
    clean_title = re.sub(r'[^a-z0-9\s-]', '', prod_title.lower()).strip()
    filename = f"history_{clean_title.replace(' ', '_')}.json"
    filepath = os.path.join(DB_FOLDER, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    return filepath

def get_history_files():
    ensure_db()
    json_files = [f for f in os.listdir(DB_FOLDER) if f.startswith('history_') and f.endswith('.json')]
    options_map = {}
    for file in json_files:
        display_name = file.replace("history_", "").replace(".json", "").replace("_", " ").upper()
        options_map[display_name] = os.path.join(DB_FOLDER, file)
    return options_map

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None