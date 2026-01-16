<?php
require_once 'db.php';
function get_todos($user) {
    global $conn;
    $stmt = $conn->prepare("SELECT * FROM todos WHERE user_id=? ORDER BY position");
    $stmt->bind_param("s", $user);
    $stmt->execute();
    return $stmt->get_result()->fetch_all(MYSQLI_ASSOC);
}
function add_todo($user, $text) {
    global $conn;
    $stmt = $conn->prepare("INSERT INTO todos (user_id, text, position) VALUES (?, ?, (SELECT COALESCE(MAX(position),0)+1 FROM todos t WHERE user_id=?))");
    $stmt->bind_param("sss", $user, $text, $user);
    $stmt->execute();
    return $conn->insert_id;
}
function update_todo($id, $text, $completed) {
    global $conn;
    $stmt = $conn->prepare("UPDATE todos SET text=?, completed=? WHERE id=?");
    $stmt->bind_param("sii", $text, $completed, $id);
    $stmt->execute();
}
function delete_todo($id) {
    global $conn;
    $stmt = $conn->prepare("DELETE FROM todos WHERE id=?");
    $stmt->bind_param("i", $id);
    $stmt->execute();
}
function reorder_todos($id, $newPos) {
    global $conn;
    $stmt = $conn->prepare("UPDATE todos SET position=? WHERE id=?");
    $stmt->bind_param("ii", $newPos, $id);
    $stmt->execute();
}
