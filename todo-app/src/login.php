<?php
require_once 'auth.php';
header('Content-Type: application/json');
$method = $_SERVER['REQUEST_METHOD'];
$data = json_decode(file_get_contents('php://input'), true);
switch ($method) {
    case 'GET':
        echo json_encode(['user' => get_current_user(), 'logged_in' => is_logged_in()]);
        break;
    case 'POST':
        if (!empty($data['username'])) {
            login($data['username']);
            echo json_encode(['success' => true]);
        }
        break;
    case 'DELETE':
        logout();
        echo json_encode(['success' => true]);
        break;
}
