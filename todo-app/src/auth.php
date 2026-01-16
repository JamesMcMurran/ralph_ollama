<?php
function session_start_safe() { if (session_status() === PHP_SESSION_NONE) session_start(); }
function login($user) { session_start_safe(); $_SESSION['user'] = $user; }
function logout() { session_start_safe(); session_destroy(); }
function is_logged_in() { session_start_safe(); return isset($_SESSION['user']); }
function get_current_user() { session_start_safe(); return $_SESSION['user'] ?? null; }