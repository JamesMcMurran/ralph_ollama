<?php
$conn = new mysqli('localhost', 'user', 'password', 'mydb');
if ($conn->connect_error) {
  die('Connection failed: ' . $conn->connect_error);
}
