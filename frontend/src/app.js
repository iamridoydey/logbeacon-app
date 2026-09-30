import express from "express";
import expressEjsLayouts from "express-ejs-layouts";
import path from "path";
import { fileURLToPath } from "url";
import { config } from "./config.js";
import session from "express-session";
import authRouter from "./routes/auth.js";
import dashboardRouter from "./routes/dashboard.js";
import analyzeRouter from "./routes/analyze.js";
import { logger } from "./logger.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

// View engine setup
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "..", "views"));
app.use(expressEjsLayouts);
app.set("layout", "layouts/main");

// Static files
app.use(express.static(path.join(__dirname, "..", "public")));

app.use((req, res, next) => {
  const start = Date.now();
  res.on("finish", () => {
    logger.info(
      {
        method: req.method,
        path: req.path, 
        status: res.statusCode,
        duration_ms: Date.now() - start,
      },
      "request completed",
    );
  });
  next();
});

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

app.use(
  session({
    secret: config.sessionSecret,
    resave: false,
    saveUninitialized: false,
    cookie: { httpOnly: true, secure: false, maxAge: 1000 * 60 * 60 * 24 },
  }),
);

app.use((req, res, next) => {
  res.locals.isSignedIn = Boolean(req.session.isSignedIn);
  next();
});

app.use("/auth", authRouter);
app.use("/dashboard", dashboardRouter);
app.use("/analyze", analyzeRouter);

app.get("/", (req, res) => {
  res.render("pages/home", { title: "LogBeacon — Home" });
});

app.use((err, req, res, next) => {
  logger.error({ err, method: req.method, path: req.path }, "unhandled error");
  if (res.headersSent) {
    return next(err);
  }
  res.status(500).send("Something went wrong");
});

app.listen(config.port, () => {
  logger.info({ port: config.port }, "LogBeacon frontend started");
});
