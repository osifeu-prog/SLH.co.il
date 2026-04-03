import express from "express";

export function createServer() {
  const app = express();

  app.get("/", (_, res) => {
    res.send("Server running");
  });

  return app;
}
