<?php
// PHP Data Objects(PDO) Sample Code:
try {
    $conn = new PDO("sqlsrv:server = tcp:adaptive-network-management.database.windows.net,1433; Database = Adaptive_Netowork_Management", "CloudSA44398b14", "Adaptive2024");
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    // If the connection is successful
    echo "Successfully connected to SQL Server!";
}
catch (PDOException $e) {
    print("Error connecting to SQL Server.");
    die(print_r($e));
}

// Read the CSV file (update the path to your actual CSV file)
$csvFile = 'C:\Users\Jeremy\Documents\GitHub\2024-S2-R-D-Adaptive-Network-Management\Population data\PopulationDataGrid.csv';
if (!file_exists($csvFile)) {
    die("CSV file not found.");
}

// Define columns and data types for PopulationDataGrid table
$columns = [
    'WKT VARCHAR(255)',           // Well-Known Text for geometry representation
    'CENTROID_X FLOAT',           // X coordinate of the centroid
    'CENTROID_Y FLOAT',           // Y coordinate of the centroid
    'GridID VARCHAR(20)',         // Unique identifier for each grid cell
    'ERP_2022 FLOAT',             // Estimated Resident Population for 2022
    'Shape_Length FLOAT'          // Length of the boundary shape
];

// Define the table name
$tableName = '"PopulationDataGrid"';

// Create the table if it doesn't exist
try {
    $createTableSQL = "CREATE TABLE $tableName (" . implode(", ", $columns) . ")";
    $conn->exec($createTableSQL);
    echo "Table '$tableName' created successfully.\n";
} catch (PDOException $e) {
    die("Error creating table: " . $e->getMessage());
}

// Prepare the SQL for data insertion
$sql = "INSERT INTO $tableName (" . implode(", ", array_map(fn($col) => explode(' ', $col)[0], $columns)) . ") VALUES (" . rtrim(str_repeat("?, ", count($columns)), ", ") . ")";
$stmt = $conn->prepare($sql);

// Read and insert data from the CSV file
if (($handle = fopen($csvFile, "r")) !== FALSE) {
    // Skip the header row
    fgetcsv($handle, 1000, ",");

    // Start transaction
    $conn->beginTransaction();
    $batchSize = 1000; // Number of rows per batch
    $rowCount = 0;

    while (($data = fgetcsv($handle, 1000, ",")) !== FALSE) {
        // Make sure the data matches the number of columns
        if (count($data) == count($columns)) {
            $stmt->execute($data);
            $rowCount++;
        }

        // Commit every 1000 rows
        if ($rowCount % $batchSize == 0) {
            $conn->commit();
            $conn->beginTransaction();
        }
    }

    // Commit the final batch
    $conn->commit();
    fclose($handle);
    
    echo "Data successfully imported into '$tableName'!";
} else {
    die("Error opening CSV file.");
}
?>
