<?php
try {
    $conn = new PDO("sqlsrv:server = tcp:adaptive-network-management.database.windows.net,1433; Database = Adaptive_Netowork_Management", "CloudSA44398b14", "Adaptive2024");
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    echo "Successfully connected to SQL Server!<br>";
    
    $createTableSQL = "
        IF OBJECT_ID('Auckland_PopulationData', 'U') IS NOT NULL
        DROP TABLE Auckland_PopulationData;

        CREATE TABLE Auckland_PopulationData (
            [WKT] VARCHAR(255) NOT NULL,
            [GridID] VARCHAR(20) NOT NULL,
            [ERP_2022] FLOAT(53) NULL,
            [x_y] VARCHAR(255) NULL,
            [coordinate] VARCHAR(4000) NULL,
            [geo_location] geography NULL
        );

        INSERT INTO Auckland_PopulationData ([WKT],[GridID], [ERP_2022], [x_y], [coordinate], [geo_location])
        SELECT [WKT], [GridID], [ERP_2022], [x_y], [coordinate], [geo_location]
        FROM PopulationDataGrid
        WHERE 
            TRY_CAST(SUBSTRING([x_y], 1, CHARINDEX(',', [x_y]) - 1) AS FLOAT) BETWEEN -37.1 AND -36.6  -- Latitude
            AND TRY_CAST(SUBSTRING([x_y], CHARINDEX(',', [x_y]) + 1, LEN([x_y])) AS FLOAT) BETWEEN 174.5 AND 175.5; -- Longitude
    ";

    $stmt = $conn->prepare($createTableSQL);
    $stmt->execute();

    echo "Table Auckland_PopulationData created and populated successfully.";
}
catch (PDOException $e) {
    echo "Error connecting to SQL Server: " . $e->getMessage();
}
?>
