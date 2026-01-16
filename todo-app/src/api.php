<?php
require_once 'db.php';
header('Content-Type: application/json');
$method = $_SERVER['REQUEST_METHOD'];
if ($method === 'GET') {
  $result = $conn->query("SELECT * FROM todos");
  $todos = [];
  while ($row = $result->fetch_assoc()) { $todos[] = $row; }
  echo json_encode($todos);
} elseif ($method === 'POST') {
  $data = json_decode(file_get_contents('php://input'), true);
  $text = $conn->real_escape_string($data['text']);
  $conn->query("INSERT INTO todos (text, user_id) VALUES ('$text', 'user')");
  echo json_encode(['id' => $conn->insert_id]);
}
