# ============================================================
# Renderer
# Fullscreen step-based column renderer (scene only, no UI)
# Version: v13 alpha.5
# Changelog:
# - render timing stats (last / avg ms) for debug HUD
# ============================================================

init -10 python:
        import renpy as rp
        from renpy.display.render import Render, render
        from renpy.display.core import Displayable
        import time

        class StepRayRenderer(Displayable):
                def __init__(self, world, **kwargs):
                        super(StepRayRenderer, self).__init__(**kwargs)
                        self.world = world
                        self._dirty = True
                        self._cache = None
                        self._cache_key = None
                        self._last_notified_view_key = None

                        # POV / projection
                        self.fov_deg = 74.0
                        self.proj_scale = 0.58
                        self.near_clip_dist = 0.18

                        # World proportions (visual only)
                        self.wall_height_world = 1.00
                        self.cell_size_world = 1.00
                        self.distance_soften = 0.20

                        # Raycaster internals
                        self.ray_step = 0.035
                        self.max_ray_dist = 18.0
                        self.columns_cap = 220

                        # Debug perf stats
                        self.render_ms_last = 0.0
                        self.render_ms_avg = 0.0
                        self._render_ms_hist = []

                def current_view_key(self):
                        return self.world.state_view_key()

                def mark_dirty(self):
                        self._dirty = True
                        try:
                                rp.redraw(self, 0)
                        except Exception:
                                try:
                                        rp.display.render.redraw(self, 0)
                                except Exception:
                                        pass

                def on_world_changed(self, reason=None, force=False):
                        new_key = self.current_view_key()
                        changed = bool(force or (new_key != self._last_notified_view_key))
                        if changed:
                                self.mark_dirty()
                                self._last_notified_view_key = new_key
                        return changed

                def per_interact(self):
                        if self._dirty:
                                try:
                                        rp.redraw(self, 0)
                                except Exception:
                                        pass

                def _make_cache_key(self, w, h):
                        return (
                                w, h,
                                self.current_view_key(),
                                self.fov_deg,
                                self.columns_cap,
                                self.proj_scale,
                                self.near_clip_dist,
                                self.wall_height_world,
                                self.cell_size_world,
                                self.distance_soften,
                        )

                def _blit_solid(self, r, color, x, y, ww, hh, st, at):
                        if ww <= 0 or hh <= 0:
                                return
                        s = rp.store.Solid(color, xysize=(ww, hh))
                        sr = render(s, ww, hh, st, at)
                        r.blit(sr, (int(x), int(y)))

                def _facing_angle_rad(self):
                        p = self.world.player
                        if p.facing == 'N':
                                return -1.57079632679
                        if p.facing == 'E':
                                return 0.0
                        if p.facing == 'S':
                                return 1.57079632679
                        return 3.14159265359

                def _edge_block_info(self, cell_x, cell_y, d):
                        c = self.world.room.get(cell_x, cell_y)
                        if not c:
                                return {'hit': True, 'edge': {'type': EDGE_WALL}, 'kind': 'void'}
                        e = c.edges.get(d, {'type': EDGE_WALL})
                        if _edge_is_traversable(e):
                                return {'hit': False, 'edge': e, 'kind': 'edge'}
                        return {'hit': True, 'edge': e, 'kind': 'edge'}

                def _cast_ray(self, ang):
                        import math
                        room = self.world.room
                        p = self.world.player
                        px = p.x + 0.5
                        py = p.y + 0.5
                        dx = math.cos(ang)
                        dy = math.sin(ang)

                        step = self.ray_step
                        max_steps = int(self.max_ray_dist / step)
                        prevx = px
                        prevy = py

                        for i in range(1, max_steps + 1):
                                t1 = i * step
                                curx = px + dx * t1
                                cury = py + dy * t1

                                prev_cx = int(math.floor(prevx))
                                prev_cy = int(math.floor(prevy))
                                cur_cx = int(math.floor(curx))
                                cur_cy = int(math.floor(cury))

                                events = []
                                if cur_cx != prev_cx and abs(curx - prevx) > 1e-9:
                                        if curx > prevx:
                                                xb = prev_cx + 1.0
                                                side_dir = 'E'
                                        else:
                                                xb = float(prev_cx)
                                                side_dir = 'W'
                                        tx = (xb - prevx) / (curx - prevx)
                                        if 0.0 <= tx <= 1.0:
                                                y_at = prevy + (cury - prevy) * tx
                                                events.append((tx, xb, y_at, side_dir))

                                if cur_cy != prev_cy and abs(cury - prevy) > 1e-9:
                                        if cury > prevy:
                                                yb = prev_cy + 1.0
                                                side_dir = 'S'
                                        else:
                                                yb = float(prev_cy)
                                                side_dir = 'N'
                                        ty = (yb - prevy) / (cury - prevy)
                                        if 0.0 <= ty <= 1.0:
                                                x_at = prevx + (curx - prevx) * ty
                                                events.append((ty, x_at, yb, side_dir))

                                if events:
                                        events.sort(key=lambda e: e[0])
                                        for frac, _a, _b, side_dir in events:
                                                hit_dist = ((i - 1) * step) + (step * frac)
                                                info = self._edge_block_info(prev_cx, prev_cy, side_dir)
                                                if info['hit']:
                                                        return {
                                                                'dist': max(0.02, hit_dist),
                                                                'edge': info['edge'],
                                                                'side': 'vertical' if side_dir in ('E', 'W') else 'horizontal',
                                                        }

                                if (cur_cx != prev_cx or cur_cy != prev_cy):
                                        nc = room.get(cur_cx, cur_cy)
                                        if nc is None:
                                                return {'dist': max(0.02, t1), 'edge': {'type': EDGE_WALL}, 'side': 'void'}
                                        if nc.object_blocker:
                                                return {'dist': max(0.02, t1), 'edge': {'type': EDGE_WALL}, 'side': 'object'}

                                prevx = curx
                                prevy = cury

                        return {'dist': self.max_ray_dist, 'edge': {'type': EDGE_WALL}, 'side': 'far'}

                def _wall_color(self, edge, side, dist):
                        et = (edge or {}).get('type', EDGE_WALL)
                        if et == EDGE_DOOR:
                                ds = _door_state(edge)
                                if ds == DOOR_LOCKED:
                                        base = [130, 34, 34]
                                elif ds == DOOR_CLOSED:
                                        base = [110, 78, 48]
                                elif ds == DOOR_AJAR:
                                        base = [165, 125, 70]
                                else:
                                        base = [200, 160, 90]
                        elif et == EDGE_WINDOW_VIEW:
                                base = [80, 110, 145]
                        else:
                                base = [168, 168, 178]

                        shade = max(0.22, 1.0 - (dist / 14.0))
                        if side == 'vertical':
                                shade *= 0.90
                        elif side == 'horizontal':
                                shade *= 0.78
                        elif side == 'object':
                                shade *= 0.70

                        return (int(base[0] * shade), int(base[1] * shade), int(base[2] * shade), 255)

                def _record_render_ms(self, ms):
                        self.render_ms_last = float(ms)
                        self._render_ms_hist.append(float(ms))
                        if len(self._render_ms_hist) > 20:
                                self._render_ms_hist = self._render_ms_hist[-20:]
                        if self._render_ms_hist:
                                self.render_ms_avg = sum(self._render_ms_hist) / float(len(self._render_ms_hist))
                        else:
                                self.render_ms_avg = self.render_ms_last

                def render(self, w, h, st, at):
                        key = self._make_cache_key(w, h)
                        if (not self._dirty) and self._cache is not None and self._cache_key == key:
                                return self._cache

                        t0 = time.perf_counter()

                        import math
                        r = Render(w, h)
                        half = h // 2
                        p_pitch = getattr(self.world.player, "pitch", 0)
                        pitch_step_px = max(18, int(h * 0.075))
                        horizon_y = half - (p_pitch * pitch_step_px)
                        if horizon_y < 24:
                                horizon_y = 24
                        if horizon_y > h - 24:
                                horizon_y = h - 24

                        self._blit_solid(r, (18, 22, 30, 255), 0, 0, w, horizon_y, st, at)
                        self._blit_solid(r, (10, 12, 16, 255), 0, horizon_y, w, h - horizon_y, st, at)
                        self._blit_solid(r, (28, 32, 40, 160), 0, horizon_y - 4, w, 8, st, at)

                        cols = min(self.columns_cap, max(96, w // 6))
                        col_w = max(1, int(math.ceil(float(w) / cols)))
                        fov = math.radians(self.fov_deg)
                        base_ang = self._facing_angle_rad()

                        for ci in range(cols):
                                sx0 = ci * col_w
                                sx1 = min(w, sx0 + col_w)
                                if sx0 >= w:
                                        break

                                u = ((ci + 0.5) / float(cols)) * 2.0 - 1.0
                                ray_ang = base_ang + (u * (fov * 0.5))
                                hit = self._cast_ray(ray_ang)

                                corrected = max(self.near_clip_dist, hit['dist'] * math.cos(ray_ang - base_ang))

                                effective_dist = (corrected * max(0.05, float(self.cell_size_world))) + max(0.0, float(self.distance_soften))
                                if effective_dist < self.near_clip_dist:
                                        effective_dist = self.near_clip_dist

                                wall_h = int((h * self.proj_scale * max(0.05, float(self.wall_height_world))) / effective_dist)
                                if wall_h > h:
                                        wall_h = h

                                y0 = int(horizon_y - (wall_h / 2.0))

                                self._blit_solid(
                                        r,
                                        self._wall_color(hit.get('edge'), hit.get('side'), corrected),
                                        sx0, y0, sx1 - sx0, wall_h, st, at
                                )

                                if wall_h < h:
                                        fog = int(max(0, min(90, corrected * 6)))
                                        self._blit_solid(r, (0, 0, 0, min(90, fog)), sx0, 0, sx1 - sx0, y0, st, at)
                                        self._blit_solid(r, (0, 0, 0, min(110, fog + 10)), sx0, y0 + wall_h, sx1 - sx0, h - (y0 + wall_h), st, at)

                        cx = w // 2
                        cy = horizon_y
                        self._blit_solid(r, (240, 240, 240, 200), cx - 1, cy - 8, 2, 16, st, at)
                        self._blit_solid(r, (240, 240, 240, 200), cx - 8, cy - 1, 16, 2, st, at)

                        self._cache = r
                        self._cache_key = key
                        self._dirty = False

                        t1 = time.perf_counter()
                        self._record_render_ms((t1 - t0) * 1000.0)

                        return r

        def make_renderer(world):
                        return StepRayRenderer(world)