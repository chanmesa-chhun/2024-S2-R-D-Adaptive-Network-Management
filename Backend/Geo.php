<?php
// try {
//     $conn = new PDO("sqlsrv:server = tcp:adaptive-network-management.database.windows.net,1433; Database = Adaptive_Netowork_Management", "CloudSA44398b14", "Adaptive2024");
//     $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
//     echo "Successfully connected to SQL Server!\n";

//     // Step 1.1: Add GEOGRAPHY column to PopulationDataGrid
//     $alterTableSQL = "ALTER TABLE PopulationDataGrid ADD geo_location GEOGRAPHY";
//     $conn->exec($alterTableSQL);
//     echo "GEOGRAPHY column 'geo_location' added to PopulationDataGrid.\n";
    
// } catch (PDOException $e) {
//     die("Error: " . $e->getMessage());
// }

// try {
//     // Step 1.2: Convert WGS84 coordinates in the 'coordinate' column to GEOGRAPHY type
//     $updateSQL = "UPDATE PopulationDataGrid SET geo_location = GEOGRAPHY::STGeomFromText(coordinate, 4326)";
//     $conn->exec($updateSQL);
//     echo "PopulationDataGrid coordinates successfully converted to GEOGRAPHY.\n";
    
// } catch (PDOException $e) {
//     die("Error converting coordinates: " . $e->getMessage());
// }

try {
    $conn = new PDO("sqlsrv:server = tcp:adaptive-network-management.database.windows.net,1433; Database = Adaptive_Netowork_Management", "CloudSA44398b14", "Adaptive2024");
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    echo "Successfully connected to SQL Server!\n";

    // Step 2.1: Add GEOGRAPHY column to ranKH_allcells_nw
    // $alterTableSQL = "ALTER TABLE ranKH_allcells_nw ADD geo_location GEOGRAPHY";
    // $conn->exec($alterTableSQL);
    // echo "GEOGRAPHY column 'geo_location' added to ranKH_allcells_nw.\n";

 // Step 2.2: Query all rows to process Long_Lat data
 $query = "SELECT id, Long_Lat FROM ranKH_allcells_nw";
 $stmt = $conn->prepare($query);
 $stmt->execute();
 $results = $stmt->fetchAll(PDO::FETCH_ASSOC);

 foreach ($results as $row) {
     $id = $row['id'];
     $longLat = $row['Long_Lat'];

     // Split the Long_Lat string into latitude and longitude
     list($lat, $lng) = explode(' ', $longLat);

     // Convert latitude and longitude to floats and check if they're within valid ranges
     $lat = floatval($lat);
     $lng = floatval($lng);

     if ($lat < -90 || $lat > 90 || $lng < -180 || $lng > 180) {
         echo "Invalid Long_Lat for id: $id (latitude: $lat, longitude: $lng), skipping.\n";
         continue;  // Skip invalid data
     }

     // Swap latitude and longitude for correct GEOGRAPHY format
     // Use POINT(经度 纬度)
     $updateSQL = "UPDATE ranKH_allcells_nw SET geo_location = GEOGRAPHY::STPointFromText('POINT($lng $lat)', 4326) WHERE id = ?";
     $updateStmt = $conn->prepare($updateSQL);
     $updateStmt->execute([$id]);

     echo "Updated id $id with valid GEOGRAPHY coordinates.\n";
 }

} catch (PDOException $e) {
 die("Error converting coordinates: " . $e->getMessage());
}

