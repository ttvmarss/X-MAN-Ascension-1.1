# Changelog

## [0.1.0] - Phase 1 Foundation

### Added
- Electron app shell with main / renderer / shared structure
- Animated "Orb" UI with idle, listening, processing, and speaking states
- Continuous voice input via Web Speech API (SpeechRecognition)
- Voice output via Web Speech API (SpeechSynthesis), calm measured tone
- Mic mute/unmute toggle
- Local persistent memory (user name + conversation history) saved to disk
- Sensitive fields encrypted at rest (user name)
- Basic command handling: time, date, greeting, name remember/recall
- Varied time-of-day-aware launch greetings
- Windows portable executable packaging via electron-builder
