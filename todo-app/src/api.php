<?php
require_once 'auth.php';
require_once 'todo.php';

header('Content-Type: application/json');
$method = $_SERVER['REQUEST_METHOD'];
$action = $_GET['action'] ?? null;
$data = json_decode(file_get_contents('php://input'), true);
$user = is_logged_in() ? get_current_user() : null;

switch ($method) {
    case 'GET':
        if ($action === 'todos') {
            $result = get_todos($user);
        }
        break;
    case 'POST':
        if ($action === 'add' && !empty($data['text'])) {
            $id = add_todo($user, $data['text']);
            $result = ['id' => $id];
        }
        break;
    case 'PUT':
        if (!empty($data['id']) && isset($data['text']) || isset($data['completed'])) {
            update_todo($data['id'], $data['text'] ?? null, $data['completed'] ?? 0);
            $result = ['success' => true];
        }
        break;
    case 'DELETE':
        if (!empty($data['id'])) {
            delete_todo($data['id']);
            $result = ['success' => true];
        }
        break;
}
echo json_encode($result);