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
    let map;                        // Global map variable
    let cellTowerMarkers = [];      // Array to store cell tower markers
    let circles = [];               // Array to store circles
    let currentCircle = null;       // Currently displayed circle
    let currentFacilityMarkers = []; // Facility markers for selected tower
    let populationData = [];        // Array for population grid data
    let hospitalsData = [];         // Array for hospitals data from CSV
    let policeData = [];            // Array for police data from CSV
    let fireStationsData = [];      // Array for fire station data from CSV

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

    // Load hospitals CSV from local file
    function loadHospitalsData(callback) {
      fetch('hospitals_data.csv')
        .then(response => response.text())
        .then(csvText => {
          const parsed = Papa.parse(csvText, { header: true });
          hospitalsData = parsed.data;
          callback();
        })
        .catch(err => {
          console.error("Error loading hospitals data:", err);
          callback();
        });
    }

    // Load police CSV from local file
    function loadPoliceData(callback) {
      fetch('police_data.csv')
        .then(response => response.text())
        .then(csvText => {
          const parsed = Papa.parse(csvText, { header: true });
          policeData = parsed.data;
          callback();
        })
        .catch(err => {
          console.error("Error loading police data:", err);
          callback();
        });
    }

    // Load fire station CSV from local file
    function loadFireStationsData(callback) {
      fetch('firestation_data.csv')
        .then(response => response.text())
        .then(csvText => {
          const parsed = Papa.parse(csvText, { header: true });
          fireStationsData = parsed.data;
          callback();
        })
        .catch(err => {
          console.error("Error loading fire station data:", err);
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

    // Count hospitals within 5km of a given location using CSV data
    function countHospitalsForTower(towerLatLng) {
      let count = 0;
      hospitalsData.forEach(hospital => {
        const lat = parseFloat(hospital.latitude);
        const lng = parseFloat(hospital.longitude);
        if (isNaN(lat) || isNaN(lng)) return;
        const hospitalLatLng = new google.maps.LatLng(lat, lng);
        const distance = google.maps.geometry.spherical.computeDistanceBetween(towerLatLng, hospitalLatLng);
        if (distance <= 5000) {
          count++;
        }
      });
      return count;
    }

    // Count police stations within 5km of a given location using CSV data
    function countPoliceForTower(towerLatLng) {
      let count = 0;
      policeData.forEach(police => {
        const lat = parseFloat(police.latitude);
        const lng = parseFloat(police.longitude);
        if (isNaN(lat) || isNaN(lng)) return;
        const policeLatLng = new google.maps.LatLng(lat, lng);
        const distance = google.maps.geometry.spherical.computeDistanceBetween(towerLatLng, policeLatLng);
        if (distance <= 5000) {
          count++;
        }
      });
      return count;
    }

    // Count fire stations within 5km of a given location using CSV data
    function countFireStationsForTower(towerLatLng) {
      let count = 0;
      fireStationsData.forEach(fireStation => {
        const lat = parseFloat(fireStation.latitude);
        const lng = parseFloat(fireStation.longitude);
        if (isNaN(lat) || isNaN(lng)) return;
        const stationLatLng = new google.maps.LatLng(lat, lng);
        const distance = google.maps.geometry.spherical.computeDistanceBetween(towerLatLng, stationLatLng);
        if (distance <= 5000) {
          count++;
        }
      });
      return count;
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

      // Load population, hospitals, police, and fire station data before fetching cell tower markers.
      loadPopulationData(function() {
        loadHospitalsData(function() {
          loadPoliceData(function() {
            loadFireStationsData(function() {
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

                    // Hospitals/Clinics cell - using local CSV
                    const hospitalCell = document.createElement('td');
                    try {
                      const count = countHospitalsForTower(marker.getPosition());
                      hospitalCell.textContent = count;
                      row.dataset.hospital = count;
                      sortTable();
                    } catch (e) {
                      console.error("Error counting hospitals:", e);
                      hospitalCell.textContent = "Error";
                    }
                    row.appendChild(hospitalCell);

                    // Police Stations cell - using local CSV
                    const policeCell = document.createElement('td');
                    try {
                      const count = countPoliceForTower(marker.getPosition());
                      policeCell.textContent = count;
                      row.dataset.police = count;
                      sortTable();
                    } catch (e) {
                      console.error("Error counting police stations:", e);
                      policeCell.textContent = "Error";
                    }
                    row.appendChild(policeCell);

                    // Fire Stations cell - using local CSV
                    const fireCell = document.createElement('td');
                    try {
                      const count = countFireStationsForTower(marker.getPosition());
                      fireCell.textContent = count;
                      row.dataset.fire = count;
                      sortTable();
                    } catch (e) {
                      console.error("Error counting fire stations:", e);
                      fireCell.textContent = "Error";
                    }
                    row.appendChild(fireCell);

                    // Nearby Towers cell
                    const towersCell = document.createElement('td');
                    towersCell.textContent = "Loading...";
                    row.appendChild(towersCell);

                    // Set dataset values for sorting
                    row.dataset.police = row.dataset.police || 0;
                    row.dataset.fire = row.dataset.fire || 0;
                    row.dataset.towers = 0;
                    // Will also later store population as row.dataset.population

                    // Save references on the marker for later update.
                    marker.tableRow = row;
                    marker.popCell = popCell;

                    // On row click, center the map, draw a 5km circle, and show facilities.
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
          });
        });
      });

      // --- Random Event Button ---
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

    // Helper: Show facility markers around a tower location
    function showFacilitiesForTower(location, service) {
      const emergencyTypes = ['hospital', 'police', 'fire_station'];
      emergencyTypes.forEach(type => {
        if (type === 'hospital') {
          hospitalsData.forEach(hospital => {
            const lat = parseFloat(hospital.latitude);
            const lng = parseFloat(hospital.longitude);
            if (isNaN(lat) || isNaN(lng)) return;
            const facilityLatLng = new google.maps.LatLng(lat, lng);
            const distance = google.maps.geometry.spherical.computeDistanceBetween(location, facilityLatLng);
            if (distance <= 5000) {
              const marker = new google.maps.Marker({
                map: map,
                position: facilityLatLng,
                title: hospital.name || "Hospital",
                icon: getIconForType('hospital') || undefined
              });
              currentFacilityMarkers.push(marker);
            }
          });
        } else if (type === 'police') {
          policeData.forEach(police => {
            const lat = parseFloat(police.latitude);
            const lng = parseFloat(police.longitude);
            if (isNaN(lat) || isNaN(lng)) return;
            const facilityLatLng = new google.maps.LatLng(lat, lng);
            const distance = google.maps.geometry.spherical.computeDistanceBetween(location, facilityLatLng);
            if (distance <= 5000) {
              const marker = new google.maps.Marker({
                map: map,
                position: facilityLatLng,
                title: police.name || "Police Station",
                icon: getIconForType('police') || undefined
              });
              currentFacilityMarkers.push(marker);
            }
          });
        } else if (type === 'fire_station') {
          fireStationsData.forEach(fireStation => {
            const lat = parseFloat(fireStation.latitude);
            const lng = parseFloat(fireStation.longitude);
            if (isNaN(lat) || isNaN(lng)) return;
            const facilityLatLng = new google.maps.LatLng(lat, lng);
            const distance = google.maps.geometry.spherical.computeDistanceBetween(location, facilityLatLng);
            if (distance <= 5000) {
              const marker = new google.maps.Marker({
                map: map,
                position: facilityLatLng,
                title: fireStation.name || "Fire Station",
                icon: getIconForType('fire_station') || undefined
              });
              currentFacilityMarkers.push(marker);
            }
          });
        }
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
        anchor: new google.maps.Point(16, 16)
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
