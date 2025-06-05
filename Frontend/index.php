<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Cell Tower Prioritization Ranking</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
  <link rel="stylesheet" href="styles.css" />
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

  <form id="ranking-form" enctype="multipart/form-data" class="ranking-form">
    <div class="form-group">
      <label for="failed-csv">Upload failed towers (.csv):</label>
      <input type="file" name="failed_towers" id="failed-csv" accept=".csv" required />
    </div>

    <div class="form-group">
      <label for="scenario">Select type of disaster:</label>
      <select name="disaster_type" id="scenario" required>
        <option value="Default">Default</option>
        <option value="Tsunami">Tsunami</option>
        <option value="Wildfire">Wildfire</option>
        <option value="Earthquake">Earthquake</option>
        <option value="Flood">Flood</option>
        <option value="Storm">Storm</option>
        <option value="Volcanic Eruption">Volcanic Eruption</option>
      </select>
    </div>

    <div class="form-group">
      <label for="prefix_start">Prefix start:</label>
      <input type="text" name="prefix_start" id="prefix_start" placeholder="e.g. 001"/>
    </div>

    <div class="form-group">
      <label for="prefix_end">Prefix end:</label>
      <input type="text" name="prefix_end" id="prefix_end" placeholder="e.g. 050"/>
    </div>

    <div class="form-group">
      <button type="submit" id="run-ranking">Run Ranking</button>
    </div>
    
    </form> <!-- close the form here -->

<div class="search-box">
  <label for="search-tower">Search a tower by ID:</label><br>
  <input type="text" id="search-tower" placeholder="Search tower ID…" />
</div>

<div id="download-link"></div>


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
    const map = L.map('map').setView([-36.8485, 174.7633], 7);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
      maxZoom:19,
      attribution:'&copy; OSM contributors'
    }).addTo(map);
    const rankingLayer = L.layerGroup().addTo(map);
    const towerIndex = {};

    document.getElementById('search-tower').addEventListener('keydown', e => {
      if (e.key !== 'Enter') return;
      e.preventDefault();
      const val = e.target.value.trim().toUpperCase();
      const marker = towerIndex[val];
      if (!marker) {
        return alert(`No tower found with ID “${val}”`);
      }
      map.setView(marker.getLatLng(), 13, { animate: true });
      marker.openPopup();
    });

    document.getElementById('ranking-form').addEventListener('submit', async e => {
      e.preventDefault();
      const form = e.target;
      const formData = new FormData(form);

      rankingLayer.clearLayers();
      document.getElementById('result-body').innerHTML = '';
      document.getElementById('download-link').innerHTML = '';

      const resp = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        body: formData
      });
      if (!resp.ok) {
        const err = await resp.json();
        return alert('Error: ' + (err.error || JSON.stringify(err)));
      }

      const { results, download_url } = await resp.json();

      document.getElementById('download-link').innerHTML =
        `<a href="http://localhost:8000${download_url}" target="_blank">
           Download full ranked CSV
         </a>`;

      const cols = [
        'tower_id','lat','lng',
        'unweighted_population','weighted_population',
        'hospital','police','fire_station','score'
      ];
      for (const row of results) {
        const tr = document.createElement('tr');
        cols.forEach(col => {
          const td = document.createElement('td');
          td.textContent = row[col] ?? '';
          tr.appendChild(td);
        });
        document.getElementById('result-body').appendChild(tr);

        const lat = parseFloat(row.lat),
              lng = parseFloat(row.lng);
        if (!isNaN(lat) && !isNaN(lng)) {
          L.marker([lat, lng])
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
      <li>Unweighted Population: The unweighted population refers to the total number of people living within the population grid cells that intersect a tower's exclusive coverage area, without considering how much of each grid cell is actually covered. It assumes the entire population of each overlapping grid is fully covered, even if the tower only covers a small portion of it.  This can lead to overestimation when only partial coverage exists.</li>
      <li>Weighted Population: The weighted population is a more accurate estimate.  It adjusts the population based on how much of each population grid cell is actually covered by the tower’s exclusive area. It calculates the area of intersection between each population grid and the exclusive area. Then it multiplies the proportion of covered area by the total population of the grid.</li>
    </ul>
  </div>

  <section id="documentation" class="documentation">
    <h2>Documentation</h2>
  </section>
</body>
</html>
