# Miro SVG Downloader

A Python tool to bulk-download SVG files from Miro boards. Perfect for extracting SVG icons and graphics that can be used as custom stencils in diagramming tools by uploading them to "My Shapes" libraries.

## Features

- **Bulk download**: Extract all SVG files from a Miro board in one command
- **Smart detection**: Automatically scans multiple item types (images, documents, shapes, etc.) to find SVGs
- **Original filenames**: Preserves original filenames when available, with automatic conflict resolution
- **Rate limiting**: Respects Miro's API rate limits (≤4 requests/second)
- **Multiple formats**: Tries different URL formats to maximize SVG recovery
- **Progress tracking**: Shows detailed progress and statistics

## Requirements

- Python 3.7 or higher
- `requests` library

## Installation

1. **Clone or download** this repository

2. **Install dependencies**:

   ```bash
   pip install requests
   ```

3. **Make the script executable** (optional):

   ```bash
   chmod +x miro-svg-dl.py
   ```

## Getting Miro Credentials

### 1. Get Your Board ID

The Board ID is the alphanumeric identifier in your Miro board URL:

```
https://miro.com/app/board/uXjVKMeNpXI=/
                            ^^^^^^^^^^^
                            This is your Board ID
```

**Example**: If your board URL is `https://miro.com/app/board/uXjVKMeNpXI=/`, then your Board ID is `uXjVKMeNpXI=`

### 2. Get Your Access Token

You need a Miro access token with `boards:read` scope. You have two options:

#### Option A: Personal Access Token (Recommended for personal use)

1. Go to [Miro Developer Portal](https://developers.miro.com/)
2. Sign in with your Miro account
3. Click **"Your apps"** in the top navigation
4. Click **"Create new app"**
5. Fill in the required fields:
   - **App name**: `SVG Downloader` (or any name you prefer)
   - **Description**: `Tool for downloading SVGs from boards`
6. After creating the app, go to the **"Permissions"** tab
7. Enable the `boards:read` scope
8. Go to the **"Install app and get OAuth token"** tab
9. Click **"Install app"** and authorize it for your team
10. Copy the generated **OAuth token**

#### Option B: OAuth Flow (For production applications)

If you're building this into an application, follow the [Miro OAuth documentation](https://developers.miro.com/docs/getting-started-with-oauth) to implement the full OAuth flow.

## Usage

### Basic Usage

```bash
python miro-svg-dl.py -b <BOARD_ID> -t <ACCESS_TOKEN>
```

### Example

```bash
python miro-svg-dl.py -b uXjVKMeNpXI -t "your_access_token_here"
```

### All Options

```bash
python miro-svg-dl.py [OPTIONS]

Required Arguments:
  -b, --board BOARD_ID     Miro board ID (from the board URL)
  -t, --token ACCESS_TOKEN Your Miro access token

Optional Arguments:
  -o, --out DIR           Output directory (default: ./svgs)
  --include-docs          Also scan document items for SVGs
  --quiet                 Suppress detailed progress messages

Examples:
  # Download to custom directory
  python miro-svg-dl.py -b uXjVKMeNpXI -t "token" -o ~/my-icons

  # Include document items and run quietly
  python miro-svg-dl.py -b uXjVKMeNpXI -t "token" --include-docs --quiet

  # Full verbose output (default)
  python miro-svg-dl.py -b uXjVKMeNpXI -t "token" -o ./downloaded-svgs
```

## How It Works

1. **Scans multiple item types**: The script examines images, documents, shapes, sticky notes, text, frames, and app cards
2. **Tests multiple URL formats**: For each potential SVG, it tries different URL parameters to access the raw file
3. **Validates SVG content**: Checks content-type headers and file content to confirm SVG format
4. **Preserves filenames**: Uses original filenames when available, falls back to item IDs
5. **Handles conflicts**: Automatically appends numbers to resolve filename conflicts
6. **Rate limiting**: Includes delays to respect Miro's API limits

## Output

The script creates a directory structure like this:

```
svgs/                          # Output directory
├── icon-arrow.svg             # Original filename preserved
├── icon-user_1.svg            # Conflict resolved with counter
├── uXjVKMeNpXI_item_123.svg   # Generated name (item ID)
└── ...
```

### Summary Information

After completion, you'll see a summary:

```
Done. Saved 15 SVG file(s) to ./svgs
  • 12 files kept their original names
  • 3 files used generated names (item IDs)
```

## Using Downloaded SVGs

The downloaded SVG files are perfect for:

- **Diagramming tools**: Upload to "My Shapes" in tools like Lucidchart, Draw.io, Visio
- **Icon libraries**: Use in design tools like Figma, Sketch, Adobe Illustrator
- **Web development**: Incorporate into websites and applications
- **Documentation**: Use in technical documentation and presentations

## Rate Limiting

The script automatically handles Miro's rate limiting:

- Maximum 4 requests per second
- Built-in delays between requests
- Graceful handling of API responses

## Troubleshooting

**No SVG files found?**

- Verify your Board ID and access token are correct
- Check that your token has `boards:read` permission
- Try using `--include-docs` flag to scan document items
- Ensure the board actually contains SVG files

**Permission errors?**

- Verify your access token is valid and not expired
- Ensure the token has access to the specific board
- Check that your Miro app has the correct permissions

**Network timeouts?**

- The script includes 20-second timeouts for requests
- If you experience issues, try running the script again

## License

This script is provided as-is for educational and personal use.
