/**
 * Phase 1 keyword-based command handling.
 * Returns { response, action? } or null if no match.
 */

function normalize(text) {
  return text.toLowerCase().replace(/[^\w\s']/g, " ").replace(/\s+/g, " ").trim();
}

function matchAny(text, patterns) {
  return patterns.some((p) => (typeof p === "string" ? text.includes(p) : p.test(text)));
}

function formatTime(date) {
  return date.toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

function formatDate(date) {
  return date.toLocaleDateString(undefined, {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

/**
 * Process user utterance against memory context.
 * @param {string} utterance
 * @param {{ userName?: string|null, corrections?: string[] }} memory
 */
function processCommand(utterance, memory = {}) {
  const text = normalize(utterance);
  if (!text) return null;

  const userName = memory.userName || null;
  const now = new Date();

  // Remember name
  const nameRemember =
    text.match(/(?:my name is|call me|i am|i'm)\s+([a-z][a-z\s'-]{0,40})/i) ||
    text.match(/remember (?:that )?my name is\s+([a-z][a-z\s'-]{0,40})/i);
  if (nameRemember) {
    const name = nameRemember[1].trim().replace(/\b\w/g, (c) => c.toUpperCase());
    return {
      response: `Understood. I'll call you ${name} from now on.`,
      action: { type: "setName", name },
    };
  }

  // Recall name
  if (matchAny(text, ["what is my name", "what's my name", "do you know my name", "who am i"])) {
    if (userName) {
      return { response: `Your name is ${userName}.` };
    }
    return { response: "I don't have your name yet. You can tell me by saying my name is, followed by your name." };
  }

  // Time
  if (matchAny(text, ["what time", "what's the time", "tell me the time", "current time"])) {
    return { response: `It's ${formatTime(now)}.` };
  }

  // Date
  if (
    matchAny(text, [
      "what date",
      "what is the date",
      "what's the date",
      "what day is it",
      "today's date",
      "tell me the date",
    ])
  ) {
    return { response: `Today is ${formatDate(now)}.` };
  }

  // Greeting
  if (matchAny(text, ["hello", "hi jarvis", "hey jarvis", "good morning", "good afternoon", "good evening", "how are you"])) {
    const prefix = userName ? `Hello, ${userName}. ` : "Hello. ";
    return { response: `${prefix}I'm here and ready to help.` };
  }

  // Clear memory
  if (matchAny(text, ["clear memory", "forget everything", "reset memory", "clear my memory"])) {
    return {
      response: "Memory cleared. Starting fresh.",
      action: { type: "clearMemory" },
    };
  }

  // Corrections — store so we don't repeat mistakes
  const correction =
    text.match(/(?:no|actually|that's wrong|you're wrong|not .+ but)\s+(.+)/i) ||
    text.match(/i meant\s+(.+)/i);
  if (correction) {
    return {
      response: "Noted. I'll remember that correction.",
      action: { type: "addCorrection", text: utterance.trim() },
    };
  }

  // Help
  if (matchAny(text, ["what can you do", "help", "your capabilities"])) {
    return {
      response:
        "I can tell you the time and date, remember your name, greet you, and keep our conversation history. More capabilities are on the way.",
    };
  }

  return null;
}

module.exports = { processCommand, normalize, formatTime, formatDate };
