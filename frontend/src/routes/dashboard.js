import { Router } from "express";
import { flaskRequest } from "../services/flaskApi.js";
import { logger } from "../logger.js"; // NEW

const router = Router();

router.get("/", async (req, res, next) => {
  try {
    const { status, data } = await flaskRequest(
      "/log",
      { method: "GET" },
      req.headers.cookie,
    );

    if (status === 401) {
      logger.info("dashboard: session expired, redirecting to sign-in");
      req.session.isSignedIn = false;
      return res.redirect("/auth/signin");
    }

    if (status !== 200) {
      logger.warn(
        { backend_status: status },
        "dashboard: backend returned an error",
      );
      return res.render("pages/error", {
        title: "Error — LogBeacon",
        message: data.error || "Something went wrong loading your dashboard.",
      });
    }

    res.render("pages/dashboard", {
      title: "Dashboard — LogBeacon",
      entries: data.entries,
      summary: data.summary,
    });
  } catch (err) {
    logger.error({ err }, "dashboard: failed to load");
    next(err);
  }
});

export default router;
