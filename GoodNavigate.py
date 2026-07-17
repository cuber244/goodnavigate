"""Comfortable camera navigation helper for WorldViz Vizard 8.

Typical use from another Vizard script::

    import viz
    import goodnavigate

    viz.go()
    goodnavigate.enable()

Importing this module does not start Vizard or add scene objects. Call enable()
after viz.go() in the script that owns the scene.
"""

import ctypes
import math
import os

import viz
import vizact


DEFAULT_SPEED = 2.0
DEFAULT_FAST_MULT = 3.0
DEFAULT_SENSE = 1.0
MOUSE_SENSE_SCALE = 0.1
DEFAULT_SPEED_MULT = 1.0
MIN_SPEED_MULT = 0.25
MAX_SPEED_MULT = 5.0
SPEED_MULT_STEP = 0.25
SPEED_OVERLAY_DURATION = 1.0
SPEED_OVERLAY_BG_FILE = 'goodnavigate_overlay_bg.png'
SPEED_OVERLAY_BG_SCALE_X = 3.25
SPEED_OVERLAY_BG_ASPECT = 512.0 / 192.0
SPEED_OVERLAY_TEXT_SCALE_X = 1.0
DEFAULT_HEIGHT_LOCK = True
DEFAULT_FORWARD_KEY = 'w'
DEFAULT_BACKWARD_KEY = 's'
DEFAULT_LEFT_KEY = 'a'
DEFAULT_RIGHT_KEY = 'd'
DEFAULT_UP_KEY = ' '
DEFAULT_DOWN_KEY = 'c'
DEFAULT_TOGGLE_HEIGHT_LOCK_KEY = 'f'
DEFAULT_CHECK_WINDOW_FOCUS = True


