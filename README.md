# GoodNavigate

GoodNavigate is a small camera navigation helper module for **WorldViz Vizard 8**.
It adds comfortable editor-style camera controls to a Vizard scene with one call.

This module depends on Vizard's `viz` and `vizact` modules, so it is intended to run inside a Vizard 8 Python environment. It is not a standalone Python camera library.

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

## Files

Upload these files together:

```text
GoodNavigate.py
goodnavigate_overlay_bg.png
README.md
```

`goodnavigate_overlay_bg.png` is used for the rounded gray speed overlay background.

## Basic Usage

Place `GoodNavigate.py` and `goodnavigate_overlay_bg.png` in the same folder as your Vizard script.

```python
import viz
import GoodNavigate

viz.go()

GoodNavigate.enable()
```

Importing `GoodNavigate` does not start Vizard and does not add scene objects. Call `GoodNavigate.enable()` after `viz.go()` in the script that owns the scene.

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
GoodNavigate.enable(
    speed=2.0,
    fast_mult=3.0,
    sense=0.2,
    speed_mult=1.0,
)
```

Disable the speed overlay if needed:

```python
GoodNavigate.enable(show_speed_overlay=False)
```

Get or set the current speed multiplier:

```python
navigator = GoodNavigate.enable()

current = navigator.get_speed_mult()
navigator.set_speed_mult(2.0)
```

Temporarily disable controls:

```python
GoodNavigate.disable()
```

## Using A Different View

By default, GoodNavigate controls `viz.MainView`. You can pass another Vizard view object.

```python
my_view = viz.MainView
GoodNavigate.enable(view=my_view)
```

## Demo Mode

You can also run `GoodNavigate.py` directly. In that case only, it starts Vizard and adds `ground.osgb` for a simple test scene.

```python
python GoodNavigate.py
```

In normal projects, import it from your own Vizard script instead.

## Notes For GitHub / pip Packaging

Recommended repository name:

```text
goodnavigate
```

This first version can be distributed by copying `GoodNavigate.py` and `goodnavigate_overlay_bg.png` into a Vizard project folder.

For future pip packaging, the import name should ideally be changed to lowercase, for example:

```python
import goodnavigate

goodnavigate.enable()
```

Until then, use:

```python
import GoodNavigate
```

## Requirements

- WorldViz Vizard 8
- Vizard Python environment with `viz` and `vizact`

## License

Add a license file before public release if you want others to reuse or modify this module clearly.
