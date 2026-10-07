import { Router } from "express";
import { trace } from "@opentelemetry/api";
import process from "process";
import { flaskRequest } from "../services/flaskApi.js";
import { logger } from "../logger.js";
import { makeDurationHistogram, withSpan } from "../observability.js";

const router = Router();

// METRIC definition: created once, when this file is first imported.
// Named "frontend" so it cannot be confused with the backend's logbeacon.auth.duration.
// Labels: action=register|signin|signout
//         outcome=success|rejected|backend_error|exception
const authDuration = makeDurationHistogram(
  "logbeacon.frontend.auth.duration",
  [0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10],
  "Time to answer POST /auth/*; labels action and outcome",
);

// Starts the stopwatch and records when the response has really been sent.
// Returns an object: set `.outcome` in the route as things happen.
function trackAuth(res, action) {
  const start = process.hrtime.bigint();
  // stays this unless the route sets another
  const state = { outcome: "exception" };

  res.once("finish", () => {
    const seconds = Number(process.hrtime.bigint() - start) / 1e9;
    // A 5xx at this point means something broke (even if a branch said "success").
    const outcome = res.statusCode >= 500 ? "exception" : state.outcome;
    authDuration.record(seconds, { action, outcome });
    trace.getActiveSpan()?.setAttribute("auth.outcome", outcome);
  });

  // Found it with TraceQL: { span.logbeacon.flow = "signin" }
  trace.getActiveSpan()?.setAttribute("logbeacon.flow", action);
  return state;
}

// What the backend's status code means for the user:
//   expected status -> success, 4xx -> rejected (user's mistake), 5xx -> backend_error
function outcomeFor(status, okStatus) {
  if (status === okStatus) return "success";
  return status >= 500 ? "backend_error" : "rejected";
}

function redirectIfSignedIn(req, res, next) {
  if (req.session.isSignedIn) {
    return res.redirect("/dashboard");
  }

  next();
}

// Register page
router.get("/register", redirectIfSignedIn, (req, res) => {
  res.render("pages/register", {
    title: "Register — LogBeacon",
    error: null,
  });
});

// Register submission
router.post("/register", redirectIfSignedIn, async (req, res, next) => {
  const track = trackAuth(res, "register");

  try {
    const { username, email, password } = req.body;

    const { status, data } = await withSpan("auth.register.backend_call", () =>
      flaskRequest("/auth/register", {
        method: "POST",
        body: JSON.stringify({ username, email, password }),
      }),
    );

    track.outcome = outcomeFor(status, 201);

    if (status !== 201) {
      // Username is OK to log. Never email, password, or api_key.
      logger.warn({ backend_status: status, username }, "flow=register failed");
      return res.render("pages/register", {
        title: "Register — LogBeacon",
        error: data.error,
      });
    }

    logger.info({ username }, "flow=register user registered");
    req.session.apiKey = data.api_key;

    return res.render("pages/register", {
      title: "Register — LogBeacon",
      error: null,
      apiKey: data.api_key,
    });
  } catch (err) {
    logger.error({ err }, "flow=register backend call failed");
    next(err);
  }
});

// Sign-in page
router.get("/signin", redirectIfSignedIn, (req, res) => {
  res.render("pages/signin", {
    title: "Sign In — LogBeacon",
    error: null,
  });
});

// Sign-in submission
router.post("/signin", redirectIfSignedIn, async (req, res, next) => {
  const track = trackAuth(res, "signin");

  try {
    const { username, password } = req.body;

    const { status, data, setCookie } = await withSpan(
      "auth.signin.backend_call",
      () =>
        flaskRequest("/auth/signin", {
          method: "POST",
          body: JSON.stringify({ username, password }),
        }),
    );

    track.outcome = outcomeFor(status, 200);

    if (status !== 200) {
      // Failed sign-ins are worth watching: a spike can mean password guessing
      logger.warn({ backend_status: status, username }, "flow=signin failed");
      return res.render("pages/signin", {
        title: "Sign In — LogBeacon",
        error: data.error,
      });
    }

    if (setCookie) {
      res.setHeader("Set-Cookie", setCookie);
    }

    req.session.isSignedIn = true;
    logger.info({ username }, "flow=signin user signed in");

    return res.redirect("/dashboard");
  } catch (err) {
    logger.error({ err }, "flow=signin backend call failed");
    next(err);
  }
});

// Sign out
router.post("/signout", async (req, res, next) => {
  const track = trackAuth(res, "signout");

  try {
    const { status } = await withSpan("auth.signout.backend_call", () =>
      flaskRequest("/auth/signout", { method: "POST" }, req.headers.cookie),
    );

    track.outcome = outcomeFor(status, 200);
    logger.info({ backend_status: status }, "flow=signout user signed out");

    // The local session is destroyed either way, so the user is signed out here.
    req.session.destroy(() => {
      res.redirect("/");
    });
  } catch (err) {
    logger.error({ err }, "flow=signout backend call failed");
    next(err);
  }
});

export default router;
