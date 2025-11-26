// static/app.js
document.addEventListener("DOMContentLoaded", function(){
  const btn = document.getElementById("getRecs");
  if (!btn) return;
  btn.addEventListener("click", async function(){
    const payload = {
      type: document.getElementById("type").value,
      avg_cost: Number(document.getElementById("avg_cost").value || 0),
      distance_km: Number(document.getElementById("distance_km").value || 5),
      weather: document.getElementById("weather").value,
      travel_type: document.getElementById("travel_type").value,
      budget_level: document.getElementById("budget_level").value,
      open_hour: new Date().getHours()
    };
    // optional: attempt geolocation (not used directly here, could be sent to server)
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(function(pos){
        // we could augment payload with coords if dataset had lat/lon
        payload.lat = pos.coords.latitude;
        payload.lon = pos.coords.longitude;
        send(payload);
      }, function(err){
        // user denied or error -> still send
        send(payload);
      }, {timeout:5000});
    } else {
      send(payload);
    }
  });

  async function send(payload){
    const resDiv = document.getElementById("results");
    resDiv.innerHTML = "<p>Loading recommendations...</p>";
    try {
      const resp = await fetch("/api/recommend", {
        method: "POST",
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(payload)
      });
      if (!resp.ok) {
        const err = await resp.json();
        resDiv.innerHTML = "<p style='color:red'>Error: " + (err.error || "unknown") + "</p>";
        return;
      }
      const data = await resp.json();
      if (!data.results || data.results.length === 0) {
        resDiv.innerHTML = "<p>No recommendations found.</p>";
        return;
      }
      let html = "<h4>Top recommendations</h4>";
      data.results.forEach(r => {
        html += `<div style="border:1px solid #eee;padding:8px;margin:8px 0;border-radius:6px;">
                  <strong>${r.name}</strong> — ${r.type} — ₹${r.avg_cost} — ${r.distance_km} km<br/>
                  <small>Open hour: ${r.open_hour}. ${r.short_description}</small>
                </div>`;
      });
      resDiv.innerHTML = html;
    } catch (e) {
      resDiv.innerHTML = "<p style='color:red'>Network error</p>";
    }
  }
});
