import test from "node:test";
import assert from "node:assert/strict";
import { flaskRequest } from "../src/services/flaskApi.js";
import { config } from "../src/config.js";

test("forwards request body, headers, and session cookie", async (t) => {
  const body = JSON.stringify({ error_log: "Example error" });

  const fetchMock = t.mock.method(globalThis, "fetch", async () => {
    return new Response(JSON.stringify({ id: 1 }), {
      status: 201,
      headers: {
        "Content-Type": "application/json",
        "Set-Cookie": "session=example; HttpOnly",
      },
    });
  });

  const result = await flaskRequest(
    "/analyze",
    {
      method: "POST",
      body,
      headers: { "X-Request-ID": "test-request" },
    },
    "session=existing",
  );

  assert.equal(fetchMock.mock.callCount(), 1);

  const [url, options] = fetchMock.mock.calls[0].arguments;

  assert.equal(url, `${config.flaskApiUrl}/analyze`);
  assert.equal(options.method, "POST");
  assert.equal(options.body, body);
  assert.equal(options.headers["Content-Type"], "application/json");
  assert.equal(options.headers["X-Request-ID"], "test-request");
  assert.equal(options.headers.Cookie, "session=existing");

  assert.deepEqual(result, {
    status: 201,
    data: { id: 1 },
    setCookie: "session=example; HttpOnly",
  });
});

test("returns backend errors without inventing a session cookie", async (t) => {
  const fetchMock = t.mock.method(globalThis, "fetch", async () => {
    return new Response(JSON.stringify({ error: "Unauthorized" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  });

  const result = await flaskRequest("/log");

  assert.equal(fetchMock.mock.calls[0].arguments[1].headers.Cookie, undefined);
  assert.deepEqual(result, {
    status: 401,
    data: { error: "Unauthorized" },
    setCookie: null,
  });
});

test("propagates network failures", async (t) => {
  t.mock.method(globalThis, "fetch", async () => {
    throw new Error("Backend unavailable");
  });

  await assert.rejects(flaskRequest("/log"), /Backend unavailable/);
});
