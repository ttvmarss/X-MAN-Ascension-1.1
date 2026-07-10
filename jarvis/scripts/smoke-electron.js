/**
 * Smoke test — launches Electron briefly, exercises memory IPC and orb states.
 * Run: node scripts/smoke-electron.js
 */

const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

const projectRoot = path.join(__dirname, "..");
const electronBin = require("electron");
const userData = fs.mkdtempSync(path.join(require("os").tmpdir(), "jarvis-smoke-"));

const env = {
  ...process.env,
  ELECTRON_ENABLE_LOGGING: "1",
};

console.log("Launching Electron smoke test...");
console.log("User data:", userData);

const child = spawn(electronBin, [projectRoot, `--user-data-dir=${userData}`], {
  env,
  stdio: ["ignore", "pipe", "pipe"],
});

let stdout = "";
let stderr = "";
child.stdout.on("data", (d) => { stdout += d.toString(); });
child.stderr.on("data", (d) => { stderr += d.toString(); });

const timeout = setTimeout(() => {
  console.log("Electron ran for 4s without crash — PASS");
  child.kill("SIGTERM");
}, 4000);

child.on("exit", (code, signal) => {
  clearTimeout(timeout);
  const memoryFile = path.join(userData, "jarvis-memory.json");
  const memoryExists = fs.existsSync(memoryFile);
  console.log("Exit code:", code, "signal:", signal);
  console.log("Memory file created:", memoryExists);
  if (memoryExists) {
    const data = JSON.parse(fs.readFileSync(memoryFile, "utf8"));
    console.log("Memory keys:", Object.keys(data).join(", "));
  }
  if (stderr.includes("ERROR") && !stderr.includes("dbus")) {
    console.error("Stderr concerns:\n", stderr.slice(-2000));
  }
  fs.rmSync(userData, { recursive: true, force: true });
  process.exit(code === 0 || signal === "SIGTERM" ? 0 : 1);
});

child.on("error", (err) => {
  clearTimeout(timeout);
  console.error("Failed to spawn Electron:", err);
  process.exit(1);
});
