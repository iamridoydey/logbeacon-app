import { Router } from "express";
import { flaskRequest } from "../services/flaskApi.js";
import { marked } from "marked";

const router = Router();

function withHtml(entries) {
    return (entries || []).map(e => ({
        ...e,
        error_solution_html: e.error_solution ? marked.parse(e.error_solution) : ""
    }));
}

router.get("/", async (req, res, next) => {
    try {
        const { status, data } = await flaskRequest("/log", {}, req.headers.cookie);

        if (status === 401) {
            return res.redirect("/auth/signin");
        }

        res.render("pages/analyze", {
            title: "Analyze — LogBeacon",
            error: null,
            entries: withHtml(data.entries),
        });
    } catch (err) {
        next(err);
    }
});

// AJAX endpoint — returns JSON, never redirects, never renders a page
router.post("/", async (req, res, next) => {
    try {
        const { error_log } = req.body;

        const { status, data } = await flaskRequest("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ error_log }),
        }, req.headers.cookie);

        if (status === 401) {
            return res.status(401).json({ error: "Not signed in — please sign in again." });
        }

        if (status !== 201) {
            return res.status(status).json({ error: data.error || "Something went wrong." });
        }

        // success — send back the one new entry, ready for the browser to render
        res.status(201).json({
            entry: {
                id: data.id,
                created_at: data.created_at || new Date().toISOString(),
                error_log,
                error_solution_html: marked.parse(data.error_solution),
                input_tokens: data.input_tokens,
                output_tokens: data.output_tokens,
                cost: data.cost,
            }
        });
    } catch (err) {
        next(err);
    }
});

export default router;