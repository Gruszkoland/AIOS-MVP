# ADRION 369 - Persona Agent Files

This directory contains individual persona definitions that can be loaded dynamically into Aider or other AI systems.

Each file represents one of the **nine personas** in the multi-dimensional AI system:

- **librarian.agent.md** - Historical continuity & knowledge archiving
- **sap.agent.md** - Strategic action planning
- **auditor.agent.md** - Quality assurance & non-regression
- **sentinel.agent.md** - Error detection & rapid response
- **architect.agent.md** - Design authority & unified design
- **healer.agent.md** - Optimization & continuous improvement
- **amplifier.agent.md** - Public narrative guardian & LinkedIn publisher
- **boosterlever.agent.md** - AI content generation & lead interaction
- **chronos.agent.md** - Temporal master & cycle orchestration

## Usage

### With Aider
```bash
aider --instructions librarian.agent.md
```

### With Custom Scripts
```python
with open('persona-agents/librarian.agent.md') as f:
    librarian_prompt = f.read()
```

### With Other AI Systems
These files are formatted as markdown with YAML frontmatter for compatibility with various AI systems (VS Code Copilot, Claude, GPT, etc.).

## YAML Frontmatter Format

Each agent file contains:
```yaml
---
role: "LIBRARIAN"
law: 1
person_type: "knowledge_archiver"
trigger_phrase: "@librarian"
---
```

Followed by detailed system prompt and instructions.
