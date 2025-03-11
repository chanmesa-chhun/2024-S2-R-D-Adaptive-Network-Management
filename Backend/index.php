<!DOCTYPE html>
<html>
<head>
  <title>Google Map with CSV Markers & Emergency Services</title>
  <link rel="stylesheet" type="text/css" href="styles.css">
  <!-- Include the Google Maps JavaScript API with Places and Geometry libraries -->
  <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyAlRJJEG94C4gjwn8sqJN0BbDpOUL2jrNs&libraries=places,geometry"></script>
  <script>
    let map; // Global map variable
    let cellTowerMarkers = []; // Array to store cell tower markers
    let circles = []; // Array to store global circles (for "Show All" if needed)
    let currentCircle = null; // Global variable for the currently displayed circle
    let currentFacilityMarkers = []; // Array to store facility markers for the selected tower

    function initMap() {
      // Choose a default center (Auckland CBD)
      const center = { lat: -36.8485, lng: 174.7633 };

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

      // Create a Places Service instance for emergency services
      const service = new google.maps.places.PlacesService(map);

      // Fetch marker data from markers.php (cell towers)
      fetch('markers.php')
        .then(response => response.json())
        .then(data => {
          const tableBody = document.getElementById('tower-body');

          data.forEach(markerData => {
            // Create a marker for each cell tower using your CSV data
            const marker = new google.maps.Marker({
              position: { lat: markerData.lat, lng: markerData.lng },
              map: map,
              title: markerData.sitename,
              icon: {
                url: 'celltower_icon3.png',
                scaledSize: new google.maps.Size(32, 32),
                anchor: new google.maps.Point(16, 32)
              }
            });
            cellTowerMarkers.push(marker);

            // Create a table row for the cell tower info
            const row = document.createElement('tr');

            // Site Name cell
            const nameCell = document.createElement('td');
            nameCell.textContent = markerData.sitename;
            row.appendChild(nameCell);

            // Coordinates cell
            const coordCell = document.createElement('td');
            coordCell.textContent = `(${markerData.lat}, ${markerData.lng})`;
            row.appendChild(coordCell);

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

            // Set default dataset values for sorting (if needed)
            row.dataset.hospital = 0;
            row.dataset.police = 0;
            row.dataset.fire = 0;
            row.dataset.towers = 0;

            // When the row is clicked:
            row.addEventListener('click', () => {
              // Recenter and zoom the map
              map.setCenter(marker.getPosition());
              map.setZoom(12);

              // Clear any previously drawn circle and facility markers
              if (currentCircle) {
                currentCircle.setMap(null);
              }
              clearFacilityMarkers();

              // Draw a 5 km circle for this tower
              currentCircle = new google.maps.Circle({
                map: map,
                center: marker.getPosition(),
                radius: 5000, // 5 km in meters
                fillColor: '#FF0000',
                fillOpacity: 0.1,
                strokeColor: '#FF0000',
                strokeOpacity: 0.8,
                strokeWeight: 2
              });

              // Display facility markers around this tower
              showFacilitiesForTower(marker.getPosition(), service);
            });

            tableBody.appendChild(row);

            // For each emergency type, perform a nearby search and update its cell and dataset
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

            // Compute the number of other cell towers within 5 km using your own CSV data
            const currentLatLng = new google.maps.LatLng(markerData.lat, markerData.lng);
            let nearbyTowerCount = 0;
            data.forEach(other => {
              // Skip the same tower
              if (markerData.lat === other.lat && markerData.lng === other.lng) return;
              const otherLatLng = new google.maps.LatLng(other.lat, other.lng);
              const distance = google.maps.geometry.spherical.computeDistanceBetween(currentLatLng, otherLatLng);
              if (distance <= 5000) {
                nearbyTowerCount++;
              }
            });
            towersCell.textContent = nearbyTowerCount;
            row.dataset.towers = nearbyTowerCount;
          });
        })
        .catch(error => console.error('Error loading markers:', error));
    }

    // Helper function to search for a specific emergency service type around a location
    function searchEmergencyServicesForTowerType(location, type, service) {
      return new Promise(resolve => {
        const request = {
          location: location,
          radius: '5000', // 5 km radius
          type: type
        };
        service.nearbySearch(request, (results, status) => {
          if (status === google.maps.places.PlacesServiceStatus.OK && results) {
            resolve(results);
          } else {
            resolve([]); // Return an empty array if search fails
          }
        });
      });
    }

    // Function to clear facility markers currently shown on the map
    function clearFacilityMarkers() {
      if (currentFacilityMarkers.length) {
        currentFacilityMarkers.forEach(marker => {
          marker.setMap(null);
        });
        currentFacilityMarkers = [];
      }
    }

    function getIconForType(type) {
      let iconUrl = null;
      if (type === 'hospital') iconUrl = 'hospital_icon.png';
      else if (type === 'police') iconUrl = 'police_station_icon.png';
      else if (type === 'fire_station') iconUrl = 'firestaion_icon.png';

      // If there's no matching URL, return null (default marker).
      if (!iconUrl) return null;

      return {
        url: iconUrl,
        // Scale down to 16x16, half the size of a 32x32 tower icon
        scaledSize: new google.maps.Size(32, 32),
        // Anchor the icon so its bottom is at the marker's position
        anchor: new google.maps.Point(8, 16)
      };
    }

    // Function to display facility markers around a given location
    function showFacilitiesForTower(location, service) {
      const emergencyTypes = ['hospital', 'police', 'fire_station'];
      emergencyTypes.forEach(type => {
        const request = {
          location: location,
          radius: '5000', // 5 km
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

    // Function to show a 5km circle around all cell towers (for global toggle)
    function showCircles() {
      hideCircles();  // Clear any existing circles and facility markers
      cellTowerMarkers.forEach(marker => {
        const circle = new google.maps.Circle({
          map: map,
          center: marker.getPosition(),
          radius: 5000, // 5 km in meters
          fillColor: '#FF0000',
          fillOpacity: 0.05,
          strokeColor: '#FF0000',
          strokeOpacity: 0.8,
          strokeWeight: 2
        });
        circles.push(circle);
      });
    }

    // Function to hide all circles and facility markers
    function hideCircles() {
      circles.forEach(circle => {
        circle.setMap(null);
      });
      circles = [];
      if (currentCircle) {
        currentCircle.setMap(null);
        currentCircle = null;
      }
      clearFacilityMarkers();
    }

    // Function to sort the table rows based on the selected priority facility
    function sortTable() {
      const select = document.getElementById("priority-select");
      const priority = select.value; // "hospital", "police", "fire", or "towers"
      if (!priority) return; // No sorting if no priority is selected

      const tableBody = document.getElementById("tower-body");
      const rowsArray = Array.from(tableBody.getElementsByTagName("tr"));

      // Sort rows based on the dataset value for the selected facility (in descending order)
      rowsArray.sort((a, b) => {
        const countA = parseInt(a.dataset[priority]) || 0;
        const countB = parseInt(b.dataset[priority]) || 0;
        return countB - countA;
      });

      // Clear current rows and re-append sorted rows
      tableBody.innerHTML = "";
      rowsArray.forEach(row => {
        tableBody.appendChild(row);
      });
    }

    // Initialize the map when the window loads
    window.onload = initMap;
  </script>
</head>
<body>
  <h1 style="text-align: center;">Map of Cell Towers & Emergency Services</h1>
  <div id="map" style="width:100%; height:500px;"></div>
  
  <!-- Buttons to toggle 5km circles (global view) -->
  <div style="text-align: center; margin: 10px;">
    <button onclick="showCircles()">Show 5km Area Around All Cell Towers</button>
    <button onclick="hideCircles()">Hide 5km Areas</button>
  </div>

  <!-- Drop-down box to choose priority facility for sorting -->
  <div style="text-align: center; margin: 10px;">
    <label for="priority-select">Prioritize by:</label>
    <select id="priority-select" onchange="sortTable()">
      <option value="">Select Priority</option>
      <option value="hospital">Hospital/Clinic</option>
      <option value="police">Police Station</option>
      <option value="fire">Fire Station</option>
      <option value="towers">Nearby Towers</option>
    </select>
  </div>

  <h2>Cell Tower List</h2>
  <!-- Table for cell tower data -->
  <table>
    <thead>
      <tr>
        <th>Site Name</th>
        <th>Coordinates</th>
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