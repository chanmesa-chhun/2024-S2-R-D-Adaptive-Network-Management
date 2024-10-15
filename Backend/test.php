<?php
ini_set('memory_limit', '512M');

try {
    $conn = new PDO("sqlsrv:server = tcp:adaptive-network-management.database.windows.net,1433; Database = Adaptive_Netowork_Management", "CloudSA44398b14", "Adaptive2024");
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    echo "Successfully connected to SQL Server!\n";

// 查询特定的 cell tower 并调试其 5 公里范围内的网格
$query = "
    SELECT t.id, t.Long_Lat, p.GridID, p.ERP_2022, 
           t.geo_location.STBuffer(5000).ToString() AS buffer_wkt,  -- 输出 buffer 区域
           p.geo_location.ToString() AS grid_location, 
           t.geo_location.STBuffer(5000).STIntersects(p.geo_location) AS intersects  -- 更改 STIntersects 使用顺序
    FROM ranKH_allcells_nw t
    JOIN PopulationDataGrid p
    ON t.geo_location.STBuffer(5000).STIntersects(p.geo_location) = 1  -- 更改 STIntersects 的顺序
    WHERE t.id = 881  -- 选择 ID 为 881 的 cell tower
";

$stmt = $conn->prepare($query);
$stmt->execute();
$results = $stmt->fetchAll(PDO::FETCH_ASSOC);

// 输出调试信息
if (!empty($results)) {
    foreach ($results as $row) {
        echo "Cell Tower ID: " . $row['id'] . "\n";
        echo "Cell Tower Location (Lat, Long): " . $row['Long_Lat'] . "\n";
        echo "Buffer (5km) WKT: " . $row['buffer_wkt'] . "\n";
        echo "Grid ID: " . $row['GridID'] . "\n";
        echo "Grid Location (WKT): " . $row['grid_location'] . "\n";
        echo "Intersects: " . ($row['intersects'] ? "Yes" : "No") . "\n";
        echo "Population in this Grid: " . $row['ERP_2022'] . "\n";
        echo "---------------------------------------------\n";
    }
} else {
    echo "No intersecting grids found for the selected cell tower.\n";
}

} catch (PDOException $e) {
    die("Error calculating population coverage: " . $e->getMessage());
}
?>
