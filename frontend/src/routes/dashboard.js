import { Router } from "express";
import { flaskRequest } from "../services/flaskApi.js";

const router = Router();

router.get("/", async (req, res) => {
    const { status, data } = await flaskRequest(
        "/log",
        { method: "GET" },
        req.headers.cookie,
    );

    if (status === 401) {
        return res.redirect("/auth/signin");
    }

    if (status !== 200) {
        return res.render("pages/error", {
            title: "Error — LogBeacon",
            message:
                data.error || "Something went wrong loading your dashboard.",
        });
    }

    res.render("pages/dashboard", {
        title: "Dashboard — LogBeacon",
        entries: data.entries,
        summary: data.summary,
    });
});

export default router;
