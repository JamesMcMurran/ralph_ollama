<?php
$conn = new mysqli('localhost', 'username', 'password', 'database');
if ($conn->connect_error) {
    die('Connection failed: ' . $conn->connect_error);
}

function getTodos() {
    global $conn;
    $sql = "SELECT * FROM todos";
    $result = $conn->query($sql);
    $todos = [];
    while ($row = $result->fetch_assoc()) {
        $todos[] = $row;
    }
    return json_encode($todos);
}

function addTodo($text) {
    global $conn;
    $stmt = $conn->prepare("INSERT INTO todos (text) VALUES (?)");
    $stmt->bind_param("s", $text);
    $stmt->execute();
    return json_encode(["success" => true]);
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    echo getTodos();
} elseif ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $data = json_decode(file_get_contents('php://input'), true);
    echo addTodo($data['text']);
}

$conn->close();