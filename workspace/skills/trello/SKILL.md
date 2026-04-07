---
name: trello
description: Управление досками, списками и карточками Trello через Trello REST API.
homepage: https://developer.atlassian.com/cloud/trello/rest/
metadata:
  {
    "openclaw":
      {
        "emoji": "📋",
        "requires": { "bins": ["python3"] },
        "install":
          [
            {
              "id": "brew",
              "kind": "brew",
              "formula": "python",
              "bins": ["python3"],
              "label": "Install Python (brew)",
            },
          ],
      },
  }
---

# Trello Skill

Manage Trello boards, lists, and cards directly from OpenClaw.

## Setup

1. **Create a Power-Up** (if you don't have one):
   - Go to https://trello.com/power-ups/admin
   - Click "Create a Power-Up" (or select an existing one)
   - Give it a name (e.g., "Nanobot Trello Integration")

2. **Get your API key**:
   - In the Power-Up admin, go to the **API Key** tab
   - Click **Generate a new API Key** (if not already generated)
   - Copy the API key

3. **Generate a token via authorization link**:
   - Construct the authorize URL with your API key, desired scope and expiration. Example for read-only access valid for 30 days:
     ```
     https://trello.com/1/authorize?expiration=30days&scope=read&response_type=token&key=YOUR_API_KEY
     ```
   - Replace `YOUR_API_KEY` with your actual API key
   - **Open this URL in a browser** — this is the critical step that was missing before
   - Log in if needed, and click **Allow**
   - You will be redirected to a page showing your token. Copy it.

   **Scope options** (comma-separated if multiple):
   - `read` — read boards, lists, cards, etc.
   - `write` — create/modify boards, lists, cards, etc.
   - `account` — read member email, modify member info, mark notifications read

   **Expiration options**: `1hour`, `1day`, `30days`, `never`

4. **Save credentials to `trello.json`** in this skill's directory:
   Create file `skills/trello/trello.json` with content:
   ```json
   {
     "api_key": "YOUR_API_KEY",
     "token": "YOUR_TOKEN"
   }
   ```
   Replace with your actual values.

**Important**: 
- The API key can be public, but the token is secret and grants full access to your Trello account. Never share it.
- The `trello.json` file should **not** be committed to version control. It is already in `.gitignore` of the skill.
- If you get "invalid token" errors, ensure you completed step 3 (opened the authorization link and clicked Allow).

## Usage

All commands are executed via the Python CLI that handles authentication and API calls.

### List boards

```bash
python trello_cli.py list-boards
```

### List lists in a board

```bash
python trello_cli.py list-lists <board_id>
```

### List cards in a list

```bash
python trello_cli.py list-cards <list_id>
```

### Create a card

```bash
python trello_cli.py create-card <list_id> "Card Title" ["Card description"]
```

### Move a card to another list

```bash
python trello_cli.py move-card <card_id> <new_list_id>
```

### Add a comment to a card

```bash
python trello_cli.py add-comment <card_id> "Your comment here"
```

### Archive a card

```bash
python trello_cli.py archive-card <card_id>
```

## Notes

- Board/List/Card IDs can be found in the Trello URL or via the list commands
- The API key and token provide full access to your Trello account - keep them secret!
- Rate limits: 300 requests per 10 seconds per API key; 100 requests per 10 seconds per token; `/1/members` endpoints are limited to 100 requests per 900 seconds
- The CLI is written in Python and works on Windows, Linux, and macOS without external dependencies beyond Python standard library.
- Paths with Unicode (including Cyrillic) are fully supported.

## Examples

```bash
# Get all boards
python trello_cli.py list-boards

# Find a specific board by name (pipe to grep/findstr)
python trello_cli.py list-boards | findstr "Work"  # Windows
python trello_cli.py list-boards | grep "Work"     # Linux/WSL

# Get all cards on a board (requires board ID, then get lists, then cards)
python trello_cli.py list-lists <board_id>
python trello_cli.py list-cards <list_id>
```
