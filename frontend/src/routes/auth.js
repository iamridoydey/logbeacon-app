import { Router } from "express";
import { flaskRequest } from "../services/flaskApi.js";
import { logger } from "../logger.js";

const router = Router();

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
  try {
    const { username, email, password } = req.body;

    const { status, data } = await flaskRequest("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, email, password }),
    });

    if (status !== 201) {
      // Username is OK to log. Never email, password, or api_key.
      logger.warn({ backend_status: status, username }, "register failed");
      return res.render("pages/register", {
        title: "Register — LogBeacon",
        error: data.error,
      });
    }

    logger.info({ username }, "user registered");
    req.session.apiKey = data.api_key;

    return res.render("pages/register", {
      title: "Register — LogBeacon",
      error: null,
      apiKey: data.api_key,
    });
  } catch (err) {
    logger.error({ err }, "register: backend call failed");
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
  try {
    const { username, password } = req.body;

    const { status, data, setCookie } = await flaskRequest("/auth/signin", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });

    if (status !== 200) {
      // Failed sign-ins are worth watching: a spike can mean password guessing
      logger.warn({ backend_status: status, username }, "sign-in failed");
      return res.render("pages/signin", {
        title: "Sign In — LogBeacon",
        error: data.error,
      });
    }

    if (setCookie) {
      res.setHeader("Set-Cookie", setCookie);
    }

    req.session.isSignedIn = true;
    logger.info({ username }, "user signed in");

    return res.redirect("/dashboard");
  } catch (err) {
    logger.error({ err }, "sign-in: backend call failed");
    next(err);
  }
});

// Sign out
router.post("/signout", async (req, res, next) => {
  try {
    await flaskRequest("/auth/signout", { method: "POST" }, req.headers.cookie);
    logger.info("user signed out");

    req.session.destroy(() => {
      res.redirect("/");
    });
  } catch (err) {
    logger.error({ err }, "sign-out: backend call failed");
    next(err);
  }
});

export default router;
