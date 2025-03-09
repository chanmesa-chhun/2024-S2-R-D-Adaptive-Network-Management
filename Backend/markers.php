<?php
header('Content-Type: application/json');

// CSV file path. Use __DIR__ to ensure it looks in the same directory as this script
$filename = __DIR__ . '/prototype2_celltowers.csv';

$markers = [];

// Open the file
if (($handle = fopen($filename, "r")) !== false) {
    // Read the first row as headers
    $header = fgetcsv($handle);
    
    // Loop through each subsequent row
    while (($data = fgetcsv($handle)) !== false) {
        // Combine headers and row data into an associative array
        $row = array_combine($header, $data);
        
        // Convert antlat and antlng to floats
        $lat = floatval($row['antlat']);
        $lng = floatval($row['antlng']);
        
        // Push marker data to our $markers array
        $markers[] = [
            'lat' => $lat,
            'lng' => $lng,
            'sitename' => $row['sitename']
        ];
    }
    fclose($handle);
} else {
    echo json_encode(["error" => "Unable to open CSV file"]);
    exit;
}

// Output the marker data as JSON
echo json_encode($markers);
?>