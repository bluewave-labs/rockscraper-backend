const express = require("express");
const cors = require("cors");
const helmet = require("helmet");
const dotenv = require("dotenv");
const bodyParser = require("body-parser");
const mongoose = require("mongoose");
const jsonErrorMiddleware = require("./middleware/jsonError.middleware");
const fileSizeValidator = require("./middleware/fileSizeValidator.middleware");
const { MAX_FILE_SIZE } = require("./utils/constants.helper");
const config = require("../config/config.js");

// Load environment variables from .env file
dotenv.config();
const env = process.env.NODE_ENV || "development";
const envConfig = config[env];

const app = express();
app.use(cors());
app.options('*', cors()); // this is for preflight requests
app.use(helmet());
app.use(bodyParser.json({ limit: MAX_FILE_SIZE }));
app.use(jsonErrorMiddleware);

const MONGO_URI = `mongodb://${envConfig.username}:${envConfig.password}@${envConfig.host}:${envConfig.port}/${envConfig.database}?authSource=admin`;
mongoose.connect(MONGO_URI)
  .then(() => console.log("MongoDB connected..."))
  .catch((err) => console.log("Error: " + err));

app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ message: "Internal Server Error" });
});

module.exports = app;
