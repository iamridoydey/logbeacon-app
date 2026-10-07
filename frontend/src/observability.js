import { metrics, SpanStatusCode, trace } from "@opentelemetry/api";

export const tracer = trace.getTracer("logbeacon.frontend");
const meter = metrics.getMeter("logbeacon.frontend");

// Reusable histogram metrics function
export function makeDurationHistogram(name, boundaries, description = "") {
  return meter.createHistogram(name, {
    unit: "s",
    description,
    advice: { explicitBucketBoundaries: boundaries },
  });
}

// Reusable counter metrics function
export function makeExecutionCounter(name, description = "") {
  return meter.createCounter(name, {
    unit: "1",
    description,
  });
}



// Run `fn` inside a child span, e.g. around a call to the Flask backend.
// If fn throws, the span is marked as an error and the error is re-thrown.
export function withSpan(name, fn) {
  return tracer.startActiveSpan(name, async (span) => {
    try {
      return await fn(span);
    } catch (err) {
      span.recordException(err);
      span.setStatus({ code: SpanStatusCode.ERROR });
      throw err;
    } finally {
      span.end();
    }
  });
}
