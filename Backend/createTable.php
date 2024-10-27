<?php
try {
    $conn = new PDO("sqlsrv:server = tcp:adaptive-network-management.database.windows.net,1433; Database = Adaptive_Netowork_Management", "CloudSA44398b14", "Adaptive2024");
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    echo "Successfully connected to SQL Server!<br>";
    
    $addGeoLocationColumnSQL = "
        IF NOT EXISTS (SELECT * FROM sys.columns 
                       WHERE name = 'geo_location' AND object_id = OBJECT_ID('prototype1_tower'))
        BEGIN
            ALTER TABLE prototype1_tower ADD geo_location geography;
        END
    ";
    
    $stmt = $conn->prepare($addGeoLocationColumnSQL);
    $stmt->execute();
    echo "geo_location column created successfully!<br>";

    $updateGeoLocationSQL = "
        UPDATE prototype1_tower
        SET geo_location = geography::Point(latitude, longitude, 4326)
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
    ";

    $stmt = $conn->prepare($updateGeoLocationSQL);
    $stmt->execute();

    echo "geo_location column updated successfully for prototype1_tower.";
}
catch (PDOException $e) {
    echo "Error connecting to SQL Server: " . $e->getMessage();
}
?>

<!-- 
// Database connection
try {
    $conn = new PDO("sqlsrv:server = tcp:adaptive-network-management.database.windows.net,1433; Database = Adaptive_Netowork_Management", "CloudSA44398b14", "Adaptive2024");
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    echo "Successfully connected to SQL Server!<br>";

    // Create table if not exists
    $createTableQuery = "
    CREATE TABLE prototype1_tower (
        TowerID INT PRIMARY KEY,
        TowerName VARCHAR(255),
        Latitude FLOAT,
        Longitude FLOAT,
        CoverageRadius FLOAT,
        PopulationCovered FLOAT
    );
    ";
    $conn->exec($createTableQuery);
    echo "Table prototype1_tower created successfully.<br>";

    // Full path to the CSV file
    $csvFile = 'C:/Users/Jeremy/Documents/GitHub/2024-S2-R-D-Adaptive-Network-Management/2degrees data/prototype1_cell_towers.csv';
    
    // Open the CSV file
    if (($handle = fopen($csvFile, "r")) !== FALSE) {
        // Skip the header row
        fgetcsv($handle);

        // Prepare insert statement
        $insertQuery = $conn->prepare("
        INSERT INTO prototype1_tower (TowerID, TowerName, Latitude, Longitude, CoverageRadius, PopulationCovered)
        VALUES (:TowerID, :TowerName, :Latitude, :Longitude, :CoverageRadius, :PopulationCovered)
        ");

        // Read through the CSV file and insert each row into the database
        while (($data = fgetcsv($handle, 1000, ",")) !== FALSE) {
            $insertQuery->bindParam(':TowerID', $data[0], PDO::PARAM_INT);
            $insertQuery->bindParam(':TowerName', $data[1]);
            $insertQuery->bindParam(':Latitude', $data[2], PDO::PARAM_STR);
            $insertQuery->bindParam(':Longitude', $data[3], PDO::PARAM_STR);
            $insertQuery->bindParam(':CoverageRadius', $data[4], PDO::PARAM_STR);
            $insertQuery->bindParam(':PopulationCovered', $data[5], PDO::PARAM_STR);
            $insertQuery->execute();
        }
        fclose($handle);
        echo "Data imported successfully.";
    } else {
        echo "Error opening the CSV file.";
    }

} catch (PDOException $e) {
    echo "Error: " . $e->getMessage();
}
 -->
