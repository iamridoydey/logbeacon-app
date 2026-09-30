import { Router } from "express";
import { flaskRequest } from "../services/flaskApi.js";
import { marked } from "marked";
import { logger } from "../logger.js"; // NEW

const router = Router();

function withHtml(entries) {
  return (entries || []).map((e) => ({
    ...e,
    error_solution_html: e.error_solution ? marked.parse(e.error_solution) : "",
  }));
}

router.get("/", async (req, res, next) => {
  try {
    const { status, data } = await flaskRequest("/log", {}, req.headers.cookie);

    if (status === 401) {
      // Session expired: normal, so info, not warn
      logger.info("analyze page: session expired, redirecting to sign-in");
      return res.redirect("/auth/signin");
    }

    res.render("pages/analyze", {
      title: "Analyze — LogBeacon",
      error: null,
      entries: withHtml(data.entries),
    });
  } catch (err) {
    // Log here for context, then let the error handler send the 500
    logger.error({ err }, "analyze page: failed to load history");
    next(err);
  }
});

router.post("/", async (req, res, next) => {
  try {
    const { error_log } = req.body;

    // Length only. Never the text itself: it may contain secrets.
    logger.info(
      { input_length: (error_log || "").length },
      "analyze: sending to backend",
    );

    const { status, data } = await flaskRequest(
      "/analyze",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ error_log }),
      },
      req.headers.cookie,
    );

    if (status === 401) {
      logger.info("analyze: not signed in");
      return res
        .status(401)
        .json({ error: "Not signed in — please sign in again." });
    }

    if (status !== 201) {
      // Flask answered but not happily: warn with its status
      logger.warn(
        { backend_status: status },
        "analyze: backend rejected request",
      );
      return res
        .status(status)
        .json({ error: data.error || "Something went wrong." });
    }

    // Token counts and cost are useful for tracking LLM spend
    logger.info(
      {
        input_tokens: data.input_tokens,
        output_tokens: data.output_tokens,
        cost: data.cost,
      },
      "analyze: success",
    );

    res.status(201).json({
      entry: {
        id: data.id,
        created_at: data.created_at || new Date().toISOString(),
        error_log,
        error_solution_html: marked.parse(data.error_solution),
        input_tokens: data.input_tokens,
        output_tokens: data.output_tokens,
        cost: data.cost,
      },
    });
  } catch (err) {
    logger.error({ err }, "analyze: request failed");
    next(err);
  }
});

export default router;
