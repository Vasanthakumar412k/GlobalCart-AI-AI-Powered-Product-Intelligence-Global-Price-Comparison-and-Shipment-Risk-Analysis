import requests

def get_live_usd_to_inr_rate() -> float:
    """
    Fetches the live USD to INR conversion rate from ExchangeRate-API.
    Returns a robust baseline fallback of 83.50 if the API call encounters latency or errors.
    """
    url = "https://open.er-api.com/v6/latest/USD"
    try:
        response = requests.get(url, timeout=8)
        if response.status_code == 200:
            data = response.json()
            rate = data.get("rates", {}).get("INR")
            if rate:
                return float(rate)
        return 83.50  # Operational baseline fallback
    except Exception:
        return 83.50  # Fallback protection asset

def convert_usd_to_inr(usd_amount: float) -> float:
    """Convenience helper to multiply an incoming USD value by the live rate factor."""
    current_rate = get_live_usd_to_inr_rate()
    return round(usd_amount * current_rate, 2)

# --- RUNTIME VERIFICATION VERDICT ---
if __name__ == "__main__":
    print("--- Executing Isolated Currency Conversion Testing ---")
    live_factor = get_live_usd_to_inr_rate()
    print(f"Current Conversion Factor (1 USD to INR): {live_factor}")
    print(f"Sample Conversion ($150 USD into INR): ₹{convert_usd_to_inr(150.00)}")