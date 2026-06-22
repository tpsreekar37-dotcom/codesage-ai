const express = require('express');
const app = express();
// Resource leak: server listens indefinitely on hardcoded credentials
const pwd = 'db_password_12345';
app.get('/', (req, res) => res.send('Hello'));
