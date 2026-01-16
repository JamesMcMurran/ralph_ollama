<?php
$conn = new mysqli('localhost', 'user', 'password', 'todoapp');
if ($conn->connect_error) {
  die('Connection failed: ' . $conn->connect_error);
}
