<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Cell Tower Failure Ranking</title>
  <link rel="stylesheet" href="styles.css">

  <!-- Google Maps JS API -->
  <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyAlRJJEG94C4gjwn8sqJN0BbDpOUL2jrNs&libraries=geometry"></script>
</head>
<body>
  <h1 style="text-align:center;">Cell Tower Prioritization Ranking in Crisis</h1>

  <div style="text-align:center; margin:20px;">
    <input type="file" id="failed-csv" accept=".csv" />
    <button id="run-ranking">Run Ranking</button>
    <div id="download-link" style="margin-top:10px;"></div>
  </div>

  <div id="map" style="width:100%; height:400px; margin-bottom:20px;"></div>

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

  <script>
    let map;
    const markers = [];

    function initMap() {
      map = new google.maps.Map(document.getElementById('map'), {
        center: { lat: -36.8485, lng: 174.7633 },
        zoom: 7,
        mapTypeId: google.maps.MapTypeId.TERRAIN
      });
    }

    async function runRanking() {
      const fileInput = document.getElementById('failed-csv');
      if (!fileInput.files.length) {
        return alert('Please select a CSV file of failed towers.');
      }

      const form = new FormData();
      form.append('file', fileInput.files[0]);

      const resp = await fetch('http://localhost:8000/run-ranking', {
        method: 'POST',
        body: form
      });

      if (!resp.ok) {
        const err = await resp.json();
        return alert('Error: ' + (err.error || JSON.stringify(err)));
      }

      const { results, download_url } = await resp.json();

      // clear old markers
      markers.forEach(m => m.setMap(null));
      markers.length = 0;

      // rebuild table
      const tbody = document.getElementById('result-body');
      tbody.innerHTML = '';

      // fix download link to hit your backend port
      document.getElementById('download-link').innerHTML =
        `<a href="http://localhost:8000${download_url}" target="_blank">
           Download full ranked CSV
         </a>`;

      // define columns in order
      const cols = [
        'tower_id',
        'lat',
        'lng',
        'unweighted_population',
        'weighted_population',
        'hospital',
        'police',
        'fire_station',
        'score'
      ];

      results.forEach(row => {
        // plot marker if lat/lng present
        const lat = parseFloat(row.lat);
        const lng = parseFloat(row.lng);
        if (!isNaN(lat) && !isNaN(lng)) {
          const marker = new google.maps.Marker({
            position: { lat, lng },
            map,
            title: row.tower_id
          });
          markers.push(marker);
        }

        // build table row
        const tr = document.createElement('tr');
        cols.forEach(col => {
          const td = document.createElement('td');
          td.textContent = row[col] ?? '';
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
    }

    window.onload = () => {
      initMap();
      document.getElementById('run-ranking').addEventListener('click', runRanking);
    };
  </script>
</body>
</html>
