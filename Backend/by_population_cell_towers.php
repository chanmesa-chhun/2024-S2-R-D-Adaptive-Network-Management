<?php

ini_set('memory_limit', '512M');

// Load the cell tower data from the uploaded CSV file
$cellTowersPath = 'C:\Users\mesac\Downloads\Code\Code\AUT\cell_towers_with_utm.csv';
$cellTowers = [];
if (($handle = fopen($cellTowersPath, 'r')) !== FALSE) {
    $headers = fgetcsv($handle, 1000, ',');
    while (($data = fgetcsv($handle, 1000, ',')) !== FALSE) {
        $cellTowers[] = array_combine($headers, $data);
    }
    fclose($handle);
}

// Convert WGS84 (lat, lng) to UTM
function convertToUTM($lat, $lng) {
    // For simplicity, we use a placeholder. We can use an appropriate UTM conversion library here.
    return ['easting' => $lat * 1000, 'northing' => $lng * 1000];
}

// Add UTM coordinates to cell towers
foreach ($cellTowers as &$tower) {
    if (isset($tower['antlat']) && isset($tower['antlng']) && is_numeric($tower['antlat']) && is_numeric($tower['antlng'])) {
        $utmCoords = convertToUTM($tower['antlat'], $tower['antlng']);
        $tower['utm_easting'] = $utmCoords['easting'];
        $tower['utm_northing'] = $utmCoords['northing'];
    } else {
        $tower['utm_easting'] = null;
        $tower['utm_northing'] = null;
    }
}

/*
// Save updated cell tower data to CSV
$updatedFilePath = 'C:\Users\mesac\Downloads\Code\Code\AUT\cell_towers_with_utm.csv';
if (($handle = fopen($updatedFilePath, 'w')) !== FALSE) {
    fputcsv($handle, array_keys($cellTowers[0])); // Insert headers
    foreach ($cellTowers as $tower) {
        fputcsv($handle, $tower);
    }
    fclose($handle);
}
*/

// Load the population data
$populationPath = 'C:\Users\mesac\Downloads\Code\Code\AUT\nz_population_utm.csv';
$populationData = [];
if (($handle = fopen($populationPath, 'r')) !== FALSE) {
    $headers = fgetcsv($handle, 1000, ',');
    while (($data = fgetcsv($handle, 1000, ',')) !== FALSE) {
        $populationData[] = array_combine($headers, $data);
    }
    fclose($handle);
}

// Remove unnecessary columns
$columnsToDrop = ['full coordinate ', 'edited coordinate ', 'coordinate with multipolygon', 'coordinate', 'x_y'];
foreach ($populationData as &$data) {
    foreach ($columnsToDrop as $column) {
        unset($data[$column]);
    }
}

// Clean trailing commas from specific columns
function cleanCommas($value) {
    return is_string($value) ? rtrim($value, ',') : $value;
}

$columnsToClean = ['x', 'y', 'x2', 'y2', 'x3', 'y3', 'x4', 'y4', 'x center', 'y center'];
foreach ($populationData as &$data) {
    foreach ($columnsToClean as $column) {
        if (isset($data[$column])) {
            $data[$column] = cleanCommas($data[$column]);
        }
    }
}

// Convert population data lat/lng to UTM coordinates
foreach ($populationData as &$data) {
    if (isset($data['y']) && isset($data['x']) && is_numeric($data['y']) && is_numeric($data['x'])) {
        $utmCoords = convertToUTM($data['y'], $data['x']);
        $data['utm_easting'] = $utmCoords['easting'];
        $data['utm_northing'] = $utmCoords['northing'];
    } else {
        $data['utm_easting'] = null;
        $data['utm_northing'] = null;
    }
}

// Calculate the population covered by each cell tower
foreach ($cellTowers as &$tower) {
    $totalPopulation = 0;
    if (isset($tower['utm_easting']) && isset($tower['utm_northing']) && is_numeric($tower['utm_easting']) && is_numeric($tower['utm_northing'])) {
        foreach ($populationData as $popData) {
            // Create coordinates for the tower and population points
            if (isset($popData['utm_easting']) && isset($popData['utm_northing']) && is_numeric($popData['utm_easting']) && is_numeric($popData['utm_northing'])) {
                $towerCoord = ['easting' => $tower['utm_easting'], 'northing' => $tower['utm_northing']];
                $popCoord = ['easting' => $popData['utm_easting'], 'northing' => $popData['utm_northing']];

                // Calculate distance manually (simplified for this example)
                $distance = sqrt(pow($towerCoord['easting'] - $popCoord['easting'], 2) + pow($towerCoord['northing'] - $popCoord['northing'], 2));

                // Check if within 5km radius
                if ($distance <= 5000) {
                    $totalPopulation += $popData['ERP_2022']; // Assuming ERP_2022 is the population count
                }
            }
        }
    }
    $tower['covered_population'] = $totalPopulation;
}

// Sort towers by covered population
usort($cellTowers, function ($a, $b) {
    return $b['covered_population'] <=> $a['covered_population'];
});

// Output sorted cell towers, each on a new line
foreach ($cellTowers as $tower) {
    echo "Site: {$tower['sitename']}, Covered Population: {$tower['covered_population']}\n";
}

?>