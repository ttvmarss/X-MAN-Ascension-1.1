/**
 * Headless tests for Phase 1 logic — memory store and commands.
 * Run: node scripts/test-phase1.js
 */

const fs = require("fs");
const path = require("path");
const os = require("os");
const { MemoryStore } = require("../main/memory-store");
const { processCommand } = require("../shared/commands");
const { pickGreeting } = require("../shared/greetings");

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) {
    passed++;
    console.log(`  ✓ ${msg}`);
  } else {
    failed++;
    console.error(`  ✗ ${msg}`);
  }
}

console.log("\n=== Command tests ===\n");

const timeResult = processCommand("hey jarvis what time is it", {});
assert(timeResult && timeResult.response.includes("It's"), "responds to time query");

const dateResult = processCommand("what is the date today", {});
assert(dateResult && dateResult.response.includes("Today is"), "responds to date query");

const nameResult = processCommand("my name is Alice", {});
assert(nameResult?.action?.type === "setName" && nameResult.action.name === "Alice", "extracts name");

const recall = processCommand("what is my name", { userName: "Alice" });
assert(recall?.response.includes("Alice"), "recalls name");

const unknown = processCommand("open the pod bay doors", {});
assert(unknown === null, "returns null for unknown commands");

console.log("\n=== Greeting tests ===\n");
const g1 = pickGreeting(null);
const g2 = pickGreeting(g1);
assert(typeof g1 === "string" && g1.length > 10, "picks a greeting");
assert(g1 !== g2 || g2, "greeting rotation works");

console.log("\n=== Memory store tests ===\n");
const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "jarvis-test-"));
const store = new MemoryStore(tmpDir);
store.load();
assert(fs.existsSync(path.join(tmpDir, "jarvis-memory.json")), "creates memory file on disk");

store.setName("Bob");
const pub = store.getPublic();
assert(pub.userName === "Bob", "stores user name");

const raw = JSON.parse(fs.readFileSync(path.join(tmpDir, "jarvis-memory.json"), "utf8"));
assert(raw.userNameEncrypted && !raw.userName, "name is encrypted at rest, not plaintext");

store.addHistory({ role: "user", text: "hello" });
store.addHistory({ role: "assistant", text: "hi" });
assert(store.getPublic().history.length === 2, "persists history");

const store2 = new MemoryStore(tmpDir);
store2.load();
assert(store2.getPublic().userName === "Bob", "memory survives reload");
assert(store2.getPublic().history.length === 2, "history survives reload");

store2.clear();
assert(store2.getPublic().userName === null, "clear memory works");

fs.rmSync(tmpDir, { recursive: true, force: true });

console.log(`\n=== Results: ${passed} passed, ${failed} failed ===\n`);
process.exit(failed > 0 ? 1 : 0);
