# GoodNavigate

GoodNavigate is a camera navigation helper package for **WorldViz Vizard 8**.
It adds comfortable editor-style camera controls to a Vizard scene with one call.

This package depends on Vizard's `viz` and `vizact` modules, so it is intended to run inside a Vizard 8 Python environment. It is not a standalone Python camera library.

## Features

- Mouse-look camera rotation
- `WASD` horizontal movement
- `Space` to move up
- `C` to move down
- `Shift` for temporary fast movement
- Mouse wheel speed adjustment
- Center-screen speed multiplier overlay
- Rounded gray overlay background
- No automatic `viz.go()` when imported

## Installation

Install it into the Python environment used by Vizard 8.

```powershell
python -m pip install git+https://github.com/cuber244/goodnavigate.git
```

If `python` is not Vizard's Python, run pip through the Vizard Python executable instead. The exact path depends on your PC, but the command will look like this:

```powershell
"C:\Path\To\Vizard8\python.exe" -m pip install git+https://github.com/cuber244/goodnavigate.git
```

After updating the GitHub repository, upgrade an existing installation with:

```powershell
python -m pip install --upgrade git+https://github.com/cuber244/goodnavigate.git
```

## Basic Usage

Use the lowercase package name for new Vizard scripts.

```python
import viz
import goodnavigate

viz.go()

goodnavigate.enable()
```

Importing `goodnavigate` does not start Vizard and does not add scene objects. Call `goodnavigate.enable()` after `viz.go()` in the script that owns the scene.

For compatibility, `import GoodNavigate` is also included after pip installation:

```python
import viz
import GoodNavigate

viz.go()
GoodNavigate.enable()
```

## Controls

| Input | Action |
| --- | --- |
| Left mouse drag | Horizontal yaw rotation, pitch is leveled when drag starts |
| Right mouse drag | Free-look yaw and pitch rotation |
| `W` / `S` | Move forward / backward |
| `A` / `D` | Move left / right |
| `Space` | Move up |
| `C` | Move down |
| `Shift` | Temporary fast movement |
| Mouse wheel | Change movement speed multiplier |

## Speed Adjustment

The mouse wheel changes the movement speed multiplier.

- Default multiplier: `x1.00`
- Minimum multiplier: `x0.25`
- Maximum multiplier: `x5.00`
- Step per wheel operation: `0.25`

When the speed changes, or when the user scrolls at the minimum/maximum limit, the current multiplier is shown in the center of the screen for 1 second.

## Configuration

You can customize the base movement speed, fast movement multiplier, mouse sensitivity, and initial speed multiplier.

```python
goodnavigate.enable(
    speed=2.0,
    fast_mult=3.0,
    sense=0.2,
    speed_mult=1.0,
)
```

Disable the speed overlay if needed:

```python
goodnavigate.enable(show_speed_overlay=False)
```

Get or set the current speed multiplier:

```python
navigator = goodnavigate.enable()

current = navigator.get_speed_mult()
navigator.set_speed_mult(2.0)
```

Temporarily disable controls:

```python
goodnavigate.disable()
```

## Using A Different View

By default, GoodNavigate controls `viz.MainView`. You can pass another Vizard view object.

```python
my_view = viz.MainView
goodnavigate.enable(view=my_view)
```

## Repository Layout

```text
pyproject.toml
README.md
src/
  goodnavigate/
    __init__.py
    goodnavigate_overlay_bg.png
  GoodNavigate.py
```

`src/goodnavigate/goodnavigate_overlay_bg.png` is packaged with the module and is used for the rounded gray speed overlay background.

The root-level `GoodNavigate.py` file can still be copied directly into a Vizard project if you want a no-pip workflow, but pip users should use the `src/` package.

## Requirements

- WorldViz Vizard 8
- Vizard Python environment with `viz` and `vizact`
- pip available in the Vizard Python environment
