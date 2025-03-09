<!DOCTYPE html>
<html>
<head>
  <title>Google Map with CSV Markers & Table</title>
  <link rel="stylesheet" type="text/css" href="styles.css">
  <!-- Include the Google Maps JavaScript API with your API key -->
  <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyAlRJJEG94C4gjwn8sqJN0BbDpOUL2jrNs"></script>
  <script>
    let map; // Make map accessible for the table click events

    function initMap() {
      // Choose a default center
      const center = { lat: -35.373025, lng: 173.830302 };

      // Initialize the map
      map = new google.maps.Map(document.getElementById('map'), {
        zoom: 7,
        center: center,
        styles: [
          { featureType: "poi", stylers: [{ visibility: "off" }] },
          { featureType: "transit", stylers: [{ visibility: "off" }] }
        ],
        mapTypeId: google.maps.MapTypeId.TERRAIN
      });

      // Fetch marker data from markers.php
      fetch('markers.php')
        .then(response => response.json())
        .then(data => {
          // Get the table body element
          const tableBody = document.getElementById('tower-body');

          data.forEach(markerData => {
            // 1. Create a marker
            const marker = new google.maps.Marker({
              position: { lat: markerData.lat, lng: markerData.lng },
              map: map,
              title: markerData.sitename,
              icon: {
                url: 'celltower_icon3.png',
                scaledSize: new google.maps.Size(32, 32),
                anchor: new google.maps.Point(16, 32),
              }
            });

            // 2. Create a table row for each tower
            const row = document.createElement('tr');

            // Site Name column
            const nameCell = document.createElement('td');
            nameCell.textContent = markerData.sitename;
            row.appendChild(nameCell);

            // Coordinates column
            const coordCell = document.createElement('td');
            coordCell.textContent = `(${markerData.lat}, ${markerData.lng})`;
            row.appendChild(coordCell);

            // 3. Clicking the row recenters the map
            row.addEventListener('click', () => {
              map.setCenter(marker.getPosition());
              map.setZoom(12); // Optional zoom level
            });

            // 4. Add the row to the table body
            tableBody.appendChild(row);
          });
        })
        .catch(error => console.error('Error loading markers:', error));
    }

    // Initialize the map when the window loads
    window.onload = initMap;
  </script>
</head>
<body>
  <h1 style="text-align: center;">Map of Cell Towers</h1>
  <div id="map" style="width:100%; height:500px;"></div>

  <h2>Cell Tower List</h2>
  <!-- Table for tower data -->
  <table>
    <thead>
      <tr>
        <th>Site Name</th>
        <th>Coordinates</th>
      </tr>
    </thead>
    <tbody id="tower-body"></tbody>
  </table>
</body>
</html>