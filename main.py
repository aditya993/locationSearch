from flask import Flask, request, jsonify
import requests
from geopy.distance import geodesic

app = Flask(__name__)


# Convert city name to lat/long
def get_coordinates(location):
    url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json"
    response = requests.get(url).json()
    if response:
        return float(response[0]['lat']), float(response[0]['lon'])
    return None, None


# Search nearby shops
def search_shops(product, lat, lon):
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    node
      ["shop"]
      (around:5000,{lat},{lon});
    out;
    """
    response = requests.post(overpass_url, data={'data': query}).json()
    return response.get("elements", [])


@app.route('/search', methods=['GET'])
def search():
    product = request.args.get("product")
    location = request.args.get("location")

    lat, lon = get_coordinates(location)
    if not lat:
        return jsonify({"error": "Location not found"})

    shops = search_shops(product, lat, lon)

    results = []
    user_location = (lat, lon)

    for shop in shops[:10]:
        shop_location = (shop["lat"], shop["lon"])
        distance = geodesic(user_location, shop_location).miles

        results.append({
            "name": shop.get("tags", {}).get("name", "Unknown Shop"),
            "distance_miles": round(distance, 2),
            "directions": f"https://www.google.com/maps/dir/{lat},{lon}/{shop['lat']},{shop['lon']}"
        })

    # Simple AI sorting by distance
    results = sorted(results, key=lambda x: x["distance_miles"])

    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True)
