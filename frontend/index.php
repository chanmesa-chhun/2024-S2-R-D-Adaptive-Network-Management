<?php
// index.php
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Cell Tower Prioritization Ranking</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
  <link rel="stylesheet" href="styles.css" />
  <style>
    body { margin:0; font-family: sans-serif; }
    #map { width:100%; height:400px; margin-bottom:20px; }
    table { width:100%; border-collapse: collapse; margin-bottom: 40px; }
    th, td { border:1px solid #aaa; padding:6px; text-align:center; }
    th { background:#eee; }
    #controls { text-align:center; margin:20px; }
    #download-link a { text-decoration:none; color:#007bff; }
  </style>
</head>
<body>
  <nav class="navbar">
    <ul>
      <li><a href="#">Homepage</a></li>
      <li><a href="#map">Map</a></li>
      <li><a href="#legend">Legend</a></li>
      <li><a href="#documentation">Documentation</a></li>
    </ul>
  </nav>

  <h1 style="text-align:center; margin-top:20px;">
    Cell Tower Prioritization Ranking in Crisis
  </h1>

  <div id="controls">
    <form id="ranking-form" enctype="multipart/form-data">
      <input type="file" name="file" id="failed-csv" accept=".csv" required />
      <select name="scenario" id="scenario" required>
        <option value="Default">Default</option>
        <option value="Tsunami">Tsunami</option>
        <option value="Wildfire">Wildfire</option>
        <option value="Earthquake">Earthquake</option>
        <option value="Flood">Flood</option>
        <option value="Storm">Storm</option>
        <option value="Volcanic Eruption">Volcanic Eruption</option>
      </select>
      <button type="submit" id="run-ranking">Run Ranking</button>
    </form>
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

  <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
  <script>
    // init map
    const map = L.map('map').setView([-36.8485, 174.7633], 7);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
      maxZoom:19,
      attribution:'&copy; OSM contributors'
    }).addTo(map);
    const rankingLayer = L.layerGroup().addTo(map);

    // draw base tower layer (static)
    fetch('http://localhost:8000/static/tower_locations.geojson')
      .then(r=>r.json())
      .then(data=>{
        L.geoJSON(data, {
          pointToLayer:(f,latlng)=>L.circleMarker(latlng,{
            radius:5, fillColor:'#007bff', color:'#fff',
            weight:1, fillOpacity:0.8
          }),
          onEachFeature:(f,lyr)=>{
            const id = f.properties.tower||f.properties.LEGEND;
            if(id) lyr.bindPopup(`<strong>${id}</strong>`)
          }
        }).addTo(map);
      })
      .catch(console.error);

    // form submission
    document.getElementById('ranking-form').addEventListener('submit', async e=>{
      e.preventDefault();
      const form = e.target;
      const formData = new FormData(form);

      // clear old
      rankingLayer.clearLayers();
      document.getElementById('result-body').innerHTML = '';
      document.getElementById('download-link').innerHTML = '';

      const resp = await fetch('http://localhost:8000/run-ranking', {
        method: 'POST',
        body: formData
      });
      if(!resp.ok){
        const err = await resp.json();
        return alert('Error: '+(err.error||JSON.stringify(err)));
      }
      const { results, download_url } = await resp.json();

      // download link
      document.getElementById('download-link').innerHTML =
        `<a href="http://localhost:8000${download_url}" target="_blank">
           Download full ranked CSV
         </a>`;

      // columns & rendering
      const cols = [
        'tower_id','lat','lng',
        'unweighted_population','weighted_population',
        'hospital','police','fire_station','score'
      ];
      for(const row of results){
        // table
        const tr = document.createElement('tr');
        cols.forEach(col=>{
          const td = document.createElement('td');
          td.textContent = row[col] ?? '';
          tr.appendChild(td);
        });
        document.getElementById('result-body').appendChild(tr);

        // map marker
        const lat = parseFloat(row.lat),
              lng = parseFloat(row.lng);
        if(!isNaN(lat)&&!isNaN(lng)){
          L.marker([lat,lng])
            .bindPopup(`<strong>${row.tower_id}</strong><br>Score: ${row.score}`)
            .addTo(rankingLayer);
        }
      }
    });

  </script>
  <div class="legend" id="legend">
    <h2>Legend</h2>
      <ul>
        <li>Tower_ID is based on each site</li>
        <li>Facilities coverage only counts if no other tower is covering</li>
        <li>Score is the final result considering facilities, population and type of disaster</li>
      </ul>
  </div>
  <section id="documentation" class="documentation">
    <h2>Documentation</h2>
    
  </section>

</body>
</html>
