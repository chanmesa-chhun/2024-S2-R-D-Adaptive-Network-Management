<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Cell Tower Prioritization Ranking</title>
  <!-- Leaflet CSS -->
  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet/dist/leaflet.css"
  />
  <style>
    body { margin:0; font-family: sans-serif; }
    #map { width:100%; height:400px; margin-bottom:20px; }
    table {
      width:100%;
      border-collapse: collapse;
      margin-bottom: 40px;
    }
    th, td {
      border:1px solid #aaa;
      padding:6px;
      text-align: center;
    }
    th {
      background:#eee;
    }
    #controls {
      text-align:center;
      margin:20px;
    }
    #download-link a {
      text-decoration:none;
      color:#007bff;
    }
  </style>
</head>
<body>

  <h1 style="text-align:center; margin-top:20px;">
    Cell Tower Prioritization Ranking in Crisis
  </h1>

  <div id="controls">
    <input type="file" id="failed-csv" accept=".csv" />
    <button id="run-ranking">Run Ranking</button>
    <div id="download-link"></div>
  </div>

  <div id="map"></div>

  <table>
    <thead>
      <tr>
        <th>Tower ID</th>
        <th>Lat</th>
        <th>Lng</th>
        <th>Unweighted Pop</th>
        <th>Weighted Pop</th>
        <th>Hospitals</th>
        <th>Police</th>
        <th>Fire Stations</th>
        <th>Score</th>
      </tr>
    </thead>
    <tbody id="result-body"></tbody>
  </table>

  <!-- Leaflet JS -->
  <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
  <script>
    // 1) Initialize map
    const map = L.map('map').setView([-36.8485, 174.7633], 7);

    // 2) Add OSM basemap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> contributors'
    }).addTo(map);

    // 3) Plot all tower locations from GeoJSON
    fetch('http://localhost:8000/static/tower_locations.geojson')
      .then(resp => resp.json())
      .then(data => {
        L.geoJSON(data, {
          pointToLayer: (feature, latlng) =>
            L.circleMarker(latlng, {
              radius: 5,
              fillColor: '#007bff',
              color: '#fff',
              weight: 1,
              fillOpacity: 0.8
            }),
          onEachFeature: (feature, layer) => {
            // use the 'tower' or 'LEGEND' property for popup
            const id = feature.properties.tower || feature.properties.LEGEND;
            if (id) layer.bindPopup(`<strong>${id}</strong>`);
          }
        }).addTo(map);
      })
      .catch(err => console.error('Failed to load tower locations:', err));

    // 4) Prepare a layer group for ranking markers
    const rankingLayer = L.layerGroup().addTo(map);

    // 5) Wire up the Run Ranking button
    document.getElementById('run-ranking').addEventListener('click', async () => {
      const fileInput = document.getElementById('failed-csv');
      if (!fileInput.files.length) {
        return alert('Please select a CSV file of failed towers.');
      }

      // upload form
      const form = new FormData();
      form.append('file', fileInput.files[0]);

      // call backend
      const resp = await fetch('http://localhost:8000/run-ranking', {
        method: 'POST',
        body: form
      });
      if (!resp.ok) {
        const err = await resp.json();
        return alert('Error: ' + (err.error || JSON.stringify(err)));
      }
      const { results, download_url } = await resp.json();

      // clear old ranking markers & table
      rankingLayer.clearLayers();
      const tbody = document.getElementById('result-body');
      tbody.innerHTML = '';

      // show download link
      document.getElementById('download-link').innerHTML =
        `<a href="http://localhost:8000${download_url}" target="_blank">
           Download full ranked CSV
         </a>`;

      // columns to display
      const cols = [
        'tower_id','lat','lng',
        'unweighted_population','weighted_population',
        'hospital','police','fire_station','score'
      ];

      // populate table & map
      for (const row of results) {
        // table
        const tr = document.createElement('tr');
        cols.forEach(col => {
          const td = document.createElement('td');
          td.textContent = row[col] ?? '';
          tr.appendChild(td);
        });
        tbody.appendChild(tr);

        // ranking marker
        const lat = parseFloat(row.lat);
        const lng = parseFloat(row.lng);
        if (!isNaN(lat) && !isNaN(lng)) {
          L.marker([lat, lng])
            .bindPopup(`<strong>${row.tower_id}</strong><br>Score: ${row.score}`)
            .addTo(rankingLayer);
        }
      }
    });
  </script>
</body>
</html>