class CameraNavigator(object):
    """WASD + mouse camera controller for a Vizard view."""

    def __init__(self, view=None, speed=DEFAULT_SPEED, fast_mult=DEFAULT_FAST_MULT,
                 sense=DEFAULT_SENSE, speed_mult=DEFAULT_SPEED_MULT,
                 min_speed_mult=MIN_SPEED_MULT, max_speed_mult=MAX_SPEED_MULT,
                 speed_mult_step=SPEED_MULT_STEP, mouse_override=True,
                 show_speed_overlay=True,
                 speed_overlay_duration=SPEED_OVERLAY_DURATION,
                 height_lock=DEFAULT_HEIGHT_LOCK,
                 forward_key=DEFAULT_FORWARD_KEY,
                 backward_key=DEFAULT_BACKWARD_KEY,
                 left_key=DEFAULT_LEFT_KEY,
                 right_key=DEFAULT_RIGHT_KEY,
                 up_key=DEFAULT_UP_KEY,
                 down_key=DEFAULT_DOWN_KEY,
                 toggle_height_lock_key=DEFAULT_TOGGLE_HEIGHT_LOCK_KEY,
                 fast_keys=None,
                 check_window_focus=DEFAULT_CHECK_WINDOW_FOCUS):
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
        self.height_lock = bool(height_lock)
        self.forward_key = forward_key
        self.backward_key = backward_key
        self.left_key = left_key
        self.right_key = right_key
        self.up_key = up_key
        self.down_key = down_key
        self.toggle_height_lock_key = toggle_height_lock_key
        self.fast_keys = tuple(fast_keys) if fast_keys is not None else (viz.KEY_SHIFT_L, viz.KEY_SHIFT_R)
        self.check_window_focus = check_window_focus
        self.active_button = None
        self.enabled = False
        self._registered = False
        self._uses_key_callbacks = False
        self._pressed_keys = set()
        self._window_handle = None
        self._timer = None
        self._speed_overlay = None
        self._speed_overlay_bg = None
        self._speed_overlay_remaining = 0.0
        self._last_overlay_aspect = None
        self._height_lock_toggle_down = False

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
            keydown_event = getattr(viz, 'KEYDOWN_EVENT', None)
            keyup_event = getattr(viz, 'KEYUP_EVENT', None)
            if keydown_event is not None and keyup_event is not None:
                viz.callback(keydown_event, self.on_key_down)
                viz.callback(keyup_event, self.on_key_up)
                self._uses_key_callbacks = True
            self._timer = vizact.ontimer(0, self.update_movement)
            self._registered = True

        self.enabled = True
        return self

    def disable(self):
        """Pause controls and return mouse handling to Vizard defaults."""
        self.pause()
        if self.mouse_override:
            viz.mouse.setOverride(viz.OFF)
        return self

    def pause(self):
        """Pause GoodNavigate controls without changing Vizard mouse override state."""
        self.enabled = False
        self._clear_input_state()
        self._speed_overlay_remaining = 0.0
        self._last_overlay_aspect = None
        self._set_speed_overlay_visible(False)
        return self

    def resume(self):
        """Resume GoodNavigate controls after pause()."""
        if self.mouse_override:
            viz.mouse.setOverride(viz.ON)
        self.enabled = True
        return self

    def configure(self, speed=None, fast_mult=None, sense=None, view=None,
                  speed_mult=None, show_speed_overlay=None, height_lock=None,
                  forward_key=None, backward_key=None, left_key=None,
                  right_key=None, up_key=None, down_key=None,
                  toggle_height_lock_key=None, fast_keys=None,
                  check_window_focus=None):
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
        if height_lock is not None:
            self.set_height_lock(height_lock)
        if check_window_focus is not None:
            self.check_window_focus = check_window_focus
        self.set_keys(
            forward=forward_key,
            backward=backward_key,
            left=left_key,
            right=right_key,
            up=up_key,
            down=down_key,
            toggle_height_lock=toggle_height_lock_key,
            fast=fast_keys,
        )
        return self

    def set_speed(self, value):
        """Set the base movement speed."""
        self.speed = value
        return self.speed

    def set_fast_mult(self, value):
        """Set the temporary fast movement multiplier."""
        self.fast_mult = value
        return self.fast_mult

    def set_sense(self, value):
        """Set the mouse-look sensitivity."""
        self.sense = value
        return self.sense

    def set_speed_mult(self, value, show_overlay=True):
        """Set the scroll-adjusted movement speed multiplier."""
        self.speed_mult = max(self.min_speed_mult, min(self.max_speed_mult, value))
        if show_overlay:
            self._show_speed_overlay()
        return self.speed_mult

    def reset_speed_mult(self):
        """Reset the scroll-adjusted movement speed multiplier to x1.00."""
        return self.set_speed_mult(DEFAULT_SPEED_MULT)

    def get_speed_mult(self):
        """Return the current scroll-adjusted movement speed multiplier."""
        return self.speed_mult

    def set_keys(self, forward=None, backward=None, left=None, right=None,
                 up=None, down=None, toggle_height_lock=None, fast=None):
        """Update keyboard bindings. Pass None to leave a binding unchanged."""
        if forward is not None:
            self.forward_key = forward
        if backward is not None:
            self.backward_key = backward
        if left is not None:
            self.left_key = left
        if right is not None:
            self.right_key = right
        if up is not None:
            self.up_key = up
        if down is not None:
            self.down_key = down
        if toggle_height_lock is not None:
            self.toggle_height_lock_key = toggle_height_lock
        if fast is not None:
            self.fast_keys = tuple(fast)
        return self

    def get_status(self):
        """Return the current GoodNavigate state as a dictionary."""
        return {
            'enabled': self.enabled,
            'height_lock': self.height_lock,
            'speed': self.speed,
            'fast_mult': self.fast_mult,
            'sense': self.sense,
            'speed_mult': self.speed_mult,
            'mouse_override': self.mouse_override,
            'show_speed_overlay': self.show_speed_overlay,
            'window_active': self._is_window_active(),
            'check_window_focus': self.check_window_focus,
            'keys': {
                'forward': self.forward_key,
                'backward': self.backward_key,
                'left': self.left_key,
                'right': self.right_key,
                'up': self.up_key,
                'down': self.down_key,
                'toggle_height_lock': self.toggle_height_lock_key,
                'fast': self.fast_keys,
            },
        }

    def set_height_lock(self, locked, show_overlay=False):
        """Set whether WASD movement ignores camera pitch."""
        self.height_lock = bool(locked)
        if show_overlay:
            self._show_height_lock_overlay()
        return self.height_lock

    def toggle_height_lock(self, show_overlay=True):
        """Toggle whether WASD movement ignores camera pitch."""
        return self.set_height_lock(not self.height_lock, show_overlay=show_overlay)

    def is_height_locked(self):
        """Return True when WASD movement is constrained to horizontal motion."""
        return self.height_lock

    def on_mouse_down(self, button):
        if (not self.enabled or self.active_button is not None or
                button not in (viz.MOUSEBUTTON_LEFT, viz.MOUSEBUTTON_RIGHT)):
            return

        self.active_button = button
        viz.mouse.setTrap(viz.ON)
        viz.mouse.setVisible(viz.OFF)

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
        yaw += event.dx * self.sense * MOUSE_SENSE_SCALE

        if self.active_button == viz.MOUSEBUTTON_RIGHT:
            pitch = max(-89.0, min(89.0, pitch - event.dy * self.sense * MOUSE_SENSE_SCALE))

        self.view.setEuler([yaw, pitch, roll])

    def on_mouse_wheel(self, *args):
        if not self.enabled:
            return

        delta = self._get_wheel_delta(args)
        if delta == 0:
            return

        step = self.speed_mult_step if delta > 0 else -self.speed_mult_step
        self.set_speed_mult(self.speed_mult + step)

    def on_key_down(self, *args):
        if not self.enabled or not self._is_window_active():
            return

        key = self._get_key_value(args)
        if key is None:
            return

        normalized = self._normalize_key(key)
        self._pressed_keys.add(normalized)
        if (self._keys_match(key, self.toggle_height_lock_key) and
                not self._height_lock_toggle_down):
            self.toggle_height_lock(show_overlay=False)
            self._height_lock_toggle_down = True

    def on_key_up(self, *args):
        key = self._get_key_value(args)
        if key is None:
            return

        normalized = self._normalize_key(key)
        self._pressed_keys.discard(normalized)
        if self._keys_match(key, self.toggle_height_lock_key):
            self._height_lock_toggle_down = False

    def _get_key_value(self, args):
        for value in args:
            if isinstance(value, (str, int, float)):
                return value

            for attr in ('key', 'char', 'name'):
                if hasattr(value, attr):
                    return getattr(value, attr)

        return None

    def _normalize_key(self, key):
        if isinstance(key, str):
            return key.lower()
        return key

    def _keys_match(self, actual, expected):
        return self._normalize_key(actual) == self._normalize_key(expected)

    def _is_key_down(self, key):
        if not self._is_window_active():
            return False
        if self._uses_key_callbacks:
            return self._normalize_key(key) in self._pressed_keys
        return viz.key.isDown(key)

    def _clear_input_state(self):
        self._pressed_keys.clear()
        self._height_lock_toggle_down = False
        if self.active_button is not None:
            self.active_button = None
            viz.mouse.setTrap(viz.OFF)
            viz.mouse.setVisible(viz.ON)

    def _is_window_active(self):
        if not self.check_window_focus:
            return True
        try:
            return self._is_foreground_window()
        except Exception:
            return True

    def _is_foreground_window(self):
        if os.name != 'nt':
            return True

        handle = self._get_window_handle()
        if not handle:
            return True

        user32 = ctypes.windll.user32
        foreground = user32.GetForegroundWindow()
        if not foreground:
            return True

        if foreground == handle:
            return True

        ga_root = 2
        root = user32.GetAncestor(handle, ga_root)
        foreground_root = user32.GetAncestor(foreground, ga_root)
        return root != 0 and root == foreground_root

    def _get_window_handle(self):
        if self._window_handle:
            return self._window_handle

        get_handle = getattr(viz.window, 'getHandle', None)
        if get_handle is None:
            return None

        try:
            self._window_handle = int(get_handle())
        except Exception:
            self._window_handle = None
        return self._window_handle

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

    def _show_overlay_message(self, message):
        if not self.show_speed_overlay:
            return

        overlay = self._ensure_speed_overlay()
        if overlay is None:
            return

        if not self._call_overlay_method('message', message):
            self._call_overlay_method('setText', message)

        self._update_speed_overlay_layout(force=True)
        self._speed_overlay_remaining = self.speed_overlay_duration
        self._set_speed_overlay_visible(True)

    def _show_speed_overlay(self):
        self._show_overlay_message(u'\u00d7{:.2f}'.format(self.speed_mult))

    def _show_height_lock_overlay(self):
        state = 'ON' if self.height_lock else 'OFF'
        self._show_overlay_message('Height Lock ' + state)

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

    def _update_height_lock_toggle(self):
        is_down = self._is_key_down(self.toggle_height_lock_key)
        if is_down and not self._height_lock_toggle_down:
            self.toggle_height_lock(show_overlay=False)
        self._height_lock_toggle_down = is_down

    def update_movement(self):
        if not self.enabled:
            return

        if not self._is_window_active():
            self._clear_input_state()
            return

        if not self._uses_key_callbacks:
            self._update_height_lock_toggle()

        dt = None
        if self._speed_overlay_remaining > 0.0:
            dt = viz.elapsed()
            self._update_speed_overlay_layout()
            self._update_speed_overlay(dt)

        mx = self._is_key_down(self.right_key) - self._is_key_down(self.left_key)
        my = self._is_key_down(self.up_key) - self._is_key_down(self.down_key)
        mz = self._is_key_down(self.forward_key) - self._is_key_down(self.backward_key)

        if mx == 0 and my == 0 and mz == 0:
            return

        if dt is None:
            dt = viz.elapsed()
        is_shift = any(self._is_key_down(key) for key in self.fast_keys)
        speed = self.speed * self.speed_mult * (self.fast_mult if is_shift else 1.0) * dt

        length = math.sqrt(mx ** 2 + my ** 2 + mz ** 2)
        mx, my, mz = (mx / length) * speed, (my / length) * speed, (mz / length) * speed

        yaw, pitch, _roll = self.view.getEuler()
        yaw_rad = math.radians(yaw)
        sin_y, cos_y = math.sin(yaw_rad), math.cos(yaw_rad)

        if self.height_lock:
            forward_x, forward_y, forward_z = sin_y, 0.0, cos_y
        else:
            pitch_rad = math.radians(pitch)
            cos_p = math.cos(pitch_rad)
            forward_x = sin_y * cos_p
            forward_y = -math.sin(pitch_rad)
            forward_z = cos_y * cos_p

        right_x, right_z = cos_y, -sin_y
        pos = self.view.getPosition()
        self.view.setPosition([
            pos[0] + (mx * right_x + mz * forward_x),
            pos[1] + my + mz * forward_y,
            pos[2] + (mx * right_z + mz * forward_z),
        ])


