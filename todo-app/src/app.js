import axios from 'axios';

const API_URL = '/api.php';

function fetchTodos() {
    return axios.get(API_URL);
}

function addTodo(text) {
    return axios.post(API_URL, { text });
}

function updateTodo(id, text, completed) {
    return axios.put(`${API_URL}?id=${id}`, { text, completed });
}

function deleteTodo(id) {
    return axios.delete(`${API_URL}?id=${id}`);
}

export { fetchTodos, addTodo, updateTodo, deleteTodo };
