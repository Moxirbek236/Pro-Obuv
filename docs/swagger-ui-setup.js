const express = require('express');
const path = require('path');
const swaggerUi = require('swagger-ui-express');
const YAML = require('yamljs');

const app = express();
const swaggerDocument = YAML.load(path.join(__dirname, '..', 'swagger.yaml'));

app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument));

const port = process.env.PORT || 3001;
app.listen(port, () => {
  console.log(`Swagger UI available at http://localhost:${port}/docs`);
});

module.exports = app;