/**
 * Varied launch greetings — time-of-day aware, never the same line twice in a row.
 */

const MORNING = [
  "Good morning. Jarvis online and ready.",
  "Morning. Systems are up — what can I do for you?",
  "Good morning. All quiet on my end. How may I help?",
  "Rise and shine. Jarvis at your service.",
];

const AFTERNOON = [
  "Good afternoon. Jarvis here — ready when you are.",
  "Afternoon. Everything's running smoothly. What do you need?",
  "Good afternoon. Standing by.",
  "Hello. Jarvis online — how can I assist?",
];

const EVENING = [
  "Good evening. Jarvis at your service.",
  "Evening. All systems nominal. What can I do?",
  "Good evening. Ready when you are.",
  "Hello. Jarvis online for the evening.",
];

const NIGHT = [
  "Working late? Jarvis is here.",
  "Good evening — or good night, depending on your schedule. How can I help?",
  "Still up? Jarvis online and listening.",
  "Night shift mode. Jarvis ready.",
];

function getTimeBucket(hour) {
  if (hour >= 5 && hour < 12) return "morning";
  if (hour >= 12 && hour < 17) return "afternoon";
  if (hour >= 17 && hour < 22) return "evening";
  return "night";
}

function bucketGreetings(bucket) {
  switch (bucket) {
    case "morning": return MORNING;
    case "afternoon": return AFTERNOON;
    case "evening": return EVENING;
    default: return NIGHT;
  }
}

/**
 * Pick a greeting different from lastGreeting when possible.
 */
function pickGreeting(lastGreeting, date = new Date()) {
  const bucket = getTimeBucket(date.getHours());
  const pool = bucketGreetings(bucket);
  const candidates = lastGreeting
    ? pool.filter((g) => g !== lastGreeting)
    : pool;
  const list = candidates.length > 0 ? candidates : pool;
  return list[Math.floor(Math.random() * list.length)];
}

module.exports = { pickGreeting, getTimeBucket };
