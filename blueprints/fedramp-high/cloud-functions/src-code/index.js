const functions = require('@google-cloud/functions-framework');

// Define the function with the name "helloHttp"
functions.http('helloHttp', (req, res) => {
  res.send(`Hello, ${req.query.name || req.body.name || 'World'}!`);
});