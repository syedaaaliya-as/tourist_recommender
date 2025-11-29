document.addEventListener("DOMContentLoaded", function () {

  const btn = document.getElementById("getRecs");
  const ticketBtn = document.getElementById("getTicket");
  const resultsDiv = document.getElementById("results");

  const countrySel = document.getElementById("country");
  const stateSel = document.getElementById("state");
  const citySel = document.getElementById("city");

  let userLat = null;
  let userLng = null;

  // ============================
  // 🌍 REQUEST USER LOCATION
  // ============================
  function requestLocation() {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        pos => {
          userLat = pos.coords.latitude;
          userLng = pos.coords.longitude;

          console.log("📍 User Location:", userLat, userLng);

          map.setView([userLat, userLng], 13);
          L.marker([userLat, userLng], { title: "You are here" }).addTo(map);
        },
        err => {
          alert("⚠ Please enable location to calculate real distance.");
          console.warn(err);
        }
      );
    } else {
      alert("Geolocation not supported");
    }
  }

  // AUTO REQUEST LOCATION ON PAGE LOAD
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
  // 📌 LOAD LOCATION LIST
  // ============================
  fetch("/api/locations")
    .then(r => r.json())
    .then(data => {
      console.log("Location data:", data);

      countrySel.innerHTML = '<option value="">--Select country--</option>';
      Object.keys(data).sort().forEach(c => {
        countrySel.innerHTML += `<option value="${c}">${c}</option>`;
      });

      countrySel.addEventListener("change", () => {
        stateSel.innerHTML = '<option value="">--Select state--</option>';
        citySel.innerHTML = '<option value="">--Select city--</option>';
        const country = countrySel.value;
        if (!country) return;

        Object.keys(data[country]).sort().forEach(s => {
          stateSel.innerHTML += `<option value="${s}">${s}</option>`;
        });
      });

      stateSel.addEventListener("change", () => {
        const country = countrySel.value;
        const state = stateSel.value;
        citySel.innerHTML = '<option value="">--Select city--</option>';
        if (!country || !state) return;

        data[country][state].forEach(city => {
          citySel.innerHTML += `<option value="${city}">${city}</option>`;
        });
      });
    })
    .catch(err => console.error("Fetch error:", err));

  // ============================
  // 📍 SHOW RESULTS ON MAP
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
  // ✨ SEND RECOMMEND REQUEST
  // ============================
  async function sendRec(payload) {
    resultsDiv.innerHTML = "<p>Loading...</p>";

    const resp = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await resp.json();
    console.log("Recommendation data:", data);

    if (!data.results || !data.results.length) {
      resultsDiv.innerHTML = "<p>No results found</p>";
      return;
    }

    let html = "<h3>Top Recommendations</h3>";
    data.results.forEach(r => {
      html += `
        <div class="rec-card">
          <strong>${r.name}</strong> — ${r.type}<br/>
          Cost: ₹${r.avg_cost} | Distance: ${r.real_distance.toFixed(2)} km<br/>
          <button onclick="window.open('https://www.google.com/maps/dir/?api=1&destination=${r.lat},${r.lng}','_blank')">Navigate</button>
        </div>
      `;
    });

    resultsDiv.innerHTML = html;
    showOnMap(data.results);
  }

  // ============================
  // 🎯 BUTTON ACTION
  // ============================
  btn.addEventListener("click", () => {
    if (!userLat || !userLng) {
      alert("Enable location and try again!");
      return;
    }

    sendRec({
      country: countrySel.value,
      state: stateSel.value,
      city: citySel.value,
      type: document.getElementById("type").value,
      avg_cost: Number(document.getElementById("avg_cost").value),
      user_lat: userLat,
      user_lng: userLng,
    });
  });

});
