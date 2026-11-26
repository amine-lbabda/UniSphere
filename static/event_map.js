const mapElement = document.getElementById("event-map");
const latitudeInput = document.getElementById("id_latitude");
const longitudeInput = document.getElementById("id_longitude");

if (mapElement && latitudeInput && longitudeInput) {
const savedLatitude = Number(latitudeInput.value);
const savedLongitude = Number(longitudeInput.value);
const hasSavedLocation =
    Number.isFinite(savedLatitude) &&
    Number.isFinite(savedLongitude) &&
    (savedLatitude !== 0 || savedLongitude !== 0);

const map = L.map(mapElement).setView(
    hasSavedLocation ? [savedLatitude, savedLongitude] : [48.8566, 2.3522],
    hasSavedLocation ? 16 : 13
);

L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    {
        maxZoom: 19,
        attribution: "Tiles &copy; Esri and its data sources",
    }
).addTo(map);
const streets = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    { maxZoom: 19, attribution: "Tiles &copy; Esri and its data sources" }
);

const satellite = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    {
        maxZoom: 19,
        attribution:
            "Tiles &copy; Esri, Maxar, Earthstar Geographics, and the GIS User Community",
    }
);

const topographic = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
    { maxZoom: 19, attribution: "Tiles &copy; Esri and its data sources" }
);

L.control.layers({
    Streets: streets,
    Satellite: satellite,
    Topographic: topographic,
}).addTo(map);
let marker;
function setLocation(lat, lng) {
    const point = L.latLng(lat, lng);

    latitudeInput.value = lat.toFixed(6);
    longitudeInput.value = lng.toFixed(6);

    map.setView(point, 16);

    if (marker) {
        marker.setLatLng(point);
    } else {
        marker = L.marker(point).addTo(map);
    }
}
var baseMaps = {
    "Satellite": satellite
}
L.control.layers(baseMaps).addTo(map);
map.on("click", (e) => setLocation(e.latlng.lat, e.latlng.lng));

if (hasSavedLocation) {
    setLocation(savedLatitude, savedLongitude);
} else if (!navigator.geolocation) {
    alert("Location is deactivated !");
} else {
    navigator.geolocation.getCurrentPosition(
        ({ coords }) => setLocation(coords.latitude, coords.longitude),
        (error) => {
            console.error("Geolocation error:", error.code, error.message);

            const messages = {
                1: "Location permission was denied.",
                2: "Your device could not determine a location.",
                3: "Getting your location timed out.",
            };

            alert(messages[error.code] ?? error.message);
        },
        { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
}
}