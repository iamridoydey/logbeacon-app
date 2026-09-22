import { Router } from "express";
import { flaskRequest } from "../services/flaskApi.js";

const router = Router();

// Signed-in users should go to the dashboard.
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
router.post("/register", redirectIfSignedIn, async (req, res) => {
  const { username, email, password } = req.body;

  const { status, data } = await flaskRequest("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, email, password }),
  });

  if (status !== 201) {
    return res.render("pages/register", {
      title: "Register — LogBeacon",
      error: data.error,
    });
  }

  req.session.apiKey = data.api_key;

  return res.render("pages/register", {
    title: "Register — LogBeacon",
    error: null,
    apiKey: data.api_key,
  });
});

// Sign-in page
router.get("/signin", redirectIfSignedIn, (req, res) => {
  res.render("pages/signin", {
    title: "Sign In — LogBeacon",
    error: null,
  });
});

// Sign-in submission
router.post("/signin", redirectIfSignedIn, async (req, res) => {
  const { username, password } = req.body;

  const { status, data, setCookie } = await flaskRequest("/auth/signin", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });

  if (status !== 200) {
    return res.render("pages/signin", {
      title: "Sign In — LogBeacon",
      error: data.error,
    });
  }

  if (setCookie) {
    res.setHeader("Set-Cookie", setCookie);
  }

  req.session.isSignedIn = true;

  return res.redirect("/dashboard");
});

// Sign out
router.post("/signout", async (req, res) => {
  await flaskRequest("/auth/signout", { method: "POST" }, req.headers.cookie);

  req.session.destroy(() => {
    res.redirect("/");
  });
});

export default router;
