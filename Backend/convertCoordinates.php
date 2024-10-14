<?php
require 'vendor/autoload.php'; // Load proj4php library

use proj4php\Proj4php;
use proj4php\Proj;
use proj4php\Point;

// Step 1: Connect to the Azure SQL database
try {
    $conn = new PDO("sqlsrv:server = tcp:adaptive-network-management.database.windows.net,1433; Database = Adaptive_Netowork_Management", "CloudSA44398b14", "Adaptive2024");
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    echo "Successfully connected to SQL Server!\n";
} catch (PDOException $e) {
    die("Error connecting to SQL Server: " . $e->getMessage());
}

// Step 2: Add the new column 'coordinate' if it does not exist
try {
    $alterTableSQL = "ALTER TABLE PopulationDataGrid ADD coordinate VARCHAR(4000)";  // Add a new column to store converted MULTIPOLYGON format
    $conn->exec($alterTableSQL);
    echo "New column 'coordinate' added successfully.\n";
} catch (PDOException $e) {
    // Ignore the error if the column already exists
    echo "Column 'coordinate' might already exist or an error occurred: " . $e->getMessage() . "\n";
}

// Step 3: Initialize proj4php for coordinate conversion
$proj4 = new Proj4php();
$projNZGD2000 = new Proj('EPSG:2193', $proj4);  // Define the NZGD2000 coordinate system
$projWGS84 = new Proj('EPSG:4326', $proj4);     // Define the WGS84 coordinate system

// Step 4: Query all rows from the table to get WKT data
$query = "SELECT GridID, WKT FROM PopulationDataGrid";  // Use GridID as the identifier
$stmt = $conn->prepare($query);
$stmt->execute();
$results = $stmt->fetchAll(PDO::FETCH_ASSOC);

// Step 5: Process each row, convert WKT coordinates, and update the table
foreach ($results as $row) {
    $gridID = $row['GridID'];  // Use GridID as the identifier
    $wkt = $row['WKT'];

    // Skip rows with missing or invalid WKT values
    if (empty($wkt) || stripos($wkt, 'MULTIPOLYGON') === false) {
        echo "Missing or invalid WKT for GridID: $gridID, skipping.\n";
        continue;
    }

    // Step 6: Parse the MULTIPOLYGON to extract coordinate pairs
    preg_match_all('/\(\(\((.*?)\)\)\)/', $wkt, $matches);  // Match the MULTIPOLYGON coordinates
    if (empty($matches[1][0])) {
        echo "Invalid MULTIPOLYGON format for GridID: $gridID, skipping.\n";
        continue;
    }

    // Step 7: Extract each coordinate pair and convert them
    $polygonString = $matches[1][0];  // Extract the polygon coordinate string
    $points = explode(',', $polygonString);  // Split the coordinate pairs into an array
    $converted_coords = [];  // Store the converted coordinates

    foreach ($points as $point) {
        $coords = array_map('trim', explode(' ', $point));  // Split each point into x and y
        if (count($coords) < 2) {
            echo "Invalid coordinate pair for GridID: $gridID, skipping.\n";
            continue 2;  // Skip this row if the coordinate pair is invalid
        }
        
        list($x, $y) = $coords;

        // Convert using proj4php
        $pointSrc = new Point(floatval($x), floatval($y), $projNZGD2000);  // Create a point in NZGD2000
        $pointDest = $proj4->transform($projWGS84, $pointSrc);  // Convert to WGS84

        // Format the converted coordinates as "longitude latitude"
        $converted_coords[] = $pointDest->x . ' ' . $pointDest->y;  // Format as "longitude latitude"
    }

    // Step 8: Format the new MULTIPOLYGON string in WGS84
    $coordinateString = "MULTIPOLYGON (((" . implode(', ', $converted_coords) . ")))";

    // Update the table with the new 'coordinate' value
    $updateSQL = "UPDATE PopulationDataGrid SET coordinate = ? WHERE GridID = ?";
    $updateStmt = $conn->prepare($updateSQL);
    $updateStmt->execute([$coordinateString, $gridID]);

    echo "Updated GridID $gridID with new coordinate: $coordinateString\n";
}

echo "All WKT data has been successfully converted and updated in 'coordinate'.\n";
?>

