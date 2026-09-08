import express from "express";
import expressEjsLayouts from "express-ejs-layouts";
import path from "path";
import { fileURLToPath } from "url";
import { config } from "./config.js";
import session from "express-session";
import authRouter from "./routes/auth.js";
import dashboardRouter from "./routes/dashboard.js";
import analyzeRouter from "./routes/analyze.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

// View engine setup
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "..", "views"));
app.use(expressEjsLayouts);
app.set("layout", "layouts/main");

// #####################################################
// ################# MIDDLEWARES #######################
// #####################################################

// Static files (compiled CSS, client-side JS)
app.use(express.static(path.join(__dirname, "..", "public")));

// Parse form submissions and JSON bodies
app.use(express.urlencoded({ extended: true }));
app.use(express.json());


// Session 
app.use(
    session({
        secret: config.sessionSecret,
        resave: false,
        saveUninitialized: false,
        cookie: { httpOnly: true, secure: false, maxAge: 1000 * 60 * 60 * 24 },
    }),
);

// Making sure auth state available to every view
app.use((req, res, next) => {
    res.locals.isSignedIn = Boolean(req.session.isSignedIn);
    next();
});

// Routes
app.use("/auth", authRouter);
app.use("/dashboard", dashboardRouter);
app.use("/analyze", analyzeRouter);

// Home route
app.get("/", (req, res) => {
    res.render("pages/home", { title: "LogBeacon — Home" });
});

app.listen(config.port, () => {
    console.log(
        `LogBeacon frontend running on http://localhost:${config.port}`,
    );
});
