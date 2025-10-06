# Setup Instructions

## 1. Create Project Structure

```bash
mkdir notion-knowledge-distiller
cd notion-knowledge-distiller
mkdir src
```

Copy the files from the artifacts into this structure:
```
notion-knowledge-distiller/
├── src/
│   ├── __init__.py
│   └── server.py
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

## 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -e .
```

## 3. Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Notion API key
# Get your key from: https://www.notion.so/my-integrations
```

Your `.env` should look like:
```
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_PARENT_PAGE_ID=  # Optional for now
```

## 4. Test the Server

```bash
# Run the server
python src/server.py
```

The server should start and wait for input (it communicates via stdio).

## 5. Configure Claude Desktop

Add this to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "notion-distiller": {
      "command": "/FULL/PATH/TO/venv/bin/python",
      "args": [
        "/FULL/PATH/TO/notion-knowledge-distiller/src/server.py"
      ]
    }
  }
}
```

**Important**: Replace `/FULL/PATH/TO/` with the actual absolute paths on your system.

## 6. Restart Claude Desktop

Restart Claude Desktop completely (quit and reopen).

## 7. Test It!

### Basic Test
In Claude Desktop, try saying:
```
Use the ping tool to test if the Notion distiller server is working
```

You should see a pong response with your configuration status!

### Create Your First Notion Page
Once the ping test works, try:
```
Create notes for this conversation in Notion
```

Claude will:
1. Analyze the current conversation
2. Extract key insights, decisions, and action items
3. Create a structured Notion page at your workspace root
4. Give you the URL to the new page!

---

## Troubleshooting

### Server not appearing in Claude Desktop
- Check the config file path and JSON syntax
- Make sure you used absolute paths (not relative)
- Check Claude Desktop logs (Help → View Logs)

### Python not found
- Use the full path to your venv Python: `/path/to/venv/bin/python`
- On Windows: `C:\path\to\venv\Scripts\python.exe`

### Dependencies not installed
- Make sure you activated the venv before installing
- Run `pip install -e .` again