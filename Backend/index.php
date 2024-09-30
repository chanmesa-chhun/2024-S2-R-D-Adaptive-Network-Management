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
$csvFile = 'C:\Users\Jeremy\Documents\GitHub\2024-S2-R-D-Adaptive-Network-Management\2degrees data\ranKH.SITES.csv';
if (!file_exists($csvFile)) {
    die("CSV file not found.");
}

// Define columns and data types for ranKH_SITES table
$columns = [
    'NAME VARCHAR(255)',
    'LONGITUDE FLOAT',
    'LATITUDE FLOAT',
    'ALTITUDE FLOAT',
    'COMMENT_ VARCHAR(255)',
    'PYLON_HEIGHT FLOAT',
    'SUPPORT_INFO VARCHAR(255)',
    'CHANNEL_ELEMENTS_UL INT',
    'CHANNEL_ELEMENTS_DL INT',
    'MAX_IUB_RATE_UL FLOAT',
    'MAX_IUB_RATE_DL FLOAT',
    'CDMA_EQUIPMENT VARCHAR(255)',
    'EVDO_CES VARCHAR(255)',
    'BH_CAPACITY_DL FLOAT',
    'BH_CAPACITY_UL FLOAT',
    'STATUS VARCHAR(255)',
    'TIER VARCHAR(255)',
    'SITENAME VARCHAR(255)',
    'OPERATOR VARCHAR(255)',
    'NAMELINK VARCHAR(255)',
    'COUNCIL VARCHAR(255)',
    'PROPERTY_TYPE VARCHAR(255)',
    'RF_RANK VARCHAR(255)',
    'PROGRESS VARCHAR(255)',
    'STRUCTURE_TYPE VARCHAR(255)',
    'SITE_TYPE VARCHAR(255)',
    'TARGET_ON_AIR VARCHAR(255)',
    'CABINET_LAYOUT VARCHAR(255)',
    'CO_STATUS VARCHAR(255)',
    'SPATIAL_REGION VARCHAR(255)',
    'ONAIR VARCHAR(255)',
    'L07_ONAIR VARCHAR(255)',
    'L18_ONAIR VARCHAR(255)',
    'L09_ONAIR VARCHAR(255)',
    'L21_ONAIR VARCHAR(255)',
    'DB_RECORD_ID VARCHAR(255)',
    'HISTORY_ID VARCHAR(255)',
    'MODIFIED_BY VARCHAR(255)',
    'MODIFIED_DATE DATETIME',
    'HISTORY_STATUS VARCHAR(255)',
    'N35_ONAIR VARCHAR(255)'
];

// Define the table name
$tableName = '"ranKH_SITES"';

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
    
    echo "Data successfully imported!";
} else {
    die("Error opening CSV file.");
}

// // Read the CSV file
// $csvFile = 'C:\Users\Jeremy\Documents\GitHub\2024-S2-R-D-Adaptive-Network-Management\2degrees data\ranKH.allcells_nw.csv';
// if (!file_exists($csvFile)) {
//     die("CSV file not found.");
// }

// // Define columns and data types
// $columns = [
//     'id INT',
//     'rat VARCHAR(255)',
//     'sitename VARCHAR(255)',
//     'sitecode VARCHAR(255)',
//     'anteast INT',
//     'antnorth INT',
//     'antlat FLOAT', 
//     'antlng FLOAT', 
//     'txid VARCHAR(255)',
//     'nename VARCHAR(255)',
//     'flacode VARCHAR(255)',
//     'nodeid VARCHAR(255)',
//     'sec INT',
//     'cellid VARCHAR(255)',
//     'localcellid VARCHAR(255)',
//     'cellname VARCHAR(255)',
//     'cgi VARCHAR(255)',
//     'cellradius VARCHAR(255)',
//     'preamblefmt VARCHAR(255)',
//     'dlarfcn VARCHAR(255)',
//     'dlcellbw VARCHAR(255)',
//     '[identity] VARCHAR(255)',
//     'rootseq VARCHAR(255)',
//     'tac VARCHAR(255)',
//     'rac VARCHAR(255)',
//     'pwr VARCHAR(255)',
//     'txrxmode VARCHAR(255)',
//     'antenna VARCHAR(255)',
//     'azimuth INT',
//     'height FLOAT', 
//     'etilt FLOAT',  
//     'mtilt FLOAT',  
//     'vendor VARCHAR(255)',
//     'operator VARCHAR(255)',
//     'beamwidth VARCHAR(255)',
//     'gain VARCHAR(255)'
// ];

