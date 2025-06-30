from flask import Flask, jsonify
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

FEED_URL = "https://hourlypricing.comed.com/api?type=5minutefeed"
AVG_URL = "https://hourlypricing.comed.com/api?type=currenthouraverage"

def get_formatted_time(dt):
    return dt.strftime("%Y%m%d%H%M")

def fetch_5min_prices():
    now = datetime.utcnow()
    end = get_formatted_time(now)
    start_time = now - timedelta(minutes=5)
    start = get_formatted_time(start_time)

    url = f"{FEED_URL}&datestart={start}&dateend={end}"
    response = requests.get(url)
    prices = response.json()

    if len(prices) < 1:
        raise ValueError("No 5-minute price data found")

    prices_sorted = sorted(prices, key=lambda p: p["millisUTC"])
    current_price = float(prices_sorted[-1]["price"])
    next_price = float(prices_sorted[-2]["price"]) if len(prices_sorted) > 1 else current_price
    timestamp = datetime.utcfromtimestamp(prices_sorted[-1]["millisUTC"] / 1000).strftime("%I:%M %p")

    return current_price, next_price, timestamp

def fetch_hour_average():
    response = requests.get(AVG_URL)
    data = response.json()
    if not data:
        return None
    return float(data[-1]["price"])

def status(p):
    if p <= 4.0:
        return "✅ GOOD"
    elif p <= 8.0:
        return "⚠️ MEH"
    else:
        return "❌ BAD"

@app.route("/data")
def comed_status():
    try:
        current_price, next_price, timestamp = fetch_5min_prices()
        hour_avg = fetch_hour_average()

        return jsonify({
            "current_price": current_price,
            "current_status": status(current_price),
            "next_price": next_price,
            "next_status": status(next_price),
            "hour_avg": hour_avg,
            "timestamp": timestamp
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)