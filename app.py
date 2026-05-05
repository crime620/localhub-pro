from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import requests
import json
import os

app = Flask(__name__)
app.secret_key = "localhub_secret"

# Admin credentials
ADMIN_EMAIL = "admin@localhub.com"
ADMIN_PASSWORD = "admin123"

# JSON files
USERS_FILE = "users.json"
FAVORITES_FILE = "favorites.json"
REVIEWS_FILE = "reviews.json"
ANNOUNCEMENTS_FILE = "announcements.json"


def load_json(file, default=[]):
    if os.path.exists(file):
        with open(file, "r") as f:
            try:
                return json.load(f)
            except:
                return default
    return default


def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Admin login
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session["admin"] = True
            session["user"] = "Administrator"
            return redirect(url_for("admin"))

        users = load_json(USERS_FILE)

        for user in users:
            if user["email"] == email and user["password"] == password:
                session["user"] = user["name"]
                session["email"] = user["email"]
                return redirect(url_for("dashboard"))

        flash("Invalid credentials")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        users = load_json(USERS_FILE)

        for user in users:
            if user["email"] == email:
                flash("Email already registered")
                return redirect(url_for("register"))

        users.append({
            "name": name,
            "email": email,
            "password": password
        })

        save_json(USERS_FILE, users)
        flash("Registration successful")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", user=session["user"])


@app.route("/detect_location", methods=["POST"])
def detect_location():
    data = request.json
    lat = data["lat"]
    lon = data["lon"]

    url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"

    res = requests.get(url, headers={"User-Agent": "LocalHub"})
    return jsonify(res.json())


@app.route("/nearby_places", methods=["POST"])
def nearby_places():
    try:
        data = request.json
        lat = data["lat"]
        lon = data["lon"]
        place_type = data["type"]

        # Hotels use tourism=hotel
        if place_type == "hotel":
            query = f"""
            [out:json][timeout:25];
            (
              node["tourism"="hotel"](around:5000,{lat},{lon});
              way["tourism"="hotel"](around:5000,{lat},{lon});
              relation["tourism"="hotel"](around:5000,{lat},{lon});
            );
            out center;
            """
        else:
            # Restaurants / hospitals / banks use amenity
            query = f"""
            [out:json][timeout:25];
            (
              node["amenity"="{place_type}"](around:5000,{lat},{lon});
              way["amenity"="{place_type}"](around:5000,{lat},{lon});
              relation["amenity"="{place_type}"](around:5000,{lat},{lon});
            );
            out center;
            """

        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=query,
            headers={"User-Agent": "LocalHub"},
            timeout=30
        )

        return jsonify(response.json())

    except Exception as e:
        return jsonify({
            "error": str(e),
            "elements": []
        })

@app.route("/weather", methods=["POST"])
def weather():
    data = request.json
    lat = data["lat"]
    lon = data["lon"]

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&current_weather=true"
    )

    res = requests.get(url)
    return jsonify(res.json())


@app.route("/search_place", methods=["POST"])
def search_place():
    data = request.json
    query = data["query"]

    res = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": query,
            "format": "json",
            "limit": 1
        },
        headers={"User-Agent": "LocalHub"}
    )

    return jsonify(res.json())


@app.route("/favorites", methods=["GET", "POST"])
def favorites():
    favs = load_json(FAVORITES_FILE)

    if request.method == "POST":
        item = request.json
        favs.append(item)
        save_json(FAVORITES_FILE, favs)
        return jsonify({"message": "Saved"})

    return jsonify(favs)


@app.route("/delete_favorite", methods=["POST"])
def delete_favorite():
    data = request.json
    place_name = data["place"]

    favs = load_json(FAVORITES_FILE)
    favs = [x for x in favs if x["place"] != place_name]

    save_json(FAVORITES_FILE, favs)

    return jsonify({"message": "Deleted"})


@app.route("/review", methods=["GET", "POST"])
def review():
    reviews = load_json(REVIEWS_FILE)

    if request.method == "POST":
        data = request.json

        reviews.append({
            "user": session.get("user", "Guest"),
            "message": data["message"],
            "rating": data["rating"]
        })

        save_json(REVIEWS_FILE, reviews)
        return jsonify({"message": "Review added"})

    return jsonify(reviews)


@app.route("/announcement", methods=["GET", "POST"])
def announcement():
    announcements = load_json(ANNOUNCEMENTS_FILE)

    if request.method == "POST":
        data = request.json
        announcements.append(data["text"])
        save_json(ANNOUNCEMENTS_FILE, announcements)
        return jsonify({"message": "Posted"})

    return jsonify(announcements)


@app.route("/admin")
def admin():
    if "admin" not in session:
        return redirect(url_for("login"))

    users = load_json(USERS_FILE)
    reviews = load_json(REVIEWS_FILE)
    announcements = load_json(ANNOUNCEMENTS_FILE)
    favorites = load_json(FAVORITES_FILE)

    analytics = {
        "users": len(users),
        "reviews": len(reviews),
        "announcements": len(announcements),
        "favorites": len(favorites)
    }

    return render_template(
        "admin.html",
        users=users,
        reviews=reviews,
        announcements=announcements,
        analytics=analytics
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
   app.run(host="0.0.0.0", port=5000, debug=True)

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)