_default_navigator = None


def enable(speed=DEFAULT_SPEED, fast_mult=DEFAULT_FAST_MULT, sense=DEFAULT_SENSE,
           speed_mult=DEFAULT_SPEED_MULT, view=None, mouse_override=True,
           show_speed_overlay=True, height_lock=DEFAULT_HEIGHT_LOCK,
           forward_key=DEFAULT_FORWARD_KEY, backward_key=DEFAULT_BACKWARD_KEY,
           left_key=DEFAULT_LEFT_KEY, right_key=DEFAULT_RIGHT_KEY,
           up_key=DEFAULT_UP_KEY, down_key=DEFAULT_DOWN_KEY,
           toggle_height_lock_key=DEFAULT_TOGGLE_HEIGHT_LOCK_KEY, fast_keys=None,
           check_window_focus=DEFAULT_CHECK_WINDOW_FOCUS):
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
            height_lock=height_lock,
            forward_key=forward_key,
            backward_key=backward_key,
            left_key=left_key,
            right_key=right_key,
            up_key=up_key,
            down_key=down_key,
            toggle_height_lock_key=toggle_height_lock_key,
            fast_keys=fast_keys,
            check_window_focus=check_window_focus,
        )
    else:
        _default_navigator.configure(
            speed=speed,
            fast_mult=fast_mult,
            sense=sense,
            speed_mult=speed_mult,
            view=view,
            show_speed_overlay=show_speed_overlay,
            height_lock=height_lock,
            forward_key=forward_key,
            backward_key=backward_key,
            left_key=left_key,
            right_key=right_key,
            up_key=up_key,
            down_key=down_key,
            toggle_height_lock_key=toggle_height_lock_key,
            fast_keys=fast_keys,
            check_window_focus=check_window_focus,
        )
        _default_navigator.mouse_override = mouse_override

    return _default_navigator.enable()


def disable():
    """Disable the shared navigator and return Vizard mouse handling to defaults."""
    if _default_navigator is not None:
        _default_navigator.disable()
    return _default_navigator


def pause():
    """Pause GoodNavigate controls without changing Vizard mouse override state."""
    if _default_navigator is not None:
        _default_navigator.pause()
    return _default_navigator


def resume():
    """Resume GoodNavigate controls after pause()."""
    if _default_navigator is not None:
        _default_navigator.resume()
    return _default_navigator


def get_navigator():
    """Return the shared navigator, or None before enable() is called."""
    return _default_navigator


if __name__ == '__main__':
    viz.go()
    viz.addChild('ground.osgb')
    enable()
