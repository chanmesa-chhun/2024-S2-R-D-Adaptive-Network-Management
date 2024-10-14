<?php
// Step 1: Connect to the Azure SQL database
try {
    $conn = new PDO("sqlsrv:server = tcp:adaptive-network-management.database.windows.net,1433; Database = Adaptive_Netowork_Management", "CloudSA44398b14", "Adaptive2024");
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    echo "Successfully connected to SQL Server!\n";
} catch (PDOException $e) {
    die("Error connecting to SQL Server: " . $e->getMessage());
}

// Step 2: Check if the 'Long_Lat' column already exists and add it if not
$checkColumnSQL = "
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'ranKH_allcells_nw' AND COLUMN_NAME = 'Long_Lat'
";
$columnExists = $conn->query($checkColumnSQL)->fetch();

if ($columnExists) {
    echo "Column 'Long_Lat' already exists. Skipping column creation.\n";
} else {
    try {
        $alterTableSQL = "ALTER TABLE ranKH_allcells_nw ADD Long_Lat VARCHAR(255)";  // Add a new column to store combined WGS84 coordinates
        $conn->exec($alterTableSQL);
        echo "New column 'Long_Lat' added successfully.\n";
    } catch (PDOException $e) {
        die("Failed to add 'Long_Lat' column: " . $e->getMessage() . "\n");
    }
}

// Step 3: Query all rows from ranKH_allcells_nw to get antlat and antlng
$query = "SELECT antlat, antlng FROM ranKH_allcells_nw";
$stmt = $conn->prepare($query);
$stmt->execute();
$results = $stmt->fetchAll(PDO::FETCH_ASSOC);

// Step 4: Process each row, combine antlat and antlng, and update the table
foreach ($results as $row) {
    $antlat = $row['antlat'];
    $antlng = $row['antlng'];

    // Skip rows with missing or invalid antlat/antlng values
    if (empty($antlat) || empty($antlng)) {
        echo "Missing antlat or antlng for a record, skipping.\n";
        continue;
    }

    // Step 5: Combine antlat and antlng into "latitude longitude" format
    $longLatString = $antlat . ' ' . $antlng;  // Format as "latitude longitude"

    // Step 6: Update the table with the new 'Long_Lat' value
    $updateSQL = "UPDATE ranKH_allcells_nw SET Long_Lat = ? WHERE antlat = ? AND antlng = ?";
    $updateStmt = $conn->prepare($updateSQL);
    $updateStmt->execute([$longLatString, $antlat, $antlng]);

    echo "Updated record with new Long_Lat: $longLatString\n";
}

echo "All antlat and antlng data has been successfully combined and updated in 'Long_Lat'.\n";
?>
