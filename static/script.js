let map;
let userLat;
let userLon;
let marker;

window.onload = () => {
    loadFavorites();
    detectLocation();
};

function detectLocation() {
    if (!navigator.geolocation) {
        alert("Geolocation is not supported by your browser.");
        return;
    }

navigator.geolocation.getCurrentPosition(
        position => {
            userLat = position.coords.latitude;
            userLon = position.coords.longitude;

            initMap(userLat, userLon);
            fetchLocation(userLat, userLon);
            fetchWeather(userLat, userLon);
        },
        error => {
            alert("Unable to fetch your location.");
            console.log(error);
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
        }
    );
}

function initMap(lat, lon) {
    map = L.map('map').setView([lat, lon], 14);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap'
    }).addTo(map);

    marker = L.marker([lat, lon])
        .addTo(map)
        .bindPopup("You are here")
        .openPopup();
}

async function fetchLocation(lat, lon) {
    const res = await fetch('/detect_location', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ lat, lon })
    });

    const data = await res.json();

    let address = data.display_name || "Location not found";

    document.getElementById("locationText").innerHTML = address;
}

async function fetchWeather(lat, lon) {
    const res = await fetch('/weather', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ lat, lon })
    });

    const data = await res.json();

    if (data.current_weather) {
        let weather = `
            Temperature: ${data.current_weather.temperature}°C <br>
            Wind Speed: ${data.current_weather.windspeed} km/h
        `;

        document.getElementById("weatherText").innerHTML = weather;
    }
}

async function loadPlaces(type) {
    document.getElementById("placesContainer").innerHTML =
        "Loading nearby places...";

    const res = await fetch('/nearby_places', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            lat: userLat,
            lon: userLon,
            type: type
        })
    });

    const data = await res.json();

    let html = "";

    if (data.elements && data.elements.length > 0) {
        data.elements.slice(0, 20).forEach(place => {
            let name = place.tags?.name || "Unnamed Place";

            let lat = place.lat || place.center?.lat;
let lon = place.lon || place.center?.lon;

html += `
    <div class="place-item">
        <strong>${name}</strong><br>
        Category: ${type}<br><br>

        <button onclick="openPlace(${lat}, ${lon}, '${name}')">
            📍 View
        </button>

        <button onclick="getDirections(${lat}, ${lon})">
            🧭 Directions
        </button>

        <button onclick="saveFavorite('${name}')">
            ❤️ Save
        </button>
    </div>
`;
        });
    } else {
        html = "No places found nearby.";
    }

    document.getElementById("placesContainer").innerHTML = html;
}

async function saveFavorite(name) {
    await fetch('/favorites', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            place: name
        })
    });

    alert("Saved to favorites!");
    loadFavorites();
}

async function loadFavorites() {
    const box = document.getElementById("favoritesContainer");
    if (!box) return;

    const res = await fetch('/favorites');
    const data = await res.json();

    let html = "";

    if (data.length === 0) {
        html = "No favorites saved yet.";
    } else {
        data.forEach(item => {
            html += `
                <div class="place-item">
                    ❤️ ${item.place}
                </div>
            `;
        });
    }

    box.innerHTML = html;
}
function openPlace(lat, lon, name) {
    if (!lat || !lon) {
        alert("Location not available for this place");
        return;
    }

    map.flyTo([lat, lon], 18, {
        animate: true,
        duration: 2
    });

    L.marker([lat, lon])
        .addTo(map)
        .bindPopup(`<b>${name}</b>`)
        .openPopup();
}

function getDirections(lat, lon) {
    window.open(
        `https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route=${userLat}%2C${userLon}%3B${lat}%2C${lon}`,
        "_blank"
    );
}