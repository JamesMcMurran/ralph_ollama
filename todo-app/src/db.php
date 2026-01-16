<?php
$host = 'mysql';
$user = 'root';
$password = 'rootpass';
die('Could not connect: ' . mysqli_connect_error()) if (!($connection = mysqli_connect($host, $user, $password)));
die('Could not select database: ' . mysqli_error($connection)) if (!mysqli_select_db($connection, 'todoapp'));
?>