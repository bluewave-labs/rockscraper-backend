const express = require("express");
const cors = require("cors");
const helmet = require("helmet");
const dotenv = require("dotenv");
const bodyParser = require("body-parser");
const mongoose = require("mongoose");
const jsonErrorMiddleware = require("./middleware/jsonError.middleware");
const fileSizeValidator = require("./middleware/fileSizeValidator.middleware");
const { MAX_FILE_SIZE } = require("./utils/constants.helper");

// Load environment variables from .env file
dotenv.config();
const app = express();

app.use(cors());
app.options('*', cors()); // this is for preflight requests
app.use(helmet());
app.use(bodyParser.json({ limit: MAX_FILE_SIZE }));
app.use(jsonErrorMiddleware);
if (process.env.ENABLE_IP_CHECK === 'true') {
  app.use(ipFilter);
}

const MONGO_URI = `mongodb://${process.env.MONGO_USER}:${process.env.MONGO_PASSWORD}@${process.env.MONGO_HOST}:${process.env.MONGO_PORT}/${process.env.MONGO_DBNAME}?authSource=admin`;
mongoose.connect(MONGO_URI)
  .then(() => console.log("MongoDB connected..."))
  .catch((err) => console.log("Error: " + err));

app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ message: "Internal Server Error" });
});

module.exports = app;
