# Where the JARVIS architecture decisions now live

The research in this folder (`ARCHITECTURE.md`, `CAPABILITIES.md`,
`REPO-GAP.md`, `BUILD-ROADMAP.md`, `TOOLING.md`) fed into a canonical,
decision-level architecture blueprint written directly against the actual
`ttvmarss/jarvis` codebase (not just the public ManinaLabs research):

**`ttvmarss/jarvis` → `docs/SYSTEM_ARCHITECTURE.md`
(branch `claude/code-system-architecture-lhzwtt`)**

That document:

- Picks one canonical stack (FastAPI backend + Electron/React/Three.js
  desktop shell, Claude API primary / Ollama fallback) out of the six
  competing stacks tried across `ttvmarss/jarvis` PRs #5–#11, and says why.
- Defines repo structure, process topology, the conversational-turn data
  flow, the event bus (WS transport layer + internal agent notify layer),
  agent roles, the tool permission-tier model, the voice pipeline, the
  PC-control layer, a new Unity client integration, and the security trust
  boundaries.
- Is meant to stop new work from restarting the project on yet another
  stack — new PRs against `jarvis` should build on it, not around it.

The research docs in this folder remain useful as background (public
ManinaLabs Blueprint summary, capability/tier comparisons, tooling install
notes) and are unchanged. Treat `SYSTEM_ARCHITECTURE.md` in the `jarvis`
repo as the current source of truth for implementation decisions; treat
this folder as the research that led there.
