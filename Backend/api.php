<?php
// Step 1: Connect to the Azure SQL database
try {
    $conn = new PDO("sqlsrv:server = tcp:adaptive-network-management.database.windows.net,1433; Database = Adaptive_Netowork_Management", "CloudSA44398b14", "Adaptive2024");
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    echo "Successfully connected to SQL Server!\n";
} catch (PDOException $e) {
    die("Error connecting to SQL Server: " . $e->getMessage());
}

// Step 2: Define the SQL statement to drop the table
$tableName = 'PopulationDataGrid';  // Replace with your table name if different
$dropTableSQL = "DROP TABLE IF EXISTS $tableName";

try {
    // Step 3: Execute the SQL statement
    $conn->exec($dropTableSQL);
    echo "Table '$tableName' has been successfully deleted.\n";
} catch (PDOException $e) {
    die("Error deleting table '$tableName': " . $e->getMessage());
}
?>
