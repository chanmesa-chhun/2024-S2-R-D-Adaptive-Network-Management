<?php

// Load the CSV file and parse it into an array
function loadCSV($filePath) {
    $data = [];

    if (!file_exists($filePath) || !is_readable($filePath)) {
        throw new Exception("Error: File does not exist or is not readable.");
    }

    if (($handle = fopen($filePath, 'r')) !== FALSE) {
        $header = fgetcsv($handle, 1000, ",");
        if ($header === false) {
            throw new Exception("Error: CSV file appears to be empty.");
        }
        
        while (($row = fgetcsv($handle, 1000, ",")) !== FALSE) {
            if (count($header) === count($row)) {
                $data[] = array_combine($header, $row);
            } else {
                throw new Exception("Error: Row data does not match header column count.");
            }
        }
        fclose($handle);
    }

    if (empty($data)) {
        throw new Exception("Error: No data found in CSV file.");
    }

    return $data;
}

// Save data to CSV
function saveCSV($filePath, $data) {
    if (empty($data)) {
        throw new Exception("Error: No data provided to save.");
    }

    $handle = fopen($filePath, 'w');
    if ($handle === FALSE) {
        throw new Exception("Error: Unable to open file for writing.");
    }

    fputcsv($handle, array_keys($data[0]));
    foreach ($data as $row) {
        fputcsv($handle, $row);
    }
    fclose($handle);
}

// Convert WGS84 (lat, lng) to UTM without a library
function convertToUTM($lat, $lng) {
    if (!is_numeric($lat) || !is_numeric($lng)) {
        throw new InvalidArgumentException("Error: Latitude and Longitude must be numeric values.");
    }

    if ($lat < -90 || $lat > 90) {
        throw new InvalidArgumentException("Error: Latitude must be between -90 and 90 degrees.");
    }

    if ($lng < -180 || $lng > 180) {
        throw new InvalidArgumentException("Error: Longitude must be between -180 and 180 degrees.");
    }

    // Determine the UTM zone
    $zone = floor(($lng + 180) / 6) + 1;

    // WGS84 constants
    $a = 6378137.0; // Semi-major axis of the WGS84 ellipsoid
    $f = 1 / 298.257223563; // Flattening
    $k0 = 0.9996; // Scale factor for UTM

    $e = sqrt(2 * $f - $f * $f); // Eccentricity of the ellipsoid
    $n = $f / (2 - $f);
    $A = $a / (1 + $n) * (1 + pow($n, 2) / 4 + pow($n, 4) / 64);

    // Convert latitude and longitude to radians
    $latRad = deg2rad($lat);
    $lngRad = deg2rad($lng);

    // Calculate the longitude of the central meridian for the zone
    $lngOrigin = deg2rad($zone * 6 - 183);

    // Calculate conformal latitude
    $t = sinh(atanh(sin($latRad)) - (2 * sqrt($n)) / (1 + $n) * atanh((2 * sqrt($n)) / (1 + $n) * sin($latRad)));
    $xi = atan($t / cos($lngRad - $lngOrigin));
    $eta = atanh(sin($lngRad - $lngOrigin) / sqrt(1 + $t * $t));

    // Calculate easting and northing
    $x = $A * $eta * $k0;
    $y = $A * $xi * $k0;

    // Adjust for southern hemisphere
    if ($lat < 0) {
        $y += 10000000.0; // False northing for southern hemisphere
    }

    // Add false easting to easting value
    $easting = $x + 500000.0; // False easting
    $northing = $y;

    return [$easting, $northing];
}

// Function to calculate population coverage (simplified version)
function calculatePopulationCoverage($cellTowers, $populationData) {
    if (!is_array($cellTowers) || !is_array($populationData)) {
        throw new InvalidArgumentException("Error: Input data must be arrays.");
    }

    foreach ($cellTowers as &$tower) {
        $coveredPopulation = 0;

        if (!isset($tower['utm_easting'], $tower['utm_northing'])) {
            throw new Exception("Error: Cell tower data is missing UTM coordinates.");
        }

        foreach ($populationData as $pop) {
            // Update column names to match actual CSV headers
            $utmEastingCenter = $pop['utm_easting_x_center'] ?? $pop['utm_easting_x'] ?? null;
            $utmNorthingCenter = $pop['utm_northing_y_center'] ?? $pop['utm_northing_y'] ?? null;

            if ($utmEastingCenter === null || $utmNorthingCenter === null) {
                // Skip this population point if coordinates are missing
                continue;
            }

            if (!is_numeric($utmEastingCenter) || !is_numeric($utmNorthingCenter)) {
                throw new Exception("Error: Population data contains invalid UTM coordinates.");
            }

            // Assuming a simple distance check (requires proper geospatial calculations)
            $distance = sqrt(pow($tower['utm_easting'] - $utmEastingCenter, 2) + pow($tower['utm_northing'] - $utmNorthingCenter, 2));
            if ($distance <= 5000) { // 5 km radius
                $coveredPopulation += (float)$pop['ERP_2022'];
            }
        }
        $tower['covered_population'] = $coveredPopulation;
    }
    return $cellTowers;
}

// Load cell tower data
try {
    $cellTowersPath = 'C:\Users\mesac\Downloads\Code\Code\AUT\cell_towers_with_utm.csv';
    $cellTowers = loadCSV($cellTowersPath);

    // Add UTM coordinates to cell towers
    foreach ($cellTowers as &$tower) {
        if (isset($tower['antlat'], $tower['antlng'])) {
            list($utmEasting, $utmNorthing) = convertToUTM($tower['antlat'], $tower['antlng']);
            $tower['utm_easting'] = $utmEasting;
            $tower['utm_northing'] = $utmNorthing;
        } else {
            throw new Exception("Error: Missing latitude or longitude in cell tower data.");
        }
    }
    unset($tower);

    // Load population data
    $populationDataPath = 'C:\Users\mesac\Downloads\Code\Code\AUT\nz_population_utm.csv';
    $populationData = loadCSV($populationDataPath);

    // Calculate population coverage for each cell tower
    $cellTowers = calculatePopulationCoverage($cellTowers, $populationData);

    // Sort cell towers by covered population
    usort($cellTowers, function($a, $b) {
        return $b['covered_population'] - $a['covered_population'];
    });

    // Output sorted towers with better formatting
    echo "<html><body><table border='1' cellpadding='5' cellspacing='0'>";
    echo "<tr><th>Site Name</th><th>Latitude</th><th>Longitude</th><th>UTM Easting</th><th>UTM Northing</th><th>Covered Population</th></tr>";
    foreach ($cellTowers as $tower) {
        echo "<tr>
            <td>" . htmlspecialchars($tower['sitename']) . "</td>
            <td>" . htmlspecialchars($tower['antlat']) . "</td>
            <td>" . htmlspecialchars($tower['antlng']) . "</td>
            <td>" . htmlspecialchars(number_format($tower['utm_easting'], 2)) . "</td>
            <td>" . htmlspecialchars(number_format($tower['utm_northing'], 2)) . "</td>
            <td>" . htmlspecialchars(number_format($tower['covered_population'], 2)) . "</td>
        </tr>";
    }
    echo "</table></body></html>";

} catch (Exception $e) {
    echo "Error: " . $e->getMessage();
}

?>