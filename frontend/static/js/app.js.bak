// app.js - Node.js starter for Plesk (Express.js)
// This file runs a minimal Express server and can optionally call Python (app.py) if needed.

const express = require("express");
const { spawn } = require("child_process");
const httpProxy = require("http-proxy");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 5000;
const HOST = process.env.HOST || "127.0.0.1"; // Plesk va server uchun mos host
const PY_HOST = process.env.FLASK_HOST || "127.0.0.1";
const PY_PORT = process.env.FLASK_PORT || 8001;

// Serve static files if needed
app.use("/static", express.static(path.join(__dirname, "static")));

// Health check route
app.get("/health", (req, res) => {
  res.json({ status: "ok", message: "Node.js app is running." });
});

// Start Python Flask server (run.py) once and proxy everything to it
let pyStarted = false;
function startPython() {
  if (pyStarted) return;
  pyStarted = true;
  const env = Object.assign({}, process.env, {
    FLASK_HOST: PY_HOST,
    FLASK_PORT: PY_PORT,
    FLASK_DEBUG: process.env.FLASK_DEBUG || "0",
  });
  const py = spawn(
    process.platform.startsWith("win") ? "python" : "python3",
    ["run.py"],
    {
      cwd: __dirname,
      env,
      stdio: "inherit",
    }
  );
  py.on("exit", (code) => {
    console.log("Flask server exited with code", code);
    pyStarted = false;
  });
}

startPython();

const proxy = httpProxy.createProxyServer({
  target: `http://${PY_HOST}:${PY_PORT}`,
  changeOrigin: true,
});

// Proxy all non-static routes to Flask
app.use((req, res, next) => {
  if (req.path.startsWith("/static")) return next();
  proxy.web(req, res, {}, (err) => {
    console.error("Proxy error:", err);
    res.status(502).json({ error: "Bad gateway" });
  });
});

// 404 handler
// 404 handled by Flask via proxy

// Error handler
app.use((err, req, res, next) => {
  console.error("Unhandled error:", err);
  res.status(500).json({ error: "Internal server error" });
});

app.listen(PORT, HOST, () => {
  console.log("✅ Server successfully started!");
  console.log(`🌍 Host: ${HOST}`);
  console.log(`🚪 Port: ${PORT}`);
  console.log(`🔗 URL: http://${HOST}:${PORT}/`);
});
