import { Router } from "express";
import { trace } from "@opentelemetry/api";
import { flaskRequest } from "../services/flaskApi.js";
import { logger } from "../logger.js";
import process from "process";
import {
  makeDurationHistogram,
  makeExecutionCounter,
  withSpan,
} from "../observability.js";

const router = Router();

// METRIC definitions: created once, when this file is first imported.
// 2 is a bucket edge because it matches the history SLO (within 2 seconds).
const dashboardDuration = makeDurationHistogram(
  "logbeacon.dashboard.duration",
  [0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10],
  "Time to answer GET /dashboard; label outcome=success|backend_error|unauthenticated|exception",
);

// Same label values as the histogram. No ".total" in the name: the exporter adds _total.
const dashboardRequests = makeExecutionCounter(
  "logbeacon.dashboard.requests",
  "GET /dashboard requests; label outcome=success|backend_error|unauthenticated|exception",
);

router.get("/", async (req, res, next) => {
  const start = process.hrtime.bigint();
  let outcome = "exception";

  logger.info(
    {
      flow: "dashboard",
      session_id: req.sessionID,
      signed_in: req.session?.isSignedIn,
    },
    "dashboard request started",
  );

  // Registered BEFORE the first await, so every path (including early returns)
  // is recorded. It runs once the response has really been sent, so rendering
  // time is included.
  res.once("finish", () => {
    const seconds = Number(process.hrtime.bigint() - start) / 1e9;

    // If rendering itself failed, the user got a 500 even though a branch below
    // had already set outcome = "success", so trust the final status code.
    const finalOutcome = res.statusCode >= 500 ? "exception" : outcome;

    dashboardDuration.record(seconds, { outcome: finalOutcome });
    dashboardRequests.add(1, { outcome: finalOutcome });

    logger.info(
      {
        flow: "dashboard",
        outcome: finalOutcome,
        status_code: res.statusCode,
        duration_seconds: Number(seconds.toFixed(3)),
      },
      "dashboard request completed",
    );
  });

  // The request span is created by auto-instrumentation. Tag it so it can be
  // found with TraceQL: { span.logbeacon.flow = "dashboard" }
  const requestSpan = trace.getActiveSpan();
  requestSpan?.setAttribute("logbeacon.flow", "dashboard");

  try {
    logger.info(
      { flow: "dashboard" },
      "fetching dashboard history from backend",
    );

    // Child span around the Flask call: shows how much of the time is the backend.
    // withSpan ends the span, and marks it as an error if the call throws.
    const { status, data } = await withSpan("dashboard.fetch_history", () =>
      flaskRequest("/log", { method: "GET" }, req.headers.cookie),
    );

    logger.info(
      {
        flow: "dashboard",
        backend_status: status,
      },
      "dashboard backend response received",
    );

    if (status === 401) {
      outcome = "unauthenticated";

      requestSpan?.setAttribute("dashboard.outcome", outcome);

      logger.info(
        {
          flow: "dashboard",
          outcome,
        },
        "session expired, redirecting to sign in",
      );

      req.session.isSignedIn = false;
      return res.redirect("/auth/signin");
    }

    if (status !== 200) {
      outcome = "backend_error";

      requestSpan?.setAttribute("dashboard.outcome", outcome);

      logger.warn(
        {
          flow: "dashboard",
          outcome,
          backend_status: status,
          backend_error: data?.error,
        },
        "backend returned an error",
      );

      return res.render("pages/error", {
        title: "Error — LogBeacon",
        message: data.error || "Something went wrong loading your dashboard.",
      });
    }

    const entryCount = data.entries?.length ?? 0;

    outcome = "success";

    requestSpan?.setAttribute("dashboard.outcome", outcome);
    requestSpan?.setAttribute("dashboard.entries", entryCount);

    logger.info(
      {
        flow: "dashboard",
        outcome,
        entries: entryCount,
      },
      "dashboard data loaded successfully",
    );

    return res.render("pages/dashboard", {
      title: "Dashboard — LogBeacon",
      entries: data.entries,
      summary: data.summary,
    });
  } catch (err) {
    logger.error(
      {
        err,
        flow: "dashboard",
        outcome: "exception",
      },
      "dashboard request failed",
    );

    next(err);
  }
});

export default router;
