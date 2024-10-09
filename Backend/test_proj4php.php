<?php
// Array of table names to check
$tables = ['PopulationDataGrid', 'ranKH_SITES', 'OtherTableName'];

// Step 1: Connect to the Azure SQL database
try {
    $conn = new PDO("sqlsrv:server = tcp:adaptive-network-management.database.windows.net,1433; Database = Adaptive_Netowork_Management", "CloudSA44398b14", "Adaptive2024");
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    echo "Successfully connected to SQL Server!\n";
} catch (PDOException $e) {
    die("Error connecting to SQL Server: " . $e->getMessage());
}

// Step 2: Loop through each table and get the row count
foreach ($tables as $tableName) {
    $countSQL = "SELECT COUNT(*) AS row_count FROM $tableName";
    try {
        $stmt = $conn->query($countSQL);
        $result = $stmt->fetch(PDO::FETCH_ASSOC);
        $rowCount = $result['row_count'];
        echo "The table '$tableName' has $rowCount rows.\n";
    } catch (PDOException $e) {
        echo "Error executing count query on table '$tableName': " . $e->getMessage() . "\n";
    }
}
?>
