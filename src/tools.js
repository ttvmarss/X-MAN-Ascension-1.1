// Anthropic tool-use definitions for JARVIS actions.
// Clean structured calls instead of regex-parsing response text.

export const JARVIS_TOOLS = [
  {
    name: 'remember',
    description:
      "Save a fact, preference, or piece of information for future sessions. " +
      "Use when the user says 'remember', 'note that', 'I prefer', etc.",
    input_schema: {
      type: 'object',
      properties: {
        fact: { type: 'string', description: 'The fact or preference to remember.' },
        category: {
          type: 'string',
          description: 'Category: preference, fact, decision, contact, general.',
        },
      },
      required: ['fact'],
    },
  },
  {
    name: 'recall',
    description:
      'Search past memories for relevant facts. Use when the user asks what JARVIS remembers, ' +
      'or when context from prior sessions would help.',
    input_schema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Search query.' },
      },
      required: ['query'],
    },
  },
  {
    name: 'add_task',
    description: "Add a task or to-do item to JARVIS's tracker.",
    input_schema: {
      type: 'object',
      properties: {
        title: { type: 'string', description: 'Task title.' },
        priority: {
          type: 'integer',
          minimum: 1,
          maximum: 5,
          description: 'Priority 1 (low) to 5 (urgent). Default 3.',
        },
        due_in_hours: { type: 'number', description: 'Optional hours from now until due.' },
      },
      required: ['title'],
    },
  },
  {
    name: 'list_tasks',
    description: 'List pending tasks. Use when the user asks about tasks/to-dos/pending.',
    input_schema: { type: 'object', properties: {} },
  },
  {
    name: 'browse_web',
    description: 'Open a URL or search query in the default browser.',
    input_schema: {
      type: 'object',
      properties: {
        query_or_url: {
          type: 'string',
          description: 'Either a full URL (https://...) or a search query.',
        },
      },
      required: ['query_or_url'],
    },
  },
  {
    name: 'open_app',
    description:
      "Launch a Windows application by name (e.g. 'notepad', 'calculator', 'spotify').",
    input_schema: {
      type: 'object',
      properties: {
        app: { type: 'string', description: 'Application name or executable.' },
      },
      required: ['app'],
    },
  },
  {
    name: 'build_project',
    description:
      'Spawn a Claude Code session to build a software project. ' +
      'Use when the user asks JARVIS to build, create, code, or develop something.',
    input_schema: {
      type: 'object',
      properties: {
        description: { type: 'string', description: 'Detailed description of what to build.' },
        project_name: {
          type: 'string',
          description: 'Optional short project name (no spaces).',
        },
      },
      required: ['description'],
    },
  },
  {
    name: 'save_note',
    description: "Save a longer note to the user's notes folder.",
    input_schema: {
      type: 'object',
      properties: {
        content: { type: 'string', description: 'Note content.' },
        title: { type: 'string', description: 'Optional note title.' },
      },
      required: ['content'],
    },
  },
  {
    name: 'get_time',
    description: 'Get the current date and time.',
    input_schema: { type: 'object', properties: {} },
  },
]
