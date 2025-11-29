document.addEventListener("DOMContentLoaded", function () {

  const btn = document.getElementById("getRecs");
  const results = document.getElementById("results");

  const countrySel = document.getElementById("country");
  const stateSel = document.getElementById("state");
  const citySel = document.getElementById("city");

  let userLat = null;
  let userLng = null;

  // ============================
  // 🌍 USER LOCATION ACCESS
  // ============================
  function requestLocation() {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        pos => {
          userLat = pos.coords.latitude;
          userLng = pos.coords.longitude;

          console.log("📍 User Location:", userLat, userLng);

          map.setView([userLat, userLng], 12);
          L.marker([userLat, userLng], { title: "You are here" }).addTo(map);
        },
        err => {
          alert("⚠ Please enable location services.");
          console.warn(err);
        }
      );
    } else {
      alert("Geolocation not supported by browser");
    }
  }

  requestLocation();

  // ============================
  // 🗺 MAP INITIALIZATION
  // ============================
  let map = L.map("map").setView([20.0, 78.0], 4);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);

  let markers = [];
  let routeLine = null;

  function clearMarkers() {
    markers.forEach(m => map.removeLayer(m));
    markers = [];
    if (routeLine) {
      map.removeLayer(routeLine);
      routeLine = null;
    }
  }

  // ============================
  // 📌 LOAD COUNTRY → STATE → CITY
  // ============================
  fetch("/api/locations")
    .then(r => r.json())
    .then(data => {
      console.log("📍 Location Data Loaded", data);

      countrySel.innerHTML = '<option value="">-- Select Country --</option>';
      Object.keys(data).sort().forEach(c => {
        countrySel.innerHTML += `<option value="${c}">${c}</option>`;
      });

      countrySel.addEventListener("change", () => {
        stateSel.innerHTML = '<option value="">-- Select State --</option>';
        citySel.innerHTML = '<option value="">-- Select City --</option>';
        const country = countrySel.value;
        Object.keys(data[country]).sort().forEach(s => {
          stateSel.innerHTML += `<option value="${s}">${s}</option>`;
        });
      });

      stateSel.addEventListener("change", () => {
        citySel.innerHTML = '<option value="">-- Select City --</option>';
        const country = countrySel.value;
        const state = stateSel.value;
        data[country][state].forEach(city => {
          citySel.innerHTML += `<option value="${city}">${city}</option>`;
        });
      });
    })
    .catch(err => console.error("❌ LOCATION LOAD ERROR", err));

  // ============================
  // ✨ RESULT CARD STYLING
  // ============================
  function displayResults(data) {
    results.innerHTML = `
      <h3 style="text-align:center; font-size:22px; font-weight:700; margin-bottom:12px;">
        Top Recommendations
      </h3>
    `;

    data.results.forEach(r => {
      results.innerHTML += `
        <div class="rec-card">
          <strong style="font-size:18px;">${r.name}</strong> — ${r.type}<br/>
          <span>Cost: ₹${r.avg_cost} | Distance: ${r.real_distance.toFixed(2)} km</span><br/>

          <button class="navigate-btn"
            onclick="window.open('https://www.google.com/maps/dir/?api=1&destination=${r.lat},${r.lng}', '_blank')">
            Navigate
          </button>
        </div>
      `;
    });
  }

  // ============================
  // 🗺 DISPLAY MARKERS ON MAP
  // ============================
  function showOnMap(results) {
    clearMarkers();

    results.forEach(r => {
      const m = L.marker([r.lat, r.lng]).addTo(map);
      m.bindPopup(`<b>${r.name}</b><br>${r.type}`);
      markers.push(m);

      if (userLat && userLng) {
        routeLine = L.polyline(
          [[userLat, userLng], [r.lat, r.lng]],
          { color: "blue", weight: 4 }
        ).addTo(map);
      }
    });
  }

  // ============================
  // 🎯 REQUEST RECOMMENDATIONS
  // ============================
  async function sendRec(payload) {
    results.innerHTML = "<p style='text-align:center;'>Loading...</p>";

    const resp = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await resp.json();
    console.log("✨ Recommendation Response:", data);

    if (!data.results || !data.results.length) {
      results.innerHTML = "<p style='text-align:center;'>No results found</p>";
      return;
    }

    displayResults(data);
    showOnMap(data.results);
  }

  // ============================
  // 🟢 BUTTON CLICK
  // ============================
  btn.addEventListener("click", () => {
    if (!userLat || !userLng) {
      alert("Please enable location first.");
      return;
    }

    sendRec({
      country: countrySel.value,
      state: stateSel.value,
      city: citySel.value,
      type: document.getElementById("type").value,
      avg_cost: Number(document.getElementById("avg_cost").value),
      weather: document.getElementById("weather").value,
      travel_type: document.getElementById("travel_type").value,
      budget_level: document.getElementById("budget_level").value,
      travel_mode: document.getElementById("travel_mode").value,
      user_lat: userLat,
      user_lng: userLng,
    });
  });

});
