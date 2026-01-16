<?php
$db_host = 'mysql';
$db_user = 'root';
$db_pass = 'rootpass';
$db_name = 'todoapp';
$conn = new mysqli($db_host, $db_user, $db_pass, $db_name);
if ($conn->connect_error) die('DB Error: ' . $conn->connect_error);