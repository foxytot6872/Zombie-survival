# Pixel Font Setup

This directory is for pixel fonts used in the game. The game will automatically use pixel fonts if they're placed here, or fall back to the default system font if not found.

## Recommended Free Pixel Fonts

You can download these free pixel fonts from Google Fonts:

1. **Press Start 2P** (Recommended for retro/arcade feel)
   - Download: https://fonts.google.com/specimen/Press+Start+2P
   - File: `PressStart2P-Regular.ttf`
   - Rename to: `PressStart2P.ttf`

2. **VT323** (Console-style monospace)
   - Download: https://fonts.google.com/specimen/VT323
   - File: `VT323-Regular.ttf`
   - Rename to: `VT323.ttf`

3. **Pixelify Sans** (Modern pixel font)
   - Download: https://fonts.google.com/specimen/Pixelify+Sans
   - File: `PixelifySans-Regular.ttf`
   - Rename to: `PixelifySans.ttf`

4. **Silkscreen** (Condensed digital feel)
   - Download: https://fonts.google.com/specimen/Silkscreen
   - File: `Silkscreen-Regular.ttf`
   - Rename to: `Silkscreen.ttf`

## Setup Instructions

1. Download your preferred font from Google Fonts
2. Extract the `.ttf` file
3. Rename it to match the font name (e.g., `PressStart2P.ttf`)
4. Place it in this `asset/fonts/` directory
5. Update the `PIXEL_FONT_PATH` in `main.py` (line ~97) to point to your font file:
   ```python
   PIXEL_FONT_PATH = 'asset/fonts/PressStart2P.ttf'  # Change to your font
   ```

## Current Font Path

The game is currently configured to use: `asset/fonts/PressStart2P.ttf`

If the font file is not found, the game will automatically fall back to the default system font (Arial on Windows).

