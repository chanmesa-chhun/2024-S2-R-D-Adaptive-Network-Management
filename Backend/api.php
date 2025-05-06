<?php
header('Content-Type: application/json');

switch ($_SERVER['REQUEST_METHOD']) {
    case 'GET':
        // Handle GET request
        $response = [
            'method' => 'GET',
            'message' => 'Hello from GET!',
            'timestamp' => time()
        ];
        echo json_encode($response);
        break;

    case 'POST':
        // Handle POST request
        $data = json_decode(file_get_contents('php://input'), true);

        if (!isset($data['name'])) {
            http_response_code(400);
            echo json_encode(['error' => 'Missing "name" in POST data.']);
            exit;
        }

        $response = [
            'method' => 'POST',
            'message' => 'Hello, ' . htmlspecialchars($data['name']) . '!',
            'timestamp' => time()
        ];
        echo json_encode($response);
        break;

    default:
        http_response_code(405); // Method Not Allowed
        echo json_encode(['error' => 'Unsupported HTTP method.']);
        break;
}
