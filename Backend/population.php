<?php
try {
    // Step 1: Connect to the Azure SQL database
    $conn = new PDO("sqlsrv:server = tcp:adaptive-network-management.database.windows.net,1433; Database = Adaptive_Netowork_Management", "CloudSA44398b14", "Adaptive2024");
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    echo "Successfully connected to SQL Server!\n";
    
    // Step 2: Query to calculate population coverage for each cell tower
    $offset = 0;
    $limit = 50; // Process 50 towers at a time to avoid memory exhaustion
    $total_population_coverage = [];
    
    while (true) {
        // Fetch a batch of cell towers
        $query = "
            SELECT t.id, t.Long_Lat, SUM(p.ERP_2022) AS total_population
            FROM ranKH_allcells_nw t
            JOIN PopulationDataGrid p
            ON t.geo_location.STBuffer(5000).STIntersects(p.geo_location) = 1
            GROUP BY t.id, t.Long_Lat
            ORDER BY total_population DESC
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
        ";
        
        $stmt = $conn->prepare($query);
        $stmt->bindValue(':offset', $offset, PDO::PARAM_INT);
        $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
        $stmt->execute();
        $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        if (empty($results)) {
            break; // No more results, stop the loop
        }
        
        // Store the results in the array
        foreach ($results as $row) {
            $total_population_coverage[] = [
                'id' => $row['id'],
                'Long_Lat' => $row['Long_Lat'],
                'total_population' => $row['total_population']
            ];
        }
        
        // Increment the offset for the next batch
        $offset += $limit;
        
        // Debugging output to track progress
        echo "Processed $offset towers so far...\n";
    }
    
    // Step 3: Sort the result based on total population in descending order
    usort($total_population_coverage, function ($a, $b) {
        return $b['total_population'] <=> $a['total_population'];
    });

    // Step 4: Output the sorted results
    foreach ($total_population_coverage as $tower) {
        echo "Cell Tower ID: " . $tower['id'] . "\n";
        echo "Cell Tower Location (Lat, Long): " . $tower['Long_Lat'] . "\n";
        echo "Total Population Covered: " . $tower['total_population'] . "\n";
        echo "---------------------------------------------\n";
    }

} catch (PDOException $e) {
    die("Error calculating population coverage: " . $e->getMessage());
}
?>
