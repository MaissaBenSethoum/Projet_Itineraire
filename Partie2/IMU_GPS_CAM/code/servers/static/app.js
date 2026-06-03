  const map = L.map("map").setView([49.3867, 1.0723], 17);
  let startTime = null;
  let intervalData = null;
  let intervalTimer = null;

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap",
    maxZoom: 19,
  }).addTo(map);

  const polyline = L.polyline([], { color: "#2ecc71", weight: 3 }).addTo(map);
  let marker = null;

  const photoLayer = L.layerGroup().addTo(map);
  let photosLoaded = new Set();

  const statusEl = document.getElementById("status");
  const infoPts = document.getElementById("info-points");
  const infoPhotos = document.getElementById("info-photos");

  const cameraIcon = L.divIcon({
    html: '<div style="font-size:22px;">📷</div>',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    className: ''
  });

  async function fetchPhotos() {
    try {
      const res = await fetch("/photos");
      const photos = await res.json();
      infoPhotos.textContent = photos.length;

      photos.forEach((p) => {
        const id = p.filename;
        if (photosLoaded.has(id)) return;
        photosLoaded.add(id);

        const popupHtml = `
          <div style="text-align:center;">
            <img src="/photo/${p.filename}" style="max-width:250px; border-radius:4px;" />
          </div>
        `;

        L.marker([p.lat, p.lon], { icon: cameraIcon })
         .bindPopup(popupHtml, { maxWidth: 280 })
         .addTo(photoLayer);
      });
    } catch (e) {
      console.error("Erreur fetchPhotos:", e);
    }
  }

  async function fetchData() {
    try {
      const res = await fetch("/data");
      const json = await res.json();
      const points = json.points || [];
      const current = json.current;

      infoPts.textContent = points.length;

      if (points.length > 1) {
        polyline.setLatLngs(points);
      }

      if (current) {
        if (!marker) {
          marker = L.marker(current).addTo(map);
          map.setView(current, 17);
        } else {
          marker.setLatLng(current);
        }
        statusEl.textContent = "En direct";
        statusEl.className = "live";
      }
      fetchPhotos();
    } catch (e) {
      statusEl.textContent = "Erreur serveur";
      statusEl.className = "";
      console.error(e);
    }
  }

  async function lancer_acquisition() {
    try {
      const res = await fetch("/start", { method: "POST" });
      const json = await res.json();
      if (json.status === "already_running") {
        console.warn("Acquisition déjà en cours.");
        return;
      }
    } catch (e) {
      console.error("Erreur /start :", e);
      return;
    }

    // Remise à zéro de la carte
    polyline.setLatLngs([]);
    if (marker) { map.removeLayer(marker); marker = null; }
    photoLayer.clearLayers();
    photosLoaded.clear();
    statusEl.textContent = "En direct";
    statusEl.className = "live";

    document.getElementById("btn-start").disabled = true;
    document.getElementById("btn-stop").disabled = false;
    document.getElementById("status-label").textContent = "Acquisition en cours...";
    document.getElementById("summary").classList.remove("visible");
    startTime = Date.now();
    document.getElementById("timer-label").textContent = "00:00:00";
    intervalTimer = setInterval(() => {
      const s = Math.round((Date.now() - startTime) / 1000);
      document.getElementById("timer-label").textContent = formatDuration(s);
    }, 1000);
    fetchData();
    intervalData = setInterval(fetchData, 1000);
  }

  async function arreter_acquisition() {
    clearInterval(intervalData);
    clearInterval(intervalTimer);
    intervalData = null;
    intervalTimer = null;
    try {
      await fetch("/stop", { method: "POST" });
    } catch (e) {
      console.error("Erreur /stop :", e);
    }
    finAcquisition();
  }

  function haversine([lat1, lon1], [lat2, lon2]) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  function formatDuration(seconds) {
    const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
    const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
    const s = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
  }

  function setSummary(distance, duration, speedAvg) {
    document.getElementById("res-distance").textContent = distance.toFixed(2) + " km";
    document.getElementById("res-duration").textContent = formatDuration(duration);
    document.getElementById("res-speed-avg").textContent = speedAvg.toFixed(2) + " km/h";
    document.getElementById("summary").classList.add("visible");
  }

  function finAcquisition() {
    document.getElementById("btn-start").disabled = false;
    document.getElementById("btn-stop").disabled = true;
    document.getElementById("status-label").textContent = "Acquisition terminée";
    const elapsed = Math.round((Date.now() - startTime) / 1000);
    const latlngs = polyline.getLatLngs();
    let distance = 0;
    for (let i = 1; i < latlngs.length; i++) {
      distance += haversine(
        [latlngs[i - 1].lat, latlngs[i - 1].lng],
        [latlngs[i].lat, latlngs[i].lng]
      );
    }
    const speedAvg = elapsed > 0 ? distance / (elapsed / 3600) : 0;
    setSummary(distance, elapsed, speedAvg);
  }
