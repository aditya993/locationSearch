from flask import Flask, request, jsonify
import requests
from geopy.distance import geodesic
import os

app = Flask(__name__)

# -----------------------------
# Convert city name to lat/lon
# -----------------------------
def get_coordinates(location):
    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": location,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "SmartShopFinderApp/1.0 (your-email@example.com)"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code != 200:
            return None, None

        data = response.json()

        if not data:
            return None, None

        return float(data[0]["lat"]), float(data[0]["lon"])

    except Exception as e:
        print("Geocoding error:", e)
        return None, None


# -----------------------------
# Search nearby shops
# -----------------------------
def search_shops(lat, lon):
    overpass_url = "https://overpass-api.de/api/interpreter"

    query = f"""
    [out:json];
    node
      ["shop"]
      (around:5000,{lat},{lon});
    out;
    """

    try:
        response = requests.post(overpass_url, data={"data": query}, timeout=20)

        if response.status_code != 200:
            return []

        data = response.json()
        return data.get("elements", [])

    except Exception as e:
        print("Overpass error:", e)
        return []


# -----------------------------
# Home Route
# -----------------------------
@app.route("/")
def home():
    return jsonify({
        "message": "Smart Local Shop Finder API is running!",
        "usage": "/search?product=laptop&location=Charlotte"
    })


# -----------------------------
# Search Route
# -----------------------------
@app.route("/search", methods=["GET"])
def search():
    product = request.args.get("product")
    location = request.args.get("location")

    if not product or not location:
        return jsonify({"error": "Please provide product and location"}), 400

    lat, lon = get_coordinates(location)

    if lat is None or lon is None:
        return jsonify({"error": "Could not fetch location. Try again."}), 400

    shops = search_shops(lat, lon)

    user_location = (lat, lon)
    results = []

    for shop in shops[:20]:
        shop_lat = shop.get("lat")
        shop_lon = shop.get("lon")

        if not shop_lat or not shop_lon:
            continue

        shop_location = (shop_lat, shop_lon)
        distance = geodesic(user_location, shop_location).miles

        results.append({
            "name": shop.get("tags", {}).get("name", "Unknown Shop"),
            "distance_miles": round(distance, 2),
            "directions": f"https://www.google.com/maps/dir/{lat},{lon}/{shop_lat},{shop_lon}"
        })

    # AI-style ranking (closest first)
    results = sorted(results, key=lambda x: x["distance_miles"])

    return jsonify({
        "product": product,
        "location": location,
        "results_found": len(results),
        "shops": results[:10]
    })


# -----------------------------
# Cloud Port Binding (Render)
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
