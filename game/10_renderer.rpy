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

                        # Boundary / door visual profile (render only)
                        self.door_height_ratio = 0.78
                        self.door_frame_ratio = 0.12
                        self.door_inset_ratio = 0.18
                        self.door_ajar_angle_deg = 36.0

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
                                self.door_height_ratio,
                                self.door_frame_ratio,
                                self.door_inset_ratio,
                                self.door_ajar_angle_deg,
                                tuple(self._active_surface_palette().get('floor_rgba', ())),
                                tuple(self._active_surface_palette().get('ceiling_rgba', ())),
                                self._active_surface_palette().get('zone_id'),
                        )

                def _blit_solid(self, r, color, x, y, ww, hh, st, at):
                        if ww <= 0 or hh <= 0:
                                return
                        s = rp.store.Solid(color, xysize=(ww, hh))
                        sr = render(s, ww, hh, st, at)
                        r.blit(sr, (int(x), int(y)))

                def _rgba_from_any(self, value, fallback=(96, 96, 96, 255)):
                        try:
                                if isinstance(value, (list, tuple)):
                                        if len(value) >= 4:
                                                return (int(value[0]), int(value[1]), int(value[2]), int(value[3]))
                                        if len(value) >= 3:
                                                return (int(value[0]), int(value[1]), int(value[2]), 255)
                                if isinstance(value, str):
                                        s = value.strip()
                                        if s.startswith("#"):
                                                s = s[1:]
                                        if len(s) == 3:
                                                s = (s[0] * 2) + (s[1] * 2) + (s[2] * 2)
                                        if len(s) == 6:
                                                return (
                                                        int(s[0:2], 16),
                                                        int(s[2:4], 16),
                                                        int(s[4:6], 16),
                                                        255,
                                                )
                                        if len(s) == 8:
                                                return (
                                                        int(s[0:2], 16),
                                                        int(s[2:4], 16),
                                                        int(s[4:6], 16),
                                                        int(s[6:8], 16),
                                                )
                        except Exception:
                                pass
                        return fallback

                def _mul_rgba(self, rgba, mul=1.0, alpha_mul=1.0):
                        m = float(mul)
                        a = float(alpha_mul)
                        if m < 0.0:
                                m = 0.0
                        if a < 0.0:
                                a = 0.0
                        if a > 1.0:
                                a = 1.0
                        return (
                                max(0, min(255, int(rgba[0] * m))),
                                max(0, min(255, int(rgba[1] * m))),
                                max(0, min(255, int(rgba[2] * m))),
                                max(0, min(255, int(rgba[3] * a))),
                        )

                def _active_zone(self):
                        room = getattr(self.world, "room", None)
                        player = getattr(self.world, "player", None)
                        if room is None or player is None:
                                return None
                        if hasattr(room, "get_zone_at"):
                                return room.get_zone_at(player.x, player.y)
                        zid = room.get_zone_id(player.x, player.y) if hasattr(room, "get_zone_id") else None
                        if zid is None:
                                return None
                        return room.get_zone(zid) if hasattr(room, "get_zone") else None

                def _active_surface_palette(self):
                        zone = self._active_zone()

                        ceiling_rgba = (18, 22, 30, 255)
                        floor_rgba = (24, 26, 32, 255)

                        if zone is not None:
                                fp = getattr(zone, "floor_profile", None)
                                cp = getattr(zone, "ceiling_profile", None)
                                is_interior = bool(getattr(zone, "is_interior", True))

                                if fp is not None:
                                        floor_rgba = self._rgba_from_any(
                                                getattr(fp, "color", None),
                                                fallback=floor_rgba,
                                        )
                                        floor_rgba = self._mul_rgba(
                                                floor_rgba,
                                                getattr(fp, "shade", 1.0),
                                                1.0,
                                        )

                                if cp is not None:
                                        ceiling_rgba = self._rgba_from_any(
                                                getattr(cp, "color", None),
                                                fallback=ceiling_rgba,
                                        )
                                        ceiling_rgba = self._mul_rgba(
                                                ceiling_rgba,
                                                getattr(cp, "shade", 1.0),
                                                1.0,
                                        )
                                elif not is_interior:
                                        ceiling_rgba = (90, 118, 154, 255)

                        return {
                                "zone_id": getattr(zone, "zone_id", None),
                                "floor_material": getattr(getattr(zone, "floor_profile", None), "material_id", None),
                                "ceiling_material": getattr(getattr(zone, "ceiling_profile", None), "material_id", None),
                                "floor_rgba": floor_rgba,
                                "floor_horizon_rgba": self._mul_rgba(floor_rgba, 0.72, 1.0),
                                "floor_near_rgba": self._mul_rgba(floor_rgba, 1.06, 1.0),
                                "ceiling_rgba": ceiling_rgba,
                                "ceiling_horizon_rgba": self._mul_rgba(ceiling_rgba, 0.82, 1.0),
                                "horizon_line_rgba": self._mul_rgba(ceiling_rgba, 0.55, 0.70),
                        }

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

                def _clamp01(self, v):
                        if v < 0.0:
                                return 0.0
                        if v > 1.0:
                                return 1.0
                        return float(v)

                def _cast_ray_from(self, ang, px, py):
                        import math
                        room = self.world.room
                        dx = math.cos(ang)
                        dy = math.sin(ang)

                        step = self.ray_step
                        max_steps = int(self.max_ray_dist / step)
                        prevx = float(px)
                        prevy = float(py)

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
                                                edge_u = self._clamp01(y_at - math.floor(y_at))
                                                events.append((tx, xb, y_at, side_dir, edge_u))

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
                                                edge_u = self._clamp01(x_at - math.floor(x_at))
                                                events.append((ty, x_at, yb, side_dir, edge_u))

                                if events:
                                        events.sort(key=lambda e: e[0])
                                        for frac, hit_x, hit_y, side_dir, edge_u in events:
                                                hit_dist = ((i - 1) * step) + (step * frac)
                                                info = self._edge_block_info(prev_cx, prev_cy, side_dir)
                                                if info['hit']:
                                                        return {
                                                                'dist': max(0.02, hit_dist),
                                                                'edge': info['edge'],
                                                                'side': 'vertical' if side_dir in ('E', 'W') else 'horizontal',
                                                                'edge_dir': side_dir,
                                                                'edge_u': edge_u,
                                                                'hit_x': hit_x,
                                                                'hit_y': hit_y,
                                                        }
                                                edge = info.get('edge') or {}
                                                if edge.get('type') == EDGE_DOOR:
                                                        return {
                                                                'dist': max(0.02, hit_dist),
                                                                'edge': edge,
                                                                'side': 'vertical' if side_dir in ('E', 'W') else 'horizontal',
                                                                'edge_dir': side_dir,
                                                                'edge_u': edge_u,
                                                                'hit_x': hit_x,
                                                                'hit_y': hit_y,
                                                        }

                                if (cur_cx != prev_cx or cur_cy != prev_cy):
                                        nc = room.get(cur_cx, cur_cy)
                                        if nc is None:
                                                return {'dist': max(0.02, t1), 'edge': {'type': EDGE_WALL}, 'side': 'void', 'edge_u': 0.5}
                                        if nc.object_blocker:
                                                return {'dist': max(0.02, t1), 'edge': {'type': EDGE_WALL}, 'side': 'object', 'edge_u': 0.5}

                                prevx = curx
                                prevy = cury

                        return {'dist': self.max_ray_dist, 'edge': {'type': EDGE_WALL}, 'side': 'far', 'edge_u': 0.5}

                def _cast_ray(self, ang):
                        p = self.world.player
                        return self._cast_ray_from(ang, p.x + 0.5, p.y + 0.5)

                def _wall_base_rgb(self, edge):
                        et = (edge or {}).get('type', EDGE_WALL)
                        if et == EDGE_DOOR:
                                ds = _door_state(edge)
                                if ds == DOOR_LOCKED:
                                        return (130, 34, 34)
                                if ds == DOOR_CLOSED:
                                        return (110, 78, 48)
                                if ds == DOOR_AJAR:
                                        return (165, 125, 70)
                                return (200, 160, 90)
                        if et == EDGE_WINDOW_VIEW:
                                return (80, 110, 145)
                        return (168, 168, 178)

                def _shaded_rgba(self, base_rgb, side, dist, extra=1.0):
                        shade = max(0.22, 1.0 - (dist / 14.0))
                        if side == 'vertical':
                                shade *= 0.90
                        elif side == 'horizontal':
                                shade *= 0.78
                        elif side == 'object':
                                shade *= 0.70
                        shade *= extra
                        if shade < 0.08:
                                shade = 0.08
                        if shade > 1.0:
                                shade = 1.0
                        return (
                                int(base_rgb[0] * shade),
                                int(base_rgb[1] * shade),
                                int(base_rgb[2] * shade),
                                255,
                        )

                def _wall_color(self, edge, side, dist):
                        return self._shaded_rgba(self._wall_base_rgb(edge), side, dist, 1.0)

                def _wall_metrics(self, corrected, screen_h, horizon_y, height_ratio=1.0):
                        effective_dist = (corrected * max(0.05, float(self.cell_size_world))) + max(0.0, float(self.distance_soften))
                        if effective_dist < self.near_clip_dist:
                                effective_dist = self.near_clip_dist
                        wall_h = int((screen_h * self.proj_scale * max(0.05, float(self.wall_height_world)) * max(0.05, float(height_ratio))) / effective_dist)
                        if wall_h > screen_h:
                                wall_h = screen_h
                        y0 = int(horizon_y - (wall_h / 2.0))
                        return y0, wall_h

                def _door_hinge_left(self, hit):
                        edge_dir = hit.get('edge_dir', 'E')
                        return edge_dir in ('E', 'N')

                def _door_leaf_span(self, door_state, hinge_left):
                        import math
                        frame = float(self.door_frame_ratio)
                        if frame < 0.04:
                                frame = 0.04
                        if frame > 0.30:
                                frame = 0.30
                        opening_left = frame
                        opening_right = 1.0 - frame
                        opening_w = max(0.08, opening_right - opening_left)

                        if door_state in (DOOR_AJAR, DOOR_OPEN):
                                angle_deg = float(self.door_ajar_angle_deg if door_state == DOOR_AJAR else max(65.0, self.door_ajar_angle_deg + 34.0))
                                if angle_deg < 0.0:
                                        angle_deg = 0.0
                                if angle_deg > 89.0:
                                        angle_deg = 89.0
                                proj_w = opening_w * math.cos(math.radians(angle_deg))
                                proj_w = max(0.03, min(opening_w, proj_w))
                                if hinge_left:
                                        return opening_left, opening_left + proj_w
                                return opening_right - proj_w, opening_right

                        return opening_left, opening_right

                def _door_column_layers(self, hit, corrected, screen_h, horizon_y):
                        edge = hit.get('edge') or {}
                        side = hit.get('side')
                        door_state = _door_state(edge)
                        hit_u = self._clamp01(hit.get('edge_u', 0.5))
                        hinge_left = self._door_hinge_left(hit)

                        wall_y0, wall_h = self._wall_metrics(corrected, screen_h, horizon_y, 1.0)
                        door_y0, door_h = self._wall_metrics(corrected, screen_h, horizon_y, float(self.door_height_ratio))
                        door_y1 = wall_y0 + wall_h
                        door_y0 = door_y1 - door_h

                        base_wall = self._wall_base_rgb({'type': EDGE_WALL})
                        base_door = self._wall_base_rgb(edge)

                        frame = float(self.door_frame_ratio)
                        if frame < 0.04:
                                frame = 0.04
                        if frame > 0.30:
                                frame = 0.30

                        leaf_l, leaf_r = self._door_leaf_span(door_state, hinge_left)
                        is_side_frame = (hit_u <= frame) or (hit_u >= (1.0 - frame))
                        is_leaf = (leaf_l <= hit_u <= leaf_r)
                        gap_open = (not is_side_frame) and (not is_leaf)

                        layers = []

                        wall_rgba = self._shaded_rgba(base_wall, side, corrected, 1.0)
                        lintel_rgba = wall_rgba
                        frame_rgba = wall_rgba

                        door_dark = 1.0 - (float(self.door_inset_ratio) * 0.45)
                        if door_dark < 0.60:
                                door_dark = 0.60

                        if is_side_frame:
                                layers.append((frame_rgba, wall_y0, wall_h))
                                return layers

                        if door_y0 > wall_y0:
                                layers.append((lintel_rgba, wall_y0, door_y0 - wall_y0))

                        if is_leaf:
                                if hinge_left:
                                        local_u = (hit_u - leaf_l) / max(0.001, (leaf_r - leaf_l))
                                else:
                                        local_u = (leaf_r - hit_u) / max(0.001, (leaf_r - leaf_l))
                                depth_mul = door_dark * (0.88 + (0.12 * local_u))
                                if door_state in (DOOR_AJAR, DOOR_OPEN):
                                        depth_mul *= 0.92
                                layers.append((self._shaded_rgba(base_door, side, corrected, depth_mul), door_y0, door_h))
                        elif not gap_open:
                                layers.append((wall_rgba, wall_y0, wall_h))

                        return layers

                def _is_passthrough_door_hit(self, hit):
                        edge = (hit or {}).get('edge') or {}
                        if edge.get('type') != EDGE_DOOR:
                                return False
                        return _door_state(edge) in (DOOR_AJAR, DOOR_OPEN) and ('hit_x' in hit) and ('hit_y' in hit)

                def _cast_ray_chain(self, ang):
                        import math
                        p = self.world.player
                        start_x = p.x + 0.5
                        start_y = p.y + 0.5
                        eps = max(0.03, self.ray_step * 1.2)
                        total_dist = 0.0
                        chain = []

                        for _ in range(6):
                                hit = self._cast_ray_from(ang, start_x, start_y)
                                local_dist = max(0.02, float(hit.get('dist', self.max_ray_dist)))
                                total_dist += local_dist

                                h = dict(hit)
                                h['dist_total'] = total_dist
                                chain.append(h)

                                if total_dist >= self.max_ray_dist:
                                        break
                                if not self._is_passthrough_door_hit(hit):
                                        break

                                start_x = hit['hit_x'] + (math.cos(ang) * eps)
                                start_y = hit['hit_y'] + (math.sin(ang) * eps)
                                total_dist += eps

                        return chain
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

                        palette = self._active_surface_palette()

                        self._blit_solid(r, palette['ceiling_rgba'], 0, 0, w, horizon_y, st, at)
                        self._blit_solid(r, palette['floor_rgba'], 0, horizon_y, w, h - horizon_y, st, at)

                        band_top_h = min(18, max(0, horizon_y))
                        if band_top_h > 0:
                                self._blit_solid(r, palette['ceiling_horizon_rgba'], 0, horizon_y - band_top_h, w, band_top_h, st, at)

                        band_bottom_h = min(18, max(0, h - horizon_y))
                        if band_bottom_h > 0:
                                self._blit_solid(r, palette['floor_horizon_rgba'], 0, horizon_y, w, band_bottom_h, st, at)

                        near_floor_h = min(22, max(0, h - horizon_y))
                        if near_floor_h > 0:
                                self._blit_solid(r, palette['floor_near_rgba'], 0, h - near_floor_h, w, near_floor_h, st, at)

                        self._blit_solid(r, palette['horizon_line_rgba'], 0, max(0, horizon_y - 2), w, min(4, h), st, at)

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
                                hit_chain = self._cast_ray_chain(ray_ang)
                                near_hit = hit_chain[0]

                                corrected = max(self.near_clip_dist, near_hit['dist_total'] * math.cos(ray_ang - base_ang))
                                wall_y0, wall_h = self._wall_metrics(corrected, h, horizon_y, 1.0)

                                layers = []

                                for hit in reversed(hit_chain):
                                        hit_corrected = max(self.near_clip_dist, hit['dist_total'] * math.cos(ray_ang - base_ang))
                                        edge = hit.get('edge') or {}
                                        if edge.get('type') == EDGE_DOOR:
                                                layers.extend(self._door_column_layers(hit, hit_corrected, h, horizon_y))
                                        else:
                                                ly0, lh = self._wall_metrics(hit_corrected, h, horizon_y, 1.0)
                                                layers.append((self._wall_color(edge, hit.get('side'), hit_corrected), ly0, lh))

                                for color, ly, lh in layers:
                                        self._blit_solid(r, color, sx0, ly, sx1 - sx0, lh, st, at)

                                if wall_h < h:
                                        fog = int(max(0, min(90, corrected * 6)))
                                        self._blit_solid(r, (0, 0, 0, min(90, fog)), sx0, 0, sx1 - sx0, wall_y0, st, at)
                                        self._blit_solid(r, (0, 0, 0, min(110, fog + 10)), sx0, wall_y0 + wall_h, sx1 - sx0, h - (wall_y0 + wall_h), st, at)

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