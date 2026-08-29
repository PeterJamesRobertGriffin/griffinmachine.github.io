# The Griffin Machine - Rare Cutaway System

## Overview

The Family Guy machine has a direct rare-video switch controlled by Python.

- Set `family_guy.rareChance` to `1` to play `clips/family_guy/rare/R1.mp4` every time Generate is pressed.
- Set it to `0` to never play `R1.mp4`; normal Family Guy clips are generated instead.
- The page re-reads `rarity-config.json` before every Generate click, so a running local server sees the next saved value without a refresh.

## How It Works

When a Family Guy video is generated:
1. The page loads the latest `rarity-config.json`.
2. If `rareChance` is exactly `1`, it plays `R1.mp4`.
3. If it is `0` (or any other valid value), it uses the normal Family Guy clips.

## Using the Rarity Controller

The `rarity_controller.py` script lets you adjust the rarity while the site is live.

### GUI Mode (Recommended)

Simply run the script without arguments to launch the GUI:

```bash
python3 rarity_controller.py
```

**Features:**
- 🎚️ Interactive slider to adjust rarity from never → always
- 📊 Real-time display showing current setting
- 🎯 Quick preset buttons (1 in 1000, 1 in 100, 1 in 20, etc.)
- 💾 One-click save with helpful commit reminders
- ✨ User-friendly interface

### Command Line Mode

```bash
# View current rarity
python3 rarity_controller.py --get

# Always play R1.mp4
python3 rarity_controller.py --set 1

# Never play R1.mp4
python3 rarity_controller.py --set 0

# Set to 1 in 100 (very rare)
python3 rarity_controller.py --set 0.01

# View common rarity presets
python3 rarity_controller.py --examples
```
### Launching the GUI Explicitly

```bash
python3 rarity_controller.py --gui
```
### Making Changes Live on GitHub

After updating the rarity:

```bash
# 1. Change the rarity
python3 rarity_controller.py --set 0.1

# 2. Commit the change
git add rarity-config.json
git commit -m "Temporarily increase rare cutaway chance to 1 in 10"

# 3. Push to GitHub
git push

# GitHub Pages is a static host: the change becomes live after the push has
# deployed. The page uses the new value on its next Generate click.
```

### Common Rarity Values

| Chance | Ratio | Use Case |
|--------|-------|----------|
| 0.001 | 1 in 1,000 | Super rare (default) |
| 0.005 | 1 in 200 | Very rare |
| 0.01 | 1 in 100 | Rare |
| 0.05 | 1 in 20 | Uncommon |
| 0.1 | 1 in 10 | Fairly common |
| 0.25 | 1 in 4 | Common |
| 0.5 | 1 in 2 | 50/50 chance |

## Configuration File

The `rarity-config.json` file stores the current rarity settings:

```json
{
  "custom": {
    "rareChance": 0.001,
    "description": "Chance of selecting a rare cutaway (default: 1 in 1000 = 0.001)"
  }
}
```

The JavaScript automatically loads this file on page load. No manual intervention needed.

## Adding Rare Clips

To add more rare cutaway clips:

1. Place start clips in: `clips/custom/rare/start/S1.mp4`, `S2.mp4`, etc.
2. Place end clips in: `clips/custom/rare/end/E1.mp4`, `E2.mp4`, etc.
3. Update the `rarity-config.json` with the counts (optional - currently uses 1 clip each):
   ```json
   {
     "custom": {
       "rareChance": 0.001,
       "rareStartCount": 3,
       "rareEndCount": 2
     }
   }
   ```

## Retep Machine Logo

The Retep machine now uses **logo4.png** for better branding!

## Workflow for Event Management

### Quick GUI Method (Recommended):
```bash
# 1. Launch the GUI
python3 rarity_controller.py

# 2. Use the slider or preset buttons to set rarity
# 3. Click "Save & Commit" to auto-generate commit message
# 4. Push to GitHub when ready
git push
```

### Command Line Method:
```bash
# 1. Set rarity
python3 rarity_controller.py --set 0.1

# 2. Commit and push
git add rarity-config.json
git commit -m "🎉 Event mode: rare cutaways at 1 in 10"
git push

# 3. After event, reset:
python3 rarity_controller.py --set 0.001
git add rarity-config.json
git commit -m "End event mode: back to 1 in 1000"
git push
```

## Technical Notes

- The rarity check happens **per video generation**, not per page load
- The config is cached on first page load, so changes require a **page refresh**
- The system uses `Math.random()` for probability calculation
- Rare clips are seamlessly blended with regular clips using the same FFmpeg concatenation process
