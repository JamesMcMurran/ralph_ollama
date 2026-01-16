<?php
$conn = new mysqli('mysql', 'root', 'rootpass', 'todoapp');
if ($conn->connect_error) { die('Connection failed'); }
