import requests
import json
import time

def simulate_vortex_entry(price_a, price_b):
    url = "http://localhost:1740/decide"
    payload = {
        "asset_a": "BTC",
        "asset_b": "USDT",
        "price_a": price_a,
        "price_b": price_b,
        "timestamp": int(time.time())
    }
    
    print(f"--- SYMULACJA: PriceA={price_a}, PriceB={price_b} ---")
    try:
        # Uwaga: Zakładamy, że serwer jest uruchomiony na localhost dla testu lokalnego
        # W produkcji n8n uderza w adrion-vortex:1740
        response = requests.post(url, json=payload, timeout=2)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Błąd połączenia (czy serwer Go działa na porcie 1740?): {e}")

if __name__ == "__main__":
    # Test 1: Brak rezonansu
    simulate_vortex_entry(100.0, 100.0)
    
    # Test 2: Potencjał (Digital Root 3 lub 6)
    # Różnica 0.000003 -> 3 (Root 3)
    simulate_vortex_entry(100.000003, 100.0)
    
    # Test 3: SINGULARITY (Digital Root 9)
    # Różnica 0.000009 -> 9 (Root 9)
    simulate_vortex_entry(100.000009, 100.0)
