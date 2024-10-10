<?php
include 'Function.php';

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

if (isset($argv[1])) { // Use "php Server.php columnName" to use the column
    $columnName = $argv[1];
    $data = getDataByColumn($columnName);
    print_r($data); // Display the data from the specified column
}
