import process from "process";
import pino from "pino";


export const logger = pino({
  level: process.env.LOG_LEVEL || "info",
  transport: {
    targets: [
      { target: "pino/file", options: { destination: 1 } },
      { target: "pino-opentelemetry-transport" },
    ],
  },
});