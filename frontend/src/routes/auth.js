import { Router } from "express";
import { flaskRequest } from "../services/flaskApi.js";

const router = Router();

// Route the user to the register page
router.get("/register", (req, res) => {
    res.render("pages/register", {
        title: "Register — LogBeacon",
        error: null,
    });
});

router.post("/register", async (req, res) => {
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

    req.session.apiKey = data.api_key; // stash it server-side, tied to this browser's session

    res.render("pages/register", {
        title: "Register — LogBeacon",
        error: null,
        apiKey: data.api_key,
    });
});

// Route the user to the signin page
router.get("/signin", (req, res) => {
    res.render("pages/signin", { title: "Sign In — LogBeacon", error: null });
});

router.post("/signin", async (req, res) => {
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

    res.redirect("/dashboard");
});

// Route the user to the home page(signout)
router.post("/signout", async (req, res) => {
    await flaskRequest("/auth/signout", { method: "POST" }, req.headers.cookie);
    req.session.destroy(() => {
        res.redirect("/");
    });
});

export default router;
