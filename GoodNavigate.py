"""Comfortable camera navigation helper for Vizard 8.

Typical use from another Vizard script::

    import viz
    import GoodNavigate

    viz.go()
    GoodNavigate.enable()

Importing this module does not start Vizard or add scene objects. Call enable()
after viz.go() in the script that owns the scene.
"""

import math
import os

import viz
import vizact


DEFAULT_SPEED = 2.0
DEFAULT_FAST_MULT = 3.0
DEFAULT_SENSE = 0.2
DEFAULT_SPEED_MULT = 1.0
MIN_SPEED_MULT = 0.25
MAX_SPEED_MULT = 5.0
SPEED_MULT_STEP = 0.25
SPEED_OVERLAY_DURATION = 1.0
SPEED_OVERLAY_BG_FILE = 'goodnavigate_overlay_bg.png'
SPEED_OVERLAY_BG_SCALE_X = 3.25
SPEED_OVERLAY_BG_ASPECT = 512.0 / 192.0
SPEED_OVERLAY_TEXT_SCALE_X = 1.0


class CameraNavigator(object):
    """WASD + mouse camera controller for a Vizard view."""

    def __init__(self, view=None, speed=DEFAULT_SPEED, fast_mult=DEFAULT_FAST_MULT,
                 sense=DEFAULT_SENSE, speed_mult=DEFAULT_SPEED_MULT,
                 min_speed_mult=MIN_SPEED_MULT, max_speed_mult=MAX_SPEED_MULT,
                 speed_mult_step=SPEED_MULT_STEP, mouse_override=True,
                 show_speed_overlay=True,
                 speed_overlay_duration=SPEED_OVERLAY_DURATION):
        self.view = view or viz.MainView
        self.speed = speed
        self.fast_mult = fast_mult
        self.sense = sense
        self.speed_mult = speed_mult
        self.min_speed_mult = min_speed_mult
        self.max_speed_mult = max_speed_mult
        self.speed_mult_step = speed_mult_step
        self.mouse_override = mouse_override
        self.show_speed_overlay = show_speed_overlay
        self.speed_overlay_duration = speed_overlay_duration
        self.active_button = None
        self.enabled = False
        self._registered = False
        self._timer = None
        self._speed_overlay = None
        self._speed_overlay_bg = None
        self._speed_overlay_remaining = 0.0
        self._last_overlay_aspect = None

    def enable(self):
        """Enable mouse-look and keyboard movement callbacks."""
        if self.mouse_override:
            viz.mouse.setOverride(viz.ON)

        if self.show_speed_overlay:
            self._ensure_speed_overlay()

        if not self._registered:
            viz.callback(viz.MOUSEDOWN_EVENT, self.on_mouse_down)
            viz.callback(viz.MOUSEUP_EVENT, self.on_mouse_up)
            viz.callback(viz.MOUSE_MOVE_EVENT, self.on_mouse_move)
            mouse_wheel_event = getattr(viz, 'MOUSEWHEEL_EVENT', None)
            if mouse_wheel_event is not None:
                viz.callback(mouse_wheel_event, self.on_mouse_wheel)
            self._timer = vizact.ontimer(0, self.update_movement)
            self._registered = True

        self.enabled = True
        return self

    def disable(self):
        """Pause controls and release any trapped mouse state."""
        self.enabled = False
        self.active_button = None
        self._speed_overlay_remaining = 0.0
        self._last_overlay_aspect = None
        self._set_speed_overlay_visible(False)
        viz.mouse.setTrap(viz.OFF)
        viz.mouse.setVisible(viz.ON)
        return self

    def configure(self, speed=None, fast_mult=None, sense=None, view=None,
                  speed_mult=None, show_speed_overlay=None):
        """Update controller settings without registering callbacks again."""
        if speed is not None:
            self.speed = speed
        if fast_mult is not None:
            self.fast_mult = fast_mult
        if sense is not None:
            self.sense = sense
        if view is not None:
            self.view = view
        if show_speed_overlay is not None:
            self.show_speed_overlay = show_speed_overlay
            if not show_speed_overlay:
                self._set_speed_overlay_visible(False)
        if speed_mult is not None:
            self.set_speed_mult(speed_mult, show_overlay=False)
        return self

    def set_speed_mult(self, value, show_overlay=True):
        """Set the scroll-adjusted movement speed multiplier."""
        self.speed_mult = max(self.min_speed_mult, min(self.max_speed_mult, value))
        if show_overlay:
            self._show_speed_overlay()
        return self.speed_mult

    def get_speed_mult(self):
        """Return the current scroll-adjusted movement speed multiplier."""
        return self.speed_mult

    def on_mouse_down(self, button):
        if (not self.enabled or self.active_button is not None or
                button not in (viz.MOUSEBUTTON_LEFT, viz.MOUSEBUTTON_RIGHT)):
            return

        self.active_button = button
        viz.mouse.setTrap(viz.ON)
        viz.mouse.setVisible(viz.OFF)

        # Left-drag is horizontal turn mode, so entering it levels the pitch.
        if button == viz.MOUSEBUTTON_LEFT:
            yaw, _pitch, roll = self.view.getEuler()
            self.view.setEuler([yaw, 0, roll])

    def on_mouse_up(self, button):
        if not self.enabled or button != self.active_button:
            return

        viz.mouse.setTrap(viz.OFF)
        viz.mouse.setVisible(viz.ON)
        self.active_button = None

    def on_mouse_move(self, event):
        if not self.enabled or self.active_button is None:
            return

        yaw, pitch, roll = self.view.getEuler()
        yaw += event.dx * self.sense

        if self.active_button == viz.MOUSEBUTTON_RIGHT:
            pitch = max(-89.0, min(89.0, pitch - event.dy * self.sense))

        self.view.setEuler([yaw, pitch, roll])

    def on_mouse_wheel(self, *args):
        if not self.enabled:
            return

        delta = self._get_wheel_delta(args)
        if delta == 0:
            return

        step = self.speed_mult_step if delta > 0 else -self.speed_mult_step
        self.set_speed_mult(self.speed_mult + step)

    def _get_wheel_delta(self, args):
        for value in args:
            if isinstance(value, (int, float)):
                return value

            for attr in ('wheel', 'delta', 'direction', 'dir'):
                if hasattr(value, attr):
                    attr_value = getattr(value, attr)
                    if isinstance(attr_value, (int, float)):
                        return attr_value

        return 0

    def _ensure_speed_overlay(self):
        if self._speed_overlay is not None:
            return self._speed_overlay

        try:
            self._speed_overlay_bg = viz.addTexQuad(parent=viz.SCREEN)
            self._speed_overlay = self._create_speed_overlay_text()
        except Exception:
            self._speed_overlay = None
            self._speed_overlay_bg = None
            return None

        self._configure_speed_overlay_bg()
        self._configure_speed_overlay_text()
        self._update_speed_overlay_layout(force=True)
        self._set_speed_overlay_visible(False)
        return self._speed_overlay

    def _create_speed_overlay_text(self):
        try:
            return viz.addText('', parent=viz.SCREEN, font='Arial')
        except Exception:
            return viz.addText('', parent=viz.SCREEN)

    def _configure_speed_overlay_bg(self):
        self._call_overlay_bg_method('setPosition', [0.5, 0.5, 0])
        self._call_overlay_bg_method('color', [0.22, 0.22, 0.22])
        self._call_overlay_bg_method('alpha', 0.82)
        self._apply_speed_overlay_bg_texture()

    def _configure_speed_overlay_text(self):
        self._call_overlay_method('setPosition', [0.5, 0.5, 0])
        self._call_overlay_method('alignment', getattr(viz, 'ALIGN_CENTER_CENTER', None))
        self._call_overlay_method('font', 'Arial')
        self._call_overlay_method('fontSize', 84)
        self._call_overlay_method('color', getattr(viz, 'WHITE', [1, 1, 1]))

    def _update_speed_overlay_layout(self, force=False):
        aspect = self._get_window_aspect()
        if not force and self._last_overlay_aspect == aspect:
            return

        self._last_overlay_aspect = aspect
        self._call_overlay_bg_method('setScale', [
            SPEED_OVERLAY_BG_SCALE_X,
            SPEED_OVERLAY_BG_SCALE_X * aspect / SPEED_OVERLAY_BG_ASPECT,
            1.0,
        ])
        self._call_overlay_method('setScale', [
            SPEED_OVERLAY_TEXT_SCALE_X,
            SPEED_OVERLAY_TEXT_SCALE_X * aspect,
            1.0,
        ])

    def _get_window_aspect(self):
        try:
            width, height = viz.window.getSize()
            if height:
                return float(width) / float(height)
        except Exception:
            pass

        try:
            width = viz.window.getWidth()
            height = viz.window.getHeight()
            if height:
                return float(width) / float(height)
        except Exception:
            pass

        return 1.0

    def _apply_speed_overlay_bg_texture(self):
        texture_path = os.path.join(os.path.dirname(__file__), SPEED_OVERLAY_BG_FILE)
        if not os.path.exists(texture_path):
            return

        try:
            texture = viz.addTexture(texture_path)
        except Exception:
            return

        self._call_overlay_bg_method('texture', texture)

    def _show_speed_overlay(self):
        if not self.show_speed_overlay:
            return

        overlay = self._ensure_speed_overlay()
        if overlay is None:
            return

        message = u'\u00d7{:.2f}'.format(self.speed_mult)
        if not self._call_overlay_method('message', message):
            self._call_overlay_method('setText', message)

        self._update_speed_overlay_layout(force=True)
        self._speed_overlay_remaining = self.speed_overlay_duration
        self._set_speed_overlay_visible(True)

    def _update_speed_overlay(self, dt):
        if self._speed_overlay_remaining <= 0.0:
            return

        self._speed_overlay_remaining -= dt
        if self._speed_overlay_remaining <= 0.0:
            self._speed_overlay_remaining = 0.0
            self._set_speed_overlay_visible(False)

    def _set_speed_overlay_visible(self, visible):
        state = viz.ON if visible else viz.OFF
        if self._speed_overlay_bg is not None:
            self._call_overlay_bg_method('visible', state)
        if self._speed_overlay is not None:
            self._call_overlay_method('visible', state)

    def _call_overlay_method(self, name, *args):
        return self._call_node_method(self._speed_overlay, name, *args)

    def _call_overlay_bg_method(self, name, *args):
        return self._call_node_method(self._speed_overlay_bg, name, *args)

    def _call_node_method(self, node, name, *args):
        if node is None:
            return False
        method = getattr(node, name, None)
        if method is None:
            return False
        try:
            method(*args)
            return True
        except Exception:
            return False

    def update_movement(self):
        if not self.enabled:
            return

        dt = None
        if self._speed_overlay_remaining > 0.0:
            dt = viz.elapsed()
            self._update_speed_overlay_layout()
            self._update_speed_overlay(dt)

        mx = viz.key.isDown('d') - viz.key.isDown('a')
        my = viz.key.isDown(' ') - viz.key.isDown('c')
        mz = viz.key.isDown('w') - viz.key.isDown('s')

        if mx == 0 and my == 0 and mz == 0:
            return

        if dt is None:
            dt = viz.elapsed()
        is_shift = viz.key.isDown(viz.KEY_SHIFT_L) or viz.key.isDown(viz.KEY_SHIFT_R)
        speed = self.speed * self.speed_mult * (self.fast_mult if is_shift else 1.0) * dt

        length = math.sqrt(mx ** 2 + my ** 2 + mz ** 2)
        mx, my, mz = (mx / length) * speed, (my / length) * speed, (mz / length) * speed

        rad = math.radians(self.view.getEuler()[0])
        sin_y, cos_y = math.sin(rad), math.cos(rad)

        pos = self.view.getPosition()
        self.view.setPosition([
            pos[0] + (mx * cos_y + mz * sin_y),
            pos[1] + my,
            pos[2] + (-mx * sin_y + mz * cos_y),
        ])


