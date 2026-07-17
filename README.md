# GoodNavigate

GoodNavigate is a camera navigation helper package for **WorldViz Vizard 8**.
It adds comfortable editor-style camera controls to a Vizard scene with one call.

This package depends on Vizard's `viz` and `vizact` modules, so it is intended to run inside a Vizard 8 Python environment. It is not a standalone Python camera library.

## Features

- Mouse-look camera rotation
- `WASD` camera movement
- Height-locked horizontal movement mode
- `F` key toggle for height lock
- Customizable movement keys
- Runtime speed and mouse sensitivity setters
- Current status dictionary
- Stops movement when the Vizard window loses focus
- `Space` to move up
- `C` to move down
- `Shift` for temporary fast movement
- Mouse wheel speed adjustment
- Center-screen speed multiplier overlay
- Rounded gray overlay background
- No automatic `viz.go()` when imported
- `pause()`, `resume()`, and `disable()` control helpers

## Installation

Install it into the Python environment used by Vizard 8.

```powershell
python -m pip install git+https://github.com/cuber244/goodnavigate.git
```

If `python` is not Vizard's Python, run pip through the Vizard Python executable instead. The exact path depends on your PC, but the command will look like this:

```powershell
"C:\Path\To\Vizard8\python.exe" -m pip install git+https://github.com/cuber244/goodnavigate.git
```

After the package is published to PyPI, installation becomes shorter:

```powershell
python -m pip install goodnavigate
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
| `F` | Toggle height lock |

`F` is handled through Vizard's key-down callback when available. If that callback is unavailable, GoodNavigate falls back to polling the key state each frame.

## Height Lock

Height lock is enabled by default.

When height lock is enabled, `WASD` movement stays horizontal even if the camera is looking up or down. This is useful for walking-style navigation.

When height lock is disabled, `W` and `S` move forward and backward along the camera's pitch direction. Looking up and pressing `W` moves upward and forward; looking down and pressing `W` moves downward and forward. `A` and `D` strafe relative to the current yaw.

Toggle height lock while running:

```python
# Press F in the Vizard window
```

Configure the initial mode:

```python
goodnavigate.enable(height_lock=True)   # default
goodnavigate.enable(height_lock=False)  # free fly movement
```

Programmatic control:

```python
navigator = goodnavigate.enable()

navigator.set_height_lock(False)
navigator.toggle_height_lock()
locked = navigator.is_height_locked()
```

## Custom Keys

You can customize movement keys when enabling GoodNavigate.

```python
goodnavigate.enable(
    forward_key='i',
    backward_key='k',
    left_key='j',
    right_key='l',
    up_key='u',
    down_key='o',
    toggle_height_lock_key='h',
)
```

Temporary fast movement keys can also be changed. Pass a tuple or list of Vizard key constants or key strings.

```python
goodnavigate.enable(fast_keys=(viz.KEY_SHIFT_L, viz.KEY_SHIFT_R))
```

You can change keys after enabling:

```python
navigator = goodnavigate.enable()
navigator.set_keys(forward='i', backward='k', toggle_height_lock='h')
```

## Speed Adjustment

The mouse wheel changes the movement speed multiplier.

- Default multiplier: `x1.00`
- Minimum multiplier: `x0.25`
- Maximum multiplier: `x5.00`
- Step per wheel operation: `0.25`

When the speed changes, or when the user scrolls at the minimum/maximum limit, the current multiplier is shown in the center of the screen for 1 second.

## Configuration

You can customize the base movement speed, fast movement multiplier, mouse sensitivity, initial speed multiplier, and initial height lock mode.

```python
goodnavigate.enable(
    speed=2.0,
    fast_mult=3.0,
    sense=0.2,
    speed_mult=1.0,
    height_lock=True,
    check_window_focus=True,
)
```

Disable the speed overlay if needed:

```python
goodnavigate.enable(show_speed_overlay=False)
```

Runtime setters:

```python
navigator = goodnavigate.enable()

navigator.set_speed(3.0)
navigator.set_fast_mult(4.0)
navigator.set_sense(0.15)
navigator.set_speed_mult(2.0)
navigator.reset_speed_mult()
```

## Status

Get the current controller state as a dictionary:

```python
navigator = goodnavigate.enable()
status = navigator.get_status()
```

The dictionary includes values such as `enabled`, `height_lock`, `speed`, `fast_mult`, `sense`, `speed_mult`, and current key bindings.


## Window Focus Safety

GoodNavigate stops movement when the Vizard window loses focus. This prevents held movement keys from remaining active after clicking another window.

This behavior is enabled by default:

```python
goodnavigate.enable(check_window_focus=True)
```

If you need to disable the focus check for a special setup, pass:

```python
goodnavigate.enable(check_window_focus=False)
```
## Pause, Resume, Disable

Pause GoodNavigate controls without returning Vizard mouse handling to its default behavior:

```python
goodnavigate.pause()
goodnavigate.resume()
```

Disable GoodNavigate controls and return mouse handling to Vizard defaults:

```python
goodnavigate.disable()
```

You can also call these on the navigator object:

```python
navigator = goodnavigate.enable()
navigator.pause()
navigator.resume()
navigator.disable()
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