// // Define table name (ensure the use of schema and table correctly)
// $tableName = '[ranKH_allcells_nw]';  // Correct SQL Server schema syntax

// // Check if the table exists
// $tableExistsQuery = "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'ranKH_allcells_nw'";
// $tableExists = $conn->query($tableExistsQuery)->fetchColumn();

// if (!$tableExists) {
//     // If the table does not exist, create the table
//     $createTableSQL = "CREATE TABLE $tableName (" . implode(", ", $columns) . ")";
    
//     try {
//         $conn->exec($createTableSQL);
//         echo "Table '$tableName' created successfully.\n";
//     } catch (PDOException $e) {
//         die("Error creating table: " . $e->getMessage());
//     }
// } else {
//     echo "Table '$tableName' already exists.\n";
// }

// // Prepare the SQL for data insertion
// $sql = "INSERT INTO $tableName (" . implode(", ", array_map(fn($col) => explode(' ', $col)[0], $columns)) . ") VALUES (" . rtrim(str_repeat("?, ", count($columns)), ", ") . ")";
// $stmt = $conn->prepare($sql);

// // Read and insert data from the CSV file
// if (($handle = fopen($csvFile, "r")) !== FALSE) {
//     // Skip the header row
//     fgetcsv($handle, 1000, ",");

//     // Start transaction
//     $conn->beginTransaction();
//     $batchSize = 1000; // Number of rows per batch
//     $rowCount = 0;

//     while (($data = fgetcsv($handle, 1000, ",")) !== FALSE) {
//         // Make sure the data matches the number of columns
//         if (count($data) == count($columns)) {
//             $stmt->execute($data);
//             $rowCount++;
//         }

//         // Commit every 1000 rows
//         if ($rowCount % $batchSize == 0) {
//             $conn->commit();
//             $conn->beginTransaction();
//         }
//     }

//     // Commit the final batch
//     $conn->commit();
//     fclose($handle);
    
//     echo "Data successfully imported!";
// } else {
//     die("Error opening CSV file.");
// }

// if (($handle = fopen($csvFile, "r")) !== FALSE) {
//     // Get the column names from the CSV file
//     $headers = fgetcsv($handle, 1000, ",");

//     // Build the CREATE TABLE statement
//     $tableName = 'ranKH.allcells_nw';
//     $columns = [];

//     foreach ($headers as $header) {
//         $columns[] = "$header VARCHAR(255)";
//     }

//     // SQL for creating the table
//     $createTableSQL = "CREATE TABLE $tableName (" . implode(", ", $columns) . ")";
    
//     try {
//         // Execute the SQL to create the table
//         $conn->exec($createTableSQL);
//         echo "Table '$tableName' created successfully.\n";
//     } catch (PDOException $e) {
//         die("Error creating table: " . $e->getMessage());
//     }

//     // Generate the INSERT statement
//     $sql = "INSERT INTO $tableName (" . implode(", ", $headers) . ") VALUES (" . rtrim(str_repeat("?, ", count($headers)), ", ") . ")";
//     $stmt = $conn->prepare($sql);

//     // Loop through the CSV file and insert data
//     $conn->beginTransaction(); // Begin transaction
//     $batchSize = 1000; // Number of rows to insert in a batch
//     $rowCount = 0;

//     while (($data = fgetcsv($handle, 1000, ",")) !== FALSE) {
//         $stmt->execute($data);
//         $rowCount++;

//         // Commit every 1000 rows
//         if ($rowCount % $batchSize == 0) {
//             $conn->commit();
//             $conn->beginTransaction();
//         }
//     }

//     // Commit the last batch
//     $conn->commit();
//     fclose($handle);
    
//     echo "Data successfully imported!";
// } else {
//     die("Error opening CSV file.");
// }

?>