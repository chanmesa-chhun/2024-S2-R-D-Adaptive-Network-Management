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

// Read the CSV file
$csvFile = 'C:\Users\Jeremy\Documents\GitHub\2024-S2-R-D-Adaptive-Network-Management\2degrees data\ranKH.allcells_nw.csv'; // Path to the CSV file
if (!file_exists($csvFile)) {
    die("CSV file not found.");
}

if (($handle = fopen($csvFile, "r")) !== FALSE) {
    // Get the column names from the CSV file
    $headers = fgetcsv($handle, 1000, ",");

    // Build the CREATE TABLE statement
    $tableName = 'ranKH.allcells_nw';
    $columns = [];

    foreach ($headers as $header) {
        $columns[] = "$header VARCHAR(255)";
    }

    // SQL for creating the table
    $createTableSQL = "CREATE TABLE $tableName (" . implode(", ", $columns) . ")";
    
    try {
        // Execute the SQL to create the table
        $conn->exec($createTableSQL);
        echo "Table '$tableName' created successfully.\n";
    } catch (PDOException $e) {
        die("Error creating table: " . $e->getMessage());
    }

    // Generate the INSERT statement
    $sql = "INSERT INTO $tableName (" . implode(", ", $headers) . ") VALUES (" . rtrim(str_repeat("?, ", count($headers)), ", ") . ")";
    $stmt = $conn->prepare($sql);

    // Loop through the CSV file and insert data
    $conn->beginTransaction(); // Begin transaction
    $batchSize = 1000; // Number of rows to insert in a batch
    $rowCount = 0;

    while (($data = fgetcsv($handle, 1000, ",")) !== FALSE) {
        $stmt->execute($data);
        $rowCount++;

        // Commit every 1000 rows
        if ($rowCount % $batchSize == 0) {
            $conn->commit();
            $conn->beginTransaction();
        }
    }

    // Commit the last batch
    $conn->commit();
    fclose($handle);
    
    echo "Data successfully imported!";
} else {
    die("Error opening CSV file.");
}

?>