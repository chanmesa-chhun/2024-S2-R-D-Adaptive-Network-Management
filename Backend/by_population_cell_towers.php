<?php

ini_set('memory_limit', '256M'); // Increase memory limit to 256MB

// Load the cell tower data from the uploaded CSV file
function loadCSV($filePath) {
    $data = [];
    if (($handle = fopen($filePath, 'r')) !== FALSE) {
        $header = fgetcsv($handle, 1000, ",");
        while (($row = fgetcsv($handle, 1000, ",")) !== FALSE) {
            $data[] = array_combine($header, $row);
        }
        fclose($handle);
    }
    return $data;
}

$cellTowersData = loadCSV('C:\Users\mesac\Downloads\Code\Code\AUT\prototype1 cell towers.csv');

function convertToUTM($lat, $lng) {
    $zone = floor(($lng + 180) / 6) + 1;
    $cmeridian = deg2rad(-183 + ($zone * 6));
    $latRad = deg2rad($lat);
    $lngRad = deg2rad($lng);

    $sm_a = 6378137.0;
    $sm_b = 6356752.314;
    $sm_EccSquared = 6.69437999013e-03;

    $N = $sm_a / sqrt(1 - $sm_EccSquared * sin($latRad) * sin($latRad));
    $T = tan($latRad) * tan($latRad);
    $C = $sm_EccSquared / (1 - $sm_EccSquared) * cos($latRad) * cos($latRad);
    $A = cos($latRad) * ($lngRad - $cmeridian);

    $M = $latRad * (1 - $sm_EccSquared / 4 - 3 * ($sm_EccSquared * $sm_EccSquared) / 64 - 5 * ($sm_EccSquared * $sm_EccSquared * $sm_EccSquared) / 256);
    $M = $M - sin(2 * $latRad) * (3 * $sm_EccSquared / 8 + 3 * ($sm_EccSquared * $sm_EccSquared) / 32 + 45 * ($sm_EccSquared * $sm_EccSquared * $sm_EccSquared) / 1024);
    $M = $M + sin(4 * $latRad) * (15 * ($sm_EccSquared * $sm_EccSquared) / 256 + 45 * ($sm_EccSquared * $sm_EccSquared * $sm_EccSquared) / 1024);
    $M = $M - sin(6 * $latRad) * (35 * ($sm_EccSquared * $sm_EccSquared * $sm_EccSquared) / 3072);

    $utmEasting = (0.9996 * $N * ($A + (1 - $T + $C) * pow($A, 3) / 6 + (5 - 18 * $T + $T * $T + 72 * $C - 58 * ($sm_EccSquared / (1 - $sm_EccSquared))) * pow($A, 5) / 120) + 500000.0);
    $utmNorthing = (0.9996 * ($M + $N * tan($latRad) * ($A * $A / 2 + (5 - $T + 9 * $C + 4 * $C * $C) * pow($A, 4) / 24 + (61 - 58 * $T + $T * $T + 600 * $C - 330 * ($sm_EccSquared / (1 - $sm_EccSquared))) * pow($A, 6) / 720)));

    return [$utmEasting, $utmNorthing];
}

// Apply the conversion and create a new array with UTM coordinates
foreach ($cellTowersData as &$row) {
    if (isset($row['antlat']) && isset($row['antlng'])) {
        list($utmEasting, $utmNorthing) = convertToUTM($row['antlat'], $row['antlng']);
        $row['utm_easting'] = $utmEasting;
        $row['utm_northing'] = $utmNorthing;
    }
}

// Save the updated data to a new CSV file
function saveCSV($filePath, $data) {
    $fp = fopen($filePath, 'w');
    fputcsv($fp, array_keys($data[0])); // Header
    foreach ($data as $row) {
        fputcsv($fp, $row);
    }
    fclose($fp);
}

saveCSV('C:\Users\mesac\Downloads\Code\Code\AUT\cell_towers_with_utm.csv', $cellTowersData);

// Load the population data from another CSV file (? what is this for)
$populationData = loadCSV('C:\Users\mesac\Downloads\Code\Code\AUT\statsNZ.csv');

// Display the updated data as a downloadable CSV file 
header('Content-Type: text/csv');
header('Content-Disposition: attachment; filename="cell_towers_with_utm.csv"');

// Open the output stream
$output = fopen('php://output', 'w');

// Write the header row
fputcsv($output, array_keys($cellTowersData[0]));

// Write the data rows
foreach ($cellTowersData as $row) {
    fputcsv($output, $row);
}

// Close the output stream
fclose($output);

// Optionally, save the file locally as well
// saveCSV('C:\Users\mesac\Downloads\Code\Code\AUT\cell_towers_with_utm.csv', $cellTowersData);