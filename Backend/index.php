<!DOCTYPE html>
<html>
<head>
  <title>Google Map with CSV Markers, Emergency Services & Population Coverage</title>
  <link rel="stylesheet" type="text/css" href="styles.css">

  <!-- Google Maps JavaScript API with Places and Geometry libraries -->
  <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyAlRJJEG94C4gjwn8sqJN0BbDpOUL2jrNs&libraries=places,geometry"></script>

  <!-- PapaParse for CSV parsing -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.3.2/papaparse.min.js"></script>

  <script>
    let map;                       // Global map variable
    let cellTowerMarkers = [];     // Array to store cell tower markers
    let circles = [];              // Array to store circles
    let currentCircle = null;      // Currently displayed circle
    let currentFacilityMarkers = []; // Facility markers for selected tower
    let populationData = [];       // Array for population grid data

    // Load population CSV (already in lat/lng)
    function loadPopulationData(callback) {
      fetch('population_250m_latlng.csv')
        .then(response => response.text())
        .then(csvText => {
          const parsed = Papa.parse(csvText, { header: true });
          populationData = parsed.data;
          callback();
        })
        .catch(err => {
          console.error("Error loading population data:", err);
          callback();
        });
    }

    // Calculate total population within 5km of a given tower (using grid centroids)
    function calculatePopulationCoverage(towerLatLng) {
      let totalPop = 0;
      populationData.forEach(cell => {
        const cellLat = parseFloat(cell.lat);
        const cellLng = parseFloat(cell.lng);
        if (isNaN(cellLat) || isNaN(cellLng)) return;
        const cellLatLng = new google.maps.LatLng(cellLat, cellLng);
        const distance = google.maps.geometry.spherical.computeDistanceBetween(towerLatLng, cellLatLng);
        if (distance <= 5000) { // within 5km
          const pop = parseFloat(cell.PopEst2022) || 0;
          totalPop += pop;
        }
      });
      return totalPop;
    }

    function initMap() {
      const center = { lat: -36.8485, lng: 174.7633 };

      map = new google.maps.Map(document.getElementById('map'), {
        zoom: 7,
        center: center,
        styles: [
          { featureType: "poi", stylers: [{ visibility: "off" }] },
          { featureType: "transit", stylers: [{ visibility: "off" }] }
        ],
        mapTypeId: google.maps.MapTypeId.TERRAIN
      });

      const service = new google.maps.places.PlacesService(map);

      // First, load population data then fetch cell tower markers.
      loadPopulationData(function() {
        fetch('markers.php')
          .then(response => response.json())
          .then(data => {
            const tableBody = document.getElementById('tower-body');

            data.forEach(markerData => {
              // Choose icon based on CSV status ("YES" or "NO")
              const markerIcon = markerData.status === "NO" ? 'celltower_down_icon.png' : 'celltower_icon3.png';

              const marker = new google.maps.Marker({
                position: { lat: markerData.lat, lng: markerData.lng },
                map: map,
                title: markerData.sitename,
                icon: {
                  url: markerIcon,
                  scaledSize: new google.maps.Size(32, 32),
                  anchor: new google.maps.Point(16, 32)
                }
              });
              // Store the CSV status in a custom property; default "YES"
              marker.customStatus = markerData.status;
              cellTowerMarkers.push(marker);

              // Create a table row for the cell tower info.
              const row = document.createElement('tr');

              // Site Name cell
              const nameCell = document.createElement('td');
              nameCell.textContent = markerData.sitename;
              row.appendChild(nameCell);

              // Coordinates cell
              const coordCell = document.createElement('td');
              coordCell.textContent = `(${markerData.lat}, ${markerData.lng})`;
              row.appendChild(coordCell);

              // Population (5km) cell (initially blank)
              const popCell = document.createElement('td');
              popCell.textContent = "—";
              row.appendChild(popCell);

              // Hospitals/Clinics cell
              const hospitalCell = document.createElement('td');
              hospitalCell.textContent = "Loading...";
              row.appendChild(hospitalCell);

              // Police Stations cell
              const policeCell = document.createElement('td');
              policeCell.textContent = "Loading...";
              row.appendChild(policeCell);

              // Fire Stations cell
              const fireCell = document.createElement('td');
              fireCell.textContent = "Loading...";
              row.appendChild(fireCell);

              // Nearby Towers cell
              const towersCell = document.createElement('td');
              towersCell.textContent = "Loading...";
              row.appendChild(towersCell);

              // Set dataset values for sorting
              row.dataset.hospital = 0;
              row.dataset.police = 0;
              row.dataset.fire = 0;
              row.dataset.towers = 0;
              // Will also later store population as row.dataset.population

              // Save references on the marker for later update.
              marker.tableRow = row;
              marker.popCell = popCell;

              // On row click, center the map, draw 5km circle, and show facilities.
              row.addEventListener('click', () => {
                map.setCenter(marker.getPosition());
                map.setZoom(12);
                if (currentCircle) currentCircle.setMap(null);
                clearFacilityMarkers();
                currentCircle = new google.maps.Circle({
                  map: map,
                  center: marker.getPosition(),
                  radius: 5000,
                  fillColor: '#FF0000',
                  fillOpacity: 0.1,
                  strokeColor: '#FF0000',
                  strokeOpacity: 0.8,
                  strokeWeight: 2
                });
                showFacilitiesForTower(marker.getPosition(), service);
              });

              tableBody.appendChild(row);

              // Emergency service queries (unchanged)
              searchEmergencyServicesForTowerType(marker.getPosition(), 'hospital', service)
                .then(results => {
                  const unique = {};
                  results.forEach(r => { unique[r.place_id] = r; });
                  const count = Object.keys(unique).length;
                  hospitalCell.textContent = count;
                  row.dataset.hospital = count;
                  sortTable();
                })
                .catch(err => {
                  console.error("Error searching hospitals:", err);
                  hospitalCell.textContent = "Error";
                });

              searchEmergencyServicesForTowerType(marker.getPosition(), 'police', service)
                .then(results => {
                  const unique = {};
                  results.forEach(r => { unique[r.place_id] = r; });
                  const count = Object.keys(unique).length;
                  policeCell.textContent = count;
                  row.dataset.police = count;
                  sortTable();
                })
                .catch(err => {
                  console.error("Error searching police stations:", err);
                  policeCell.textContent = "Error";
                });

              searchEmergencyServicesForTowerType(marker.getPosition(), 'fire_station', service)
                .then(results => {
                  const unique = {};
                  results.forEach(r => { unique[r.place_id] = r; });
                  const count = Object.keys(unique).length;
                  fireCell.textContent = count;
                  row.dataset.fire = count;
                  sortTable();
                })
                .catch(err => {
                  console.error("Error searching fire stations:", err);
                  fireCell.textContent = "Error";
                });

              // Count nearby towers (within 5km)
              const towerLatLng = new google.maps.LatLng(markerData.lat, markerData.lng);
              let nearbyTowerCount = 0;
              data.forEach(other => {
                if (markerData.lat === other.lat && markerData.lng === other.lng) return;
                const otherLatLng = new google.maps.LatLng(other.lat, other.lng);
                const distance = google.maps.geometry.spherical.computeDistanceBetween(towerLatLng, otherLatLng);
                if (distance <= 5000) nearbyTowerCount++;
              });
              towersCell.textContent = nearbyTowerCount;
              row.dataset.towers = nearbyTowerCount;
            });
          })
          .catch(error => console.error('Error loading markers:', error));
      });

      // --- Random Event Button ---
      // Now uses a 10% chance to mark a tower as "NO"
      document.getElementById("random-event").addEventListener("click", function() {
        cellTowerMarkers.forEach(marker => {
          if (Math.random() < 0.1) {
            marker.setIcon({
              url: 'celltower_down_icon.png',
              scaledSize: new google.maps.Size(32, 32),
              anchor: new google.maps.Point(16, 32)
            });
            marker.customStatus = "NO";
          }
        });
      });

      // --- Run Button ---
      // Calculate population coverage only for towers with status "NO" and update the table.
      document.getElementById("run-coverage").addEventListener("click", function() {
        const tableBody = document.getElementById("tower-body");
        let filteredRows = [];
        cellTowerMarkers.forEach(marker => {
          if (marker.customStatus === "NO") {
            const towerLatLng = marker.getPosition();
            const populationCovered = calculatePopulationCoverage(towerLatLng);
            marker.popCell.textContent = populationCovered.toFixed(0);
            marker.tableRow.dataset.population = populationCovered;
            marker.tableRow.style.display = ""; // ensure row is visible
            filteredRows.push(marker.tableRow);
          } else {
            // Hide rows for towers not marked "NO"
            marker.tableRow.style.display = "none";
          }
        });
        // Sort the filtered rows by population (descending)
        filteredRows.sort((a, b) => {
          const popA = parseFloat(a.dataset.population) || 0;
          const popB = parseFloat(b.dataset.population) || 0;
          return popB - popA;
        });
        tableBody.innerHTML = "";
        filteredRows.forEach(row => {
          tableBody.appendChild(row);
        });
      });

      // --- Reset Markers Button ---
      // Revert all markers back to "YES" status and show all rows.
      document.getElementById("reset-markers").addEventListener("click", function() {
        cellTowerMarkers.forEach(marker => {
          marker.setIcon({
            url: 'celltower_icon3.png',
            scaledSize: new google.maps.Size(32, 32),
            anchor: new google.maps.Point(16, 32)
          });
          marker.customStatus = "YES";
          marker.tableRow.style.display = "";
          marker.popCell.textContent = "—";
        });
      });
    }

    // Helper: Search for emergency service of a given type
    function searchEmergencyServicesForTowerType(location, type, service) {
      return new Promise(resolve => {
        const request = {
          location: location,
          radius: '5000',
          type: type
        };
        service.nearbySearch(request, (results, status) => {
          if (status === google.maps.places.PlacesServiceStatus.OK && results) {
            resolve(results);
          } else {
            resolve([]);
          }
        });
      });
    }

    // Helper: Clear facility markers
    function clearFacilityMarkers() {
      if (currentFacilityMarkers.length) {
        currentFacilityMarkers.forEach(marker => marker.setMap(null));
        currentFacilityMarkers = [];
      }
    }

    // Helper: Show facility markers around a tower location
    function showFacilitiesForTower(location, service) {
      const emergencyTypes = ['hospital', 'police', 'fire_station'];
      emergencyTypes.forEach(type => {
        const request = {
          location: location,
          radius: '5000',
          type: type
        };
        service.nearbySearch(request, (results, status) => {
          if (status === google.maps.places.PlacesServiceStatus.OK && results) {
            results.forEach(place => {
              const marker = new google.maps.Marker({
                map: map,
                position: place.geometry.location,
                title: place.name,
                icon: getIconForType(type) || undefined
              });
              currentFacilityMarkers.push(marker);
            });
          }
        });
      });
    }

    // Helper: Return an icon for a given emergency service type
    function getIconForType(type) {
      let iconUrl = null;
      if (type === 'hospital') iconUrl = 'hospital_icon.png';
      else if (type === 'police') iconUrl = 'police_station_icon.png';
      else if (type === 'fire_station') iconUrl = 'firestation_icon.png';
      if (!iconUrl) return null;
      return {
        url: iconUrl,
        scaledSize: new google.maps.Size(32, 32),
        anchor: new google.maps.Point(8, 16)
      };
    }

    // Show 5km circles around all towers
    function showCircles() {
      hideCircles();
      cellTowerMarkers.forEach(marker => {
        const circle = new google.maps.Circle({
          map: map,
          center: marker.getPosition(),
          radius: 5000,
          fillColor: '#FF0000',
          fillOpacity: 0.05,
          strokeColor: '#FF0000',
          strokeOpacity: 0.8,
          strokeWeight: 2
        });
        circles.push(circle);
      });
    }

    // Hide circles and facility markers
    function hideCircles() {
      circles.forEach(circle => circle.setMap(null));
      circles = [];
      if (currentCircle) {
        currentCircle.setMap(null);
        currentCircle = null;
      }
      clearFacilityMarkers();
    }

    // Sorting function: now includes a "Population" option.
    function sortTable() {
      const select = document.getElementById("priority-select");
      const priority = select.value; // Could be "hospital", "police", "fire", "towers", or "population"
      if (!priority) return;
      const tableBody = document.getElementById("tower-body");
      const rowsArray = Array.from(tableBody.getElementsByTagName("tr"));
      rowsArray.sort((a, b) => {
        const countA = parseFloat(a.dataset[priority]) || 0;
        const countB = parseFloat(b.dataset[priority]) || 0;
        return countB - countA;
      });
      tableBody.innerHTML = "";
      rowsArray.forEach(row => tableBody.appendChild(row));
    }

    window.onload = initMap;
  </script>
