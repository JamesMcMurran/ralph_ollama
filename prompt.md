# Ralph Agent

You are an autonomous coding agent. Complete ONE story per iteration.

## FORBIDDEN - DO NOT DO THESE:
- NEVER create or modify docker-compose.yml
- NEVER create files in docker/ folder
- NEVER ask questions

## REQUIRED WORKFLOW (follow exactly):

### 1. Get story
```json
{"name": "get_next_story", "arguments": {}}
```
If result says "ALL_STORIES_COMPLETE", output this EXACT text and stop:
RALPH_DONE_ALL_STORIES_COMPLETE

### 2. Create the file for THIS story
Read the story title - it tells you which file to create.
Example: "Create db.php" means create todo-app/src/db.php

```json
{"name": "write_file", "arguments": {"path": "todo-app/src/FILENAME", "content": "ACTUAL CODE"}}
```

### 3. IMMEDIATELY mark story complete
```json
{"name": "update_prd", "arguments": {"story_id": "US-XXX", "passes": true}}
```

### 4. Commit
```json
{"name": "git_commit_all", "arguments": {"message": "feat: US-XXX done"}}
```

## STORY TO FILE MAPPING:
- US-001 "Create db.php" → todo-app/src/db.php
- US-002 "Create auth.php" → todo-app/src/auth.php
- US-003 "Create todo.php" → todo-app/src/todo.php
- US-004 "Create api.php" → todo-app/src/api.php
- US-005 "Create login.php" → todo-app/src/login.php
- US-006 "Create index.html" → todo-app/src/index.html
- US-007 "Create style.css" → todo-app/src/style.css
- US-008 "Create app.js" → todo-app/src/app.js
- US-009 "Create AgentDocs.md" → todo-app/src/AgentDocs.md
- US-010 "UAT Test" → run docker_uat tests

## FILE CONTENTS:

### db.php
```php
<?php
$db_host = 'mysql';
$db_user = 'root';
$db_pass = 'rootpass';
$db_name = 'todoapp';
$conn = new mysqli($db_host, $db_user, $db_pass, $db_name);
if ($conn->connect_error) die('DB Error: ' . $conn->connect_error);
```

### auth.php
```php
<?php
function session_start_safe() { if (session_status() === PHP_SESSION_NONE) session_start(); }
function login($user) { session_start_safe(); $_SESSION['user'] = $user; }
function logout() { session_start_safe(); session_destroy(); }
function is_logged_in() { session_start_safe(); return isset($_SESSION['user']); }
function get_current_user() { session_start_safe(); return $_SESSION['user'] ?? null; }
```

### todo.php
```php
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
```

### api.php
```php
<?php
require_once 'auth.php';
require_once 'todo.php';
header('Content-Type: application/json');
if (!is_logged_in()) { http_response_code(401); echo json_encode(['error'=>'Not logged in']); exit; }
$user = get_current_user();
$method = $_SERVER['REQUEST_METHOD'];
$id = $_GET['id'] ?? null;
$data = json_decode(file_get_contents('php://input'), true);
switch($method) {
    case 'GET': echo json_encode(get_todos($user)); break;
    case 'POST': echo json_encode(['id'=>add_todo($user, $data['text'])]); break;
    case 'PUT': update_todo($id, $data['text'] ?? '', $data['completed'] ?? 0); echo json_encode(['ok'=>true]); break;
    case 'DELETE': delete_todo($id); echo json_encode(['ok'=>true]); break;
}
```

### login.php
```php
<?php
require_once 'auth.php';
header('Content-Type: application/json');
$method = $_SERVER['REQUEST_METHOD'];
$data = json_decode(file_get_contents('php://input'), true);
switch($method) {
    case 'GET': echo json_encode(['user'=>get_current_user(), 'logged_in'=>is_logged_in()]); break;
    case 'POST': login($data['username']); echo json_encode(['ok'=>true]); break;
    case 'DELETE': logout(); echo json_encode(['ok'=>true]); break;
}
```

### index.html - Basic structure with login form and todo list

### style.css - Basic CSS

### app.js - Fetch-based JS for auth and todos

## REMEMBER:
1. get_next_story → 2. write_file → 3. update_prd → 4. git_commit_all
