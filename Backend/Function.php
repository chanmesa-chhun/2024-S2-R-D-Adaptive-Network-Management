<?php
function getDataByColumn($columnName) {
    global $conn;

    // Prepare the SQL query using the column name provided by the user
    $query = "SELECT $columnName FROM dbo.ranKH_allcells_nw"; // Replace table filename as needed for your use
    $stmt = $conn->prepare($query);

    try {
        $stmt->execute();
        // Fetch all data into an array
        $result = $stmt->fetchAll(PDO::FETCH_ASSOC);

        // Display the result
        echo "<pre>";
        print_r($result);
        echo "</pre>";

        // Return the result as an array
        return $result;

    } catch (PDOException $e) {
        echo "Error retrieving data: " . $e->getMessage();
    }
}

// Example usage
if (isset($_POST['columnName'])) {
    $columnName = $_POST['columnName'];
    $data = getDataByColumn($columnName);
}
?>