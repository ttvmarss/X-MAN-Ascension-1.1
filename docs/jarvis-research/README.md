# ManinaLabs J.A.R.V.I.S. — Research Pack

Research compiled from the public site [jarvis.driftworksstudios.com](https://jarvis.driftworksstudios.com) (ManinaLabs / DriftWorks Studios, Sam Manina), the free Blueprint preview PDF, and related public materials.

**Important:** ManinaLabs sells copyrighted educational kits. This pack documents **publicly disclosed** architecture and tooling so we can build our **own** assistant. It does **not** redistribute paid kit source, prompts, or the full 119-page Blueprint.

| Doc | Purpose |
|-----|---------|
| [SITE-AUDIT.md](./SITE-AUDIT.md) | Full crawl of the marketing site, pages, APIs, demos |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Target system architecture (from free Blueprint Ch.1) |
| [TOOLING.md](./TOOLING.md) | Every tool / service / dependency to acquire |
| [CAPABILITIES.md](./CAPABILITIES.md) | Feature matrix vs kit tiers |
| [BUILD-ROADMAP.md](./BUILD-ROADMAP.md) | Phased build plan matching their public methodology |
| [REPO-GAP.md](./REPO-GAP.md) | How existing X-MAN / JARVIS branches compare |

## One-line summary

J.A.R.V.I.S. here means a **local Windows Python assistant**: Flask + Socket.IO backend, Claude (cloud brain), Whisper STT, Coqui XTTS voice cloning, Chroma + SQLite + markdown memory, ~50 tools, holographic orb UI — built with Claude Code.
