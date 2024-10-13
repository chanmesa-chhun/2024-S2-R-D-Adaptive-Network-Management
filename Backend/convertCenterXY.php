<?php
require 'vendor/autoload.php'; // Load the proj4php library

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

// Step 2: Add the new column 'x_y' if it does not exist
try {
    $alterTableSQL = "ALTER TABLE PopulationDataGrid ADD x_y VARCHAR(255)";  // Add a new column to store latitude and longitude
    $conn->exec($alterTableSQL);
    echo "New column 'x_y' added successfully.\n";
} catch (PDOException $e) {
    // Ignore the error if the column already exists
    echo "Column 'x_y' might already exist or an error occurred: " . $e->getMessage() . "\n";
}

// Step 3: Initialize proj4php for coordinate conversion
$proj4 = new Proj4php();
$projNZGD2000 = new Proj('EPSG:2193', $proj4);  // Define the NZGD2000 coordinate system
$projWGS84 = new Proj('EPSG:4326', $proj4);     // Define the WGS84 coordinate system

// Step 4: Query all rows from the table to get CENTROID_X and CENTROID_Y
$query = "SELECT GridID, CENTROID_X, CENTROID_Y FROM PopulationDataGrid";  // Use GridID as the unique identifier
$stmt = $conn->prepare($query);
$stmt->execute();
$results = $stmt->fetchAll(PDO::FETCH_ASSOC);

// Step 5: Process each row, convert coordinates, and update the table
foreach ($results as $row) {
    $gridID = $row['GridID'];  // Use GridID as the identifier
    $centroidX = $row['CENTROID_X'];
    $centroidY = $row['CENTROID_Y'];

    // Skip rows with missing or invalid coordinates
    if (empty($centroidX) || empty($centroidY)) {
        echo "Missing CENTROID_X or CENTROID_Y for GridID: $gridID, skipping.\n";
        continue;
    }

    // Convert the centroid coordinates from NZGD2000 to WGS84
    $pointSrc = new Point(floatval($centroidX), floatval($centroidY), $projNZGD2000);  // Create a point in NZGD2000
    $pointDest = $proj4->transform($projWGS84, $pointSrc);  // Transform to WGS84

    // Format the result as "latitude, longitude"
    $x_y_string = $pointDest->y . ', ' . $pointDest->x;  // Format as "latitude, longitude"

    // Update the table with the new x_y value
    $updateSQL = "UPDATE PopulationDataGrid SET x_y = ? WHERE GridID = ?";
    $updateStmt = $conn->prepare($updateSQL);
    $updateStmt->execute([$x_y_string, $gridID]);

    echo "Updated GridID $gridID with new x_y coordinates: $x_y_string\n";
}

echo "All centroid coordinates have been successfully converted and updated in 'x_y'.\n";
?>
