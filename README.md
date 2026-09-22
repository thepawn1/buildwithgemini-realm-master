# RealmMaster: DM Companion

RealmMaster is an omniscient tabletop RPG companion, rule keeper, visual artificer, and campaign manager built using Google's Agent Development Kit (ADK).

## Features

- **Rich UI (A2UI)**: Natively renders character profiles, quests, dice rolls, and loot tables as interactive UI cards in the chat.
- **Long-Term Memory**: Uses a Vertex AI Memory Bank to remember character profiles, active inventories, party members, and ongoing campaign quest notes across sessions.
- **Rulebook Grounding (RAG)**: Grounded on the Dungeon Master's Guide via Vertex AI RAG Engine for accurate rule lookups.
- **Code Execution Sandbox**: Securely runs Python code for complex dice math and tabletop simulations.

## Agent Tools

- **5e SRD Lookup**: Queries a REST compendium to fetch accurate stats and rules.
- **Scene & Portrait Generation**: Takes a visual prompt, generates an illustration using Vertex AI Imagen 3, and uploads the image to a public Cloud Storage bucket.
- **Dynamic Encounter Loot**: Queries a Firestore compendium to pick appropriate rarity rewards based on encounter Challenge Rating (CR) and drops loot directly into the active inventory.

## Custom Frontend

The project includes a custom FastAPI proxy and a themed chat UI built with HTML/JS/CSS.
- **Fantasy Theming**: "Lord of the Rings" style aesthetic with parchment backgrounds, elven green accents, and ornate borders.
- **Rich Text & Media**: Full Markdown support, animated 3D dice rolls, and fullscreen click-to-expand image modals for generated art.
- **Quick Prompts**: One-click prompt buttons to easily roll dice, check inventory, or generate portraits.

## How to Run Locally

### 1. Start the Agent
Use the Antigravity CLI to run the agent locally:
```bash
uv run adk web --port 8081
```

### 2. Start the Frontend
In a separate terminal, start the FastAPI proxy:
```bash
cd frontend
python -m venv .venv-frontend
source .venv-frontend/bin/activate
pip install -r requirements.txt
export AGENT_ENGINE_RESOURCE_NAME="<your-agent-engine-resource-name>"
export AGENT_DIRECTORY="app"
export PORT=8080
python main.py
```
Then navigate to `http://localhost:8080` in your browser.
