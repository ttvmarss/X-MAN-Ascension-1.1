/**
 * Persistent local memory store.
 * Saves to a JSON file on disk; encrypts sensitive fields at rest.
 */

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const ALGORITHM = "aes-256-gcm";
const IV_LENGTH = 12;
const TAG_LENGTH = 16;
const KEY_LENGTH = 32;

const DEFAULT_MEMORY = {
  version: 1,
  userName: null,
  lastGreeting: null,
  corrections: [],
  history: [],
  createdAt: null,
  updatedAt: null,
};

function deriveKey(userDataPath) {
  // Machine-local key derived from app data path — not military-grade,
  // but prevents casual plaintext reads of the name on disk.
  return crypto
    .createHash("sha256")
    .update(`jarvis-v1:${userDataPath}`)
    .digest();
}

function encrypt(plaintext, key) {
  const iv = crypto.randomBytes(IV_LENGTH);
  const cipher = crypto.createCipheriv(ALGORITHM, key.slice(0, KEY_LENGTH), iv);
  const encrypted = Buffer.concat([
    cipher.update(plaintext, "utf8"),
    cipher.final(),
  ]);
  const tag = cipher.getAuthTag();
  return Buffer.concat([iv, tag, encrypted]).toString("base64");
}

function decrypt(encoded, key) {
  const buf = Buffer.from(encoded, "base64");
  const iv = buf.subarray(0, IV_LENGTH);
  const tag = buf.subarray(IV_LENGTH, IV_LENGTH + TAG_LENGTH);
  const data = buf.subarray(IV_LENGTH + TAG_LENGTH);
  const decipher = crypto.createDecipheriv(ALGORITHM, key.slice(0, KEY_LENGTH), iv);
  decipher.setAuthTag(tag);
  return Buffer.concat([decipher.update(data), decipher.final()]).toString("utf8");
}

class MemoryStore {
  constructor(userDataPath) {
    this.filePath = path.join(userDataPath, "jarvis-memory.json");
    this.key = deriveKey(userDataPath);
    this.data = { ...DEFAULT_MEMORY };
  }

  load() {
    try {
      if (!fs.existsSync(this.filePath)) {
        this.data = {
          ...DEFAULT_MEMORY,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        this.save();
        return this.getPublic();
      }

      const raw = JSON.parse(fs.readFileSync(this.filePath, "utf8"));
      let userName = null;
      if (raw.userNameEncrypted) {
        try {
          userName = decrypt(raw.userNameEncrypted, this.key);
        } catch {
          console.error("[memory] Failed to decrypt user name");
        }
      } else if (raw.userName) {
        userName = raw.userName;
      }

      this.data = {
        version: raw.version ?? 1,
        userName,
        lastGreeting: raw.lastGreeting ?? null,
        corrections: Array.isArray(raw.corrections) ? raw.corrections : [],
        history: Array.isArray(raw.history) ? raw.history.slice(-200) : [],
        createdAt: raw.createdAt ?? new Date().toISOString(),
        updatedAt: raw.updatedAt ?? new Date().toISOString(),
      };
      return this.getPublic();
    } catch (err) {
      console.error("[memory] Load failed:", err.message);
      return this.getPublic();
    }
  }

  save() {
    try {
      const dir = path.dirname(this.filePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      const payload = {
        version: this.data.version,
        userNameEncrypted: this.data.userName
          ? encrypt(this.data.userName, this.key)
          : null,
        lastGreeting: this.data.lastGreeting,
        corrections: this.data.corrections.slice(-50),
        history: this.data.history.slice(-200),
        createdAt: this.data.createdAt,
        updatedAt: new Date().toISOString(),
      };

      fs.writeFileSync(this.filePath, JSON.stringify(payload, null, 2), "utf8");
      this.data.updatedAt = payload.updatedAt;
    } catch (err) {
      console.error("[memory] Save failed:", err.message);
      throw err;
    }
  }

  getPublic() {
    return {
      userName: this.data.userName,
      lastGreeting: this.data.lastGreeting,
      corrections: [...this.data.corrections],
      history: [...this.data.history],
      memoryPath: this.filePath,
    };
  }

  setName(name) {
    this.data.userName = name;
    this.save();
    return this.getPublic();
  }

  setLastGreeting(greeting) {
    this.data.lastGreeting = greeting;
    this.save();
    return this.getPublic();
  }

  addCorrection(text) {
    this.data.corrections.push({ text, at: new Date().toISOString() });
    this.save();
    return this.getPublic();
  }

  addHistory(entry) {
    this.data.history.push({
      ...entry,
      at: new Date().toISOString(),
    });
    this.save();
    return this.getPublic();
  }

  clear() {
    const createdAt = this.data.createdAt;
    this.data = {
      ...DEFAULT_MEMORY,
      createdAt: createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.save();
    return this.getPublic();
  }
}

module.exports = { MemoryStore };
