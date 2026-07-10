/**
 * Main renderer app — ties orb, voice, memory, and commands together.
 */

// Inline command logic (shared/commands.js is Node-only; mirrored here for renderer)
function normalize(text) {
  return text.toLowerCase().replace(/[^\w\s']/g, " ").replace(/\s+/g, " ").trim();
}

function processCommand(utterance, memory = {}) {
  const text = normalize(utterance);
  if (!text) return null;

  const userName = memory.userName || null;
  const now = new Date();

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

  if (["what is my name", "what's my name", "do you know my name", "who am i"].some((p) => text.includes(p))) {
    if (userName) return { response: `Your name is ${userName}.` };
    return {
      response:
        "I don't have your name yet. You can tell me by saying my name is, followed by your name.",
    };
  }

  if (["what time", "what's the time", "tell me the time", "current time"].some((p) => text.includes(p))) {
    const t = now.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit", hour12: true });
    return { response: `It's ${t}.` };
  }

  if (
    [
      "what date",
      "what is the date",
      "what's the date",
      "what day is it",
      "today's date",
      "tell me the date",
    ].some((p) => text.includes(p))
  ) {
    const d = now.toLocaleDateString(undefined, {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
    return { response: `Today is ${d}.` };
  }

  if (
    ["hello", "hi jarvis", "hey jarvis", "good morning", "good afternoon", "good evening", "how are you"].some(
      (p) => text.includes(p)
    )
  ) {
    const prefix = userName ? `Hello, ${userName}. ` : "Hello. ";
    return { response: `${prefix}I'm here and ready to help.` };
  }

  if (["clear memory", "forget everything", "reset memory", "clear my memory"].some((p) => text.includes(p))) {
    return { response: "Memory cleared. Starting fresh.", action: { type: "clearMemory" } };
  }

  const correction =
    text.match(/(?:no|actually|that's wrong|you're wrong|not .+ but)\s+(.+)/i) ||
    text.match(/i meant\s+(.+)/i);
  if (correction) {
    return {
      response: "Noted. I'll remember that correction.",
      action: { type: "addCorrection", text: utterance.trim() },
    };
  }

  if (["what can you do", "help", "your capabilities"].some((p) => text.includes(p))) {
    return {
      response:
        "I can tell you the time and date, remember your name, greet you, and keep our conversation history. More capabilities are on the way.",
    };
  }

  return null;
}

function pickGreeting(lastGreeting) {
  const hour = new Date().getHours();
  let pool;
  if (hour >= 5 && hour < 12) {
    pool = [
      "Good morning. Jarvis online and ready.",
      "Morning. Systems are up — what can I do for you?",
      "Good morning. All quiet on my end. How may I help?",
    ];
  } else if (hour >= 12 && hour < 17) {
    pool = [
      "Good afternoon. Jarvis here — ready when you are.",
      "Afternoon. Everything's running smoothly. What do you need?",
      "Good afternoon. Standing by.",
    ];
  } else if (hour >= 17 && hour < 22) {
    pool = [
      "Good evening. Jarvis at your service.",
      "Evening. All systems nominal. What can I do?",
      "Good evening. Ready when you are.",
    ];
  } else {
    pool = [
      "Working late? Jarvis is here.",
      "Still up? Jarvis online and listening.",
      "Night shift mode. Jarvis ready.",
    ];
  }
  const candidates = lastGreeting ? pool.filter((g) => g !== lastGreeting) : pool;
  const list = candidates.length ? candidates : pool;
  return list[Math.floor(Math.random() * list.length)];
}

async function main() {
  const canvas = document.getElementById("orb-canvas");
  const micBtn = document.getElementById("mic-toggle");
  const micOn = document.getElementById("mic-icon-on");
  const micOff = document.getElementById("mic-icon-off");
  const statusEl = document.getElementById("status");

  const orb = new OrbRenderer(canvas);
  orb.start();

  let memory = {
    userName: null,
    lastGreeting: null,
    corrections: [],
    history: [],
    memoryPath: null,
  };

  const setStatus = (msg) => {
    statusEl.textContent = msg;
  };

  const loadMemory = async () => {
    if (!window.jarvis?.memory) {
      setStatus("Memory bridge unavailable.");
      return;
    }
    const result = await window.jarvis.memory.load();
    if (result.ok) {
      memory = result.data;
    } else {
      setStatus(`Memory load failed: ${result.error}`);
    }
  };

  const saveHistory = async (role, text) => {
    if (!window.jarvis?.memory) return;
    await window.jarvis.memory.addHistory({ role, text });
  };

  const applyAction = async (action) => {
    if (!action || !window.jarvis?.memory) return;
    switch (action.type) {
      case "setName":
        await window.jarvis.memory.setName(action.name);
        memory.userName = action.name;
        break;
      case "clearMemory":
        await window.jarvis.memory.clear();
        memory = { userName: null, lastGreeting: null, corrections: [], history: [] };
        break;
      case "addCorrection":
        await window.jarvis.memory.addCorrection(action.text);
        memory.corrections = [...(memory.corrections || []), action.text];
        break;
      default:
        break;
    }
  };

  const voice = new VoiceController({
    onStateChange: (state) => {
      if (state === "listening") orb.setState(ORB_STATES.LISTENING);
      else if (state === "speaking") orb.setState(ORB_STATES.SPEAKING);
      else orb.setState(ORB_STATES.IDLE);
    },
    onTranscript: async (text) => {
      await handleUserUtterance(text);
    },
    onError: (msg) => {
      setStatus(msg);
      speakSafe(`I'm afraid I hit a snag: ${msg}`);
    },
  });

  const speakSafe = async (text) => {
    try {
      await voice.speak(text, {
        onPulse: (amp) => orb.setSpeakAmplitude(amp),
      });
    } catch (err) {
      console.error("[app] speak failed:", err);
      setStatus(`Speech output failed: ${err.message}`);
      orb.setState(ORB_STATES.IDLE);
    }
  };

  const handleUserUtterance = async (text) => {
    orb.setState(ORB_STATES.PROCESSING);
    await saveHistory("user", text);

    const ack = "Already on it.";
    await speakSafe(ack);

    const result = processCommand(text, memory);
    let response;
    if (result) {
      await applyAction(result.action);
      response = result.response;
    } else {
      response =
        "I'm not sure how to help with that yet. You can ask for the time, date, or tell me your name.";
    }

    await saveHistory("assistant", response);
    await speakSafe(response);
  };

  micBtn.addEventListener("click", () => {
    const nextMuted = !voice.muted;
    voice.setMuted(nextMuted);
    micBtn.classList.toggle("muted", nextMuted);
    micBtn.setAttribute("aria-label", nextMuted ? "Unmute microphone" : "Mute microphone");
    micBtn.title = nextMuted ? "Unmute microphone" : "Mute microphone";
    micOn.classList.toggle("hidden", nextMuted);
    micOff.classList.toggle("hidden", !nextMuted);
  });

  await loadMemory();

  const greeting = pickGreeting(memory.lastGreeting);
  if (window.jarvis?.memory) {
    await window.jarvis.memory.setLastGreeting(greeting);
  }
  memory.lastGreeting = greeting;

  setTimeout(async () => {
    await speakSafe(greeting);
    voice.startListening();
  }, 600);

  // Dev helper: cycle orb states with number keys 1-4
  if (typeof process !== "undefined" && process.env?.JARVIS_DEV) {
    window.addEventListener("keydown", (e) => {
      const map = { 1: ORB_STATES.IDLE, 2: ORB_STATES.LISTENING, 3: ORB_STATES.PROCESSING, 4: ORB_STATES.SPEAKING };
      if (map[e.key]) orb.setState(map[e.key]);
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  main().catch((err) => console.error("[app] startup failed:", err));
});

// Export for automated testing
window.__jarvis = { processCommand, pickGreeting };