</head>
<body>
  <h1 style="text-align: center;">Map of Cell Towers</h1>
  <div id="map" style="width:100%; height:500px;"></div>
  
  <!-- Buttons: Show/Hide Circles, Random Event, Run, Reset -->
  <div style="text-align: center; margin: 10px;">
    <button onclick="showCircles()">Show 5km Area Around All Cell Towers</button>
    <button onclick="hideCircles()">Hide 5km Areas</button>
    <button id="random-event">Random Event</button>
    <button id="run-coverage">Run</button>
    <button id="reset-markers">Reset Markers</button>
  </div>

  <!-- Sorting dropdown: now includes "Population" -->
  <div style="text-align: center; margin: 10px;">
    <label for="priority-select">Prioritize by:</label>
    <select id="priority-select" onchange="sortTable()">
      <option value="">Select Priority</option>
      <option value="hospital">Hospital/Clinic</option>
      <option value="police">Police Station</option>
      <option value="fire">Fire Station</option>
      <option value="towers">Nearby Towers</option>
      <option value="population">Population</option>
    </select>
  </div>

  <h2>Cell Tower List</h2>
  <table>
    <thead>
      <tr>
        <th>Site Name</th>
        <th>Coordinates</th>
        <th>Population (5km)</th>
        <th>Hospitals/Clinics</th>
        <th>Police Stations</th>
        <th>Fire Stations</th>
        <th>Nearby Towers</th>
      </tr>
    </thead>
    <tbody id="tower-body"></tbody>
  </table>
</body>
</html>