_default_navigator = None


def enable(speed=DEFAULT_SPEED, fast_mult=DEFAULT_FAST_MULT, sense=DEFAULT_SENSE,
           speed_mult=DEFAULT_SPEED_MULT, view=None, mouse_override=True,
           show_speed_overlay=True):
    """Enable the shared camera navigator and return it.

    Call this once after viz.go() from your scene script. Repeated calls reuse the
    same controller and only update its settings.
    """
    global _default_navigator

    if _default_navigator is None:
        _default_navigator = CameraNavigator(
            view=view,
            speed=speed,
            fast_mult=fast_mult,
            sense=sense,
            speed_mult=speed_mult,
            mouse_override=mouse_override,
            show_speed_overlay=show_speed_overlay,
        )
    else:
        _default_navigator.configure(
            speed=speed,
            fast_mult=fast_mult,
            sense=sense,
            speed_mult=speed_mult,
            view=view,
            show_speed_overlay=show_speed_overlay,
        )
        _default_navigator.mouse_override = mouse_override

    return _default_navigator.enable()


def disable():
    """Disable the shared camera navigator if it has been created."""
    if _default_navigator is not None:
        _default_navigator.disable()
    return _default_navigator


def get_navigator():
    """Return the shared navigator, or None before enable() is called."""
    return _default_navigator


if __name__ == '__main__':
    viz.go()
    viz.addChild('ground.osgb')
    enable()










