# 06_core_game.rpy
# ============================================================
# Core: Game controller / facade (debug-safe)
# + movement: W/S forward/back, A/D strafe, Q/E turn, F interact
# + compat doors API (old UI + new interact)
# + renderer refresh after every action
# ============================================================

init -20 python:
        import renpy as rp
        import random


        def _yc_surface(material_id, color, shade=1.0, tags=None, texture_id=None, meta=None):
                return {
                        "material_id": material_id,
                        "color": color,
                        "shade": float(shade),
                        "texture_id": texture_id,
                        "tags": list(tags or []),
                        "meta": dict(meta or {}),
                }



        def _yc_fill_generated_room_defaults(room, zone_id=1, zone_name="generated", zone_type="generated"):
                room.define_zone(zone_id, name=zone_name, zone_type=zone_type)
                for y in range(room.h):
                        for x in range(room.w):
                                room.set_zone(x, y, zone_id)
                for y in range(room.h):
                        for x in range(room.w):
                                for d in DIRS:
                                        room.set_boundary_mirrored(x, y, d, EDGE_WALL)
                room.rebuild_zone_memberships()
                room.refresh_all_boundary_zone_links()
                return room

        def _yc_link_cells(room, ax, ay, bx, by, door_state=None):
                dx = int(bx) - int(ax)
                dy = int(by) - int(ay)
                if abs(dx) + abs(dy) != 1:
                        return False
                if dx == 1:
                        d = "E"
                elif dx == -1:
                        d = "W"
                elif dy == 1:
                        d = "S"
                else:
                        d = "N"
                if door_state is None:
                        return room.set_boundary_mirrored(ax, ay, d, EDGE_OPEN)
                return room.set_boundary_mirrored(ax, ay, d, EDGE_DOOR, door_state=door_state)

        def _yc_make_world_from_template(room, player_x, player_y, facing="E"):
                try:
                        W = generate_demo_room()
                except Exception:
                        W = yc_generate_house_floor_mvp_world()

                W.room = room

                p = getattr(W, "player", None)
                if p is None:
                        W.player = Player(player_x, player_y, facing)
                        p = W.player
                else:
                        p.x = int(player_x)
                        p.y = int(player_y)
                        p.facing = str(facing)
                        if hasattr(p, "pitch"):
                                p.pitch = 0

                W.tick = 0
                W.last_move_result = "spawn"

                try:
                        room.rebuild_zone_memberships()
                        room.refresh_all_boundary_zone_links()
                except Exception:
                        pass

                if hasattr(W, "_touch_logic"):
                        try:
                                W._touch_logic()
                        except Exception:
                                pass
                return W

        def _yc_count_boundaries(room, boundary_type):
                n = 0
                for be in room.boundaries.values():
                        if getattr(be, "boundary_type", None) == boundary_type:
                                n += 1
                return n

        def _yc_paint_zone_rect(room, x0, y0, x1, y1, zone_id):
                x0 = int(x0)
                y0 = int(y0)
                x1 = int(x1)
                y1 = int(y1)
                if x0 > x1:
                        x0, x1 = x1, x0
                if y0 > y1:
                        y0, y1 = y1, y0
                for y in range(y0, y1 + 1):
                        for x in range(x0, x1 + 1):
                                if room.in_bounds(x, y):
                                        room.set_zone(x, y, zone_id)

        def _yc_open_same_zone_neighbors(room):
                for y in range(room.h):
                        for x in range(room.w):
                                zid = room.get_zone_id(x, y)
                                if zid is None:
                                        continue
                                if room.in_bounds(x + 1, y) and room.get_zone_id(x + 1, y) == zid:
                                        room.set_boundary_mirrored(x, y, "E", EDGE_OPEN)
                                if room.in_bounds(x, y + 1) and room.get_zone_id(x, y + 1) == zid:
                                        room.set_boundary_mirrored(x, y, "S", EDGE_OPEN)

        def yc_generate_vertical_house_world():
                room = Room(15, 11, name="Generated House Vertical Core")

                if not hasattr(room, "define_level"):
                        raise Exception("Vertical core not installed. Apply 01_core_room vertical_links patch first.")

                # Levels: current renderer still shows one 2D floor, but the world core
                # now knows this house has an upper floor connected by a stairwell.
                room.define_level(0, name="ground", elevation=0.0, floor_z=0.0, ceiling_z=3.0)
                room.define_level(1, name="first",  elevation=3.0, floor_z=3.0, ceiling_z=6.0)

                # Ground floor zones with explicit floor/ceiling profiles.
                room.define_zone(
                        10,
                        name="living_room_0",
                        zone_type="room",
                        level_id=0,
                        tags=["house", "ground", "living"],
                        floor_profile=_yc_surface("living_wood", "#8a6d4d", shade=1.00, tags=["interior", "wood", "living"]),
                        ceiling_profile=_yc_surface("painted_ceiling", "#d8d5cf", shade=1.00, tags=["interior", "ceiling"]),
                        ceiling_height=3.0,
                )
                room.define_zone(
                        11,
                        name="hall_0",
                        zone_type="hall",
                        level_id=0,
                        tags=["house", "ground", "hall"],
                        floor_profile=_yc_surface("hall_runner", "#7a705d", shade=0.98, tags=["interior", "hall"]),
                        ceiling_profile=_yc_surface("painted_ceiling", "#d4d1ca", shade=0.99, tags=["interior", "ceiling"]),
                        ceiling_height=2.9,
                )
                room.define_zone(
                        12,
                        name="kitchen_0",
                        zone_type="kitchen",
                        level_id=0,
                        tags=["house", "ground", "kitchen"],
                        floor_profile=_yc_surface("kitchen_tile", "#8f9398", shade=0.98, tags=["interior", "tile", "kitchen"]),
                        ceiling_profile=_yc_surface("painted_ceiling", "#d7d4cd", shade=1.00, tags=["interior", "ceiling"]),
                        ceiling_height=2.85,
                )
                room.define_zone(
                        20,
                        name="stairwell_0",
                        zone_type="stairwell",
                        level_id=0,
                        tags=["house", "ground", "vertical", "stairs"],
                        floor_profile=_yc_surface("stairs_wood", "#6f5d47", shade=0.96, tags=["interior", "stairs"]),
                        ceiling_profile=_yc_surface("stair_ceiling", "#cbc8c1", shade=0.98, tags=["interior", "ceiling", "stairwell"]),
                        ceiling_height=4.8,
                )

                # Upper floor zones are metadata-first for now, but already carry surface profiles.
                upper_footprint = [(6, 1), (7, 1), (8, 1), (6, 2), (7, 2), (8, 2), (6, 3), (7, 3), (8, 3)]
                room.define_zone(
                        110,
                        name="hall_1",
                        zone_type="hall",
                        level_id=1,
                        tags=["house", "upper", "hall"],
                        meta={"footprint_cells": upper_footprint},
                        floor_profile=_yc_surface("hall_runner", "#7a705d", shade=0.98, tags=["interior", "hall"]),
                        ceiling_profile=_yc_surface("painted_ceiling", "#d4d1ca", shade=0.99, tags=["interior", "ceiling"]),
                        ceiling_height=2.8,
                )
                room.define_zone(
                        111,
                        name="bedroom_a_1",
                        zone_type="room",
                        level_id=1,
                        tags=["house", "upper", "bedroom"],
                        meta={"footprint_cells": [(1, 1), (2, 1), (3, 1)]},
                        floor_profile=_yc_surface("bedroom_wood", "#866a50", shade=1.00, tags=["interior", "wood", "bedroom"]),
                        ceiling_profile=_yc_surface("painted_ceiling", "#ddd9d2", shade=1.00, tags=["interior", "ceiling"]),
                        ceiling_height=2.75,
                )
                room.define_zone(
                        112,
                        name="bedroom_b_1",
                        zone_type="room",
                        level_id=1,
                        tags=["house", "upper", "bedroom"],
                        meta={"footprint_cells": [(11, 1), (12, 1), (13, 1)]},
                        floor_profile=_yc_surface("bedroom_wood", "#866a50", shade=1.00, tags=["interior", "wood", "bedroom"]),
                        ceiling_profile=_yc_surface("painted_ceiling", "#ddd9d2", shade=1.00, tags=["interior", "ceiling"]),
                        ceiling_height=2.75,
                )
                room.define_zone(
                        120,
                        name="stairwell_1",
                        zone_type="stairwell",
                        level_id=1,
                        tags=["house", "upper", "vertical", "stairs"],
                        meta={"footprint_cells": upper_footprint},
                        floor_profile=_yc_surface("stairs_wood", "#6f5d47", shade=0.96, tags=["interior", "stairs"]),
                        ceiling_profile=_yc_surface("stair_ceiling", "#cbc8c1", shade=0.98, tags=["interior", "ceiling", "stairwell"]),
                        ceiling_height=4.8,
                )

                # Paint current visible floor.
                _yc_paint_zone_rect(room, 1, 1, 5, 4, 10)   # living
                _yc_paint_zone_rect(room, 1, 5, 13, 9, 11)  # hall / corridor
                _yc_paint_zone_rect(room, 9, 1, 13, 4, 12)  # kitchen
                _yc_paint_zone_rect(room, 6, 1, 8, 4, 20)   # stairwell footprint on ground floor

                # Same-zone interiors are open.
                _yc_open_same_zone_neighbors(room)

                # Inter-zone connections.
                room.set_boundary_mirrored(3, 4, "S", EDGE_DOOR, door_state=DOOR_CLOSED)   # hall <-> living
                room.set_boundary_mirrored(11, 4, "S", EDGE_DOOR, door_state=DOOR_CLOSED)  # hall <-> kitchen
                room.set_boundary_mirrored(7, 4, "S", EDGE_OPEN)                            # hall <-> stairwell

                room.rebuild_zone_memberships()
                room.refresh_all_boundary_zone_links()

                stair_cells = [(6, 1), (7, 1), (8, 1), (6, 2), (7, 2), (8, 2), (6, 3), (7, 3), (8, 3), (6, 4), (7, 4), (8, 4)]
                room.build_ceiling_opening(
                        "stairs_void_0_1",
                        level_a=0,
                        level_b=1,
                        cells=stair_cells,
                        opening_type="stair_void",
                        blocks_movement=True,
                        blocks_vision=False,
                        blocks_fall=False,
                )

                room.build_vertical_link(
                        "stairs_main",
                        zone_a=20,
                        zone_b=120,
                        link_type="stairs",
                        entry_cells_a=[(7, 3), (7, 4)],
                        entry_cells_b=[(7, 3), (7, 4)],
                        is_bidirectional=True,
                        travel_mode="walk",
                        travel_time=1.5,
                        shaft_zone_ids=[20, 120],
                        meta={"style": "two_flight_house_stairs", "note": "Current renderer still shows only floor 0 footprint."},
                )

                room.build_visibility_portal(
                        "stairs_look_up",
                        from_zone_id=20,
                        to_zone_id=120,
                        opening_id="stairs_void_0_1",
                        portal_type="vertical_void",
                        meta={"direction": "up"},
                )
                room.build_visibility_portal(
                        "stairs_look_down",
                        from_zone_id=120,
                        to_zone_id=20,
                        opening_id="stairs_void_0_1",
                        portal_type="vertical_void",
                        meta={"direction": "down"},
                )

                return _yc_make_world_from_template(room, 7, 8, facing="N")

        def yc_vertical_house_summary(world=None):
                try:
                        W = world or yc_generate_vertical_house_world()
                        r = W.room
                        levels_n = len(getattr(r, "levels", {}) or {})
                        links_n = len(getattr(r, "vertical_links", []) or [])
                        openings_n = len(getattr(r, "ceiling_openings", {}) or {})
                        portals_n = len(getattr(r, "visibility_portals", {}) or {})
                        rep = r.vertical_core_checker() if hasattr(r, "vertical_core_checker") else {"ok": False, "errors": ["missing_vertical_core_checker"]}
                        srep = r.surface_core_checker() if hasattr(r, "surface_core_checker") else {"ok": False, "errors": ["missing_surface_core_checker"]}
                        return "Vertical house: levels=%s links=%s openings=%s portals=%s vertical_ok=%s surface_ok=%s" % (
                                levels_n,
                                links_n,
                                openings_n,
                                portals_n,
                                bool(rep.get("ok", False)),
                                bool(srep.get("ok", False)),
                        )
                except Exception as e:
                        return "Vertical house summary EXC: %r" % (e,)

        def yc_generate_tunnel_world(with_doors=False, length=17):
                length = int(length)
                if length < 9:
                        length = 9
                if length > 39:
                        length = 39

                h = 7
                w = length
                mid = h // 2

                room = Room(w, h, name=("Generated Tunnel Doors" if with_doors else "Generated Tunnel"))
                _yc_fill_generated_room_defaults(room, zone_name=("tunnel_doors" if with_doors else "tunnel"), zone_type="corridor")

                for x in range(1, w - 1):
                        if with_doors and x in (4, 8, 12, w - 3):
                                _yc_link_cells(room, x - 1, mid, x, mid, door_state=DOOR_CLOSED)
                        else:
                                _yc_link_cells(room, x - 1, mid, x, mid)

                if mid - 1 >= 1:
                        _yc_link_cells(room, w - 2, mid, w - 2, mid - 1)
                if mid + 1 <= h - 2:
                        _yc_link_cells(room, w - 2, mid, w - 2, mid + 1)

                return _yc_make_world_from_template(room, 1, mid, facing="E")

        def yc_generate_maze_world(with_doors=False, w=11, h=11, seed=1337):
                w = int(w)
                h = int(h)
                if w < 7:
                        w = 7
                if h < 7:
                        h = 7
                if w > 19:
                        w = 19
                if h > 19:
                        h = 19

                rng = random.Random(int(seed))
                room = Room(w, h, name=("Generated Maze Doors" if with_doors else "Generated Maze"))
                _yc_fill_generated_room_defaults(room, zone_name=("maze_doors" if with_doors else "maze"), zone_type="maze")

                start = (1, 1)
                stack = [start]
                visited = set([start])
                parent = {start: None}

                while stack:
                        cx, cy = stack[-1]
                        opts = []
                        for d in DIRS:
                                dx, dy = DIR_VEC[d]
                                nx = cx + dx
                                ny = cy + dy
                                if 1 <= nx <= (w - 2) and 1 <= ny <= (h - 2) and (nx, ny) not in visited:
                                        opts.append((nx, ny))
                        rng.shuffle(opts)
                        if not opts:
                                stack.pop()
                                continue
                        nx, ny = opts[0]
                        visited.add((nx, ny))
                        parent[(nx, ny)] = (cx, cy)
                        _yc_link_cells(room, cx, cy, nx, ny)
                        stack.append((nx, ny))

                if with_doors:
                        far = start
                        far_dist = 0
                        for cell in visited:
                                cur = cell
                                dd = 0
                                while cur is not None and cur != start:
                                        cur = parent.get(cur)
                                        dd += 1
                                if dd > far_dist:
                                        far = cell
                                        far_dist = dd

                        path = []
                        cur = far
                        while cur is not None:
                                path.append(cur)
                                cur = parent.get(cur)
                        path.reverse()

                        for i in range(3, len(path), 4):
                                a = path[i - 1]
                                b = path[i]
                                _yc_link_cells(room, a[0], a[1], b[0], b[1], door_state=DOOR_CLOSED)

                return _yc_make_world_from_template(room, start[0], start[1], facing="E")

        class Game(object):
                def __init__(self):
                        self.world = yc_generate_house_floor_mvp_world()

                        self.view = None
                        self.renderer = None

                        self.show_controls = True
                        self.show_map = True
                        self.show_log = False
                        self.show_tests = False
                        self.show_render_tune = False
                        self.show_generator_ui = False
                        self.show_panel = False
                        self.show_status = True

                        self.log = []
                        self.log_page_size = 10
                        self.log_page_start = 0
                        self.test_results = []
                        self.debug_token_colors = {
                                "OK": "#57d957",
                                "FAIL": "#ff5a5a",
                                "ON": "#57d957",
                                "OFF": "#ff5a5a",
                        }

                        self._log("Game init OK")
                        self._log("World: %s" % self.world.room.name)
                        self._log("Input: W/S/A/D move, Q/E turn, F interact, 1 demo, 2 house, 3 maze, 4 maze+doors, 5 tunnel, 6 tunnel+doors, 7 vertical house")

                # --------------------------------------------------
                # Core helpers
                # --------------------------------------------------
                def _refresh_ui(self):
                        try:
                                rp.restart_interaction()
                        except Exception:
                                pass

                def _log(self, msg):
                        try:
                                tick = getattr(self.world, "tick", 0)
                        except Exception:
                                tick = 0
                        self.log.append("[t%s] %s" % (tick, msg))
                        try:
                                if self.log_page_start + int(self.log_page_size) >= max(0, len(self.log) - 1):
                                        self.log_page_latest()
                        except Exception:
                                pass

                def debug_markup_text(self, line):
                        try:
                                out = str(line)
                        except Exception:
                                out = "%r" % (line,)
                        for token, color in getattr(self, "debug_token_colors", {}).items():
                                out = out.replace(token, "{color=%s}%s{/color}" % (color, token))
                        return out

                def toggle_panel(self):
                        self.show_panel = not getattr(self, "show_panel", True)
                        self._refresh_ui()

                def toggle_status(self):
                        self.show_status = not getattr(self, "show_status", True)
                        self._refresh_ui()

                def _ensure_log_page_state(self):
                        if not hasattr(self, "log_page_size") or int(getattr(self, "log_page_size", 10)) <= 0:
                                self.log_page_size = 10
                        if not hasattr(self, "log_page_start"):
                                self.log_page_start = 0
                        max_start = max(0, len(self.log) - int(self.log_page_size))
                        self.log_page_start = max(0, min(int(self.log_page_start), max_start))

                def log_page_latest(self):
                        self._ensure_log_page_state()
                        self.log_page_start = max(0, len(self.log) - int(self.log_page_size))
                        self._refresh_ui()

                def log_page_oldest(self):
                        self._ensure_log_page_state()
                        self.log_page_start = 0
                        self._refresh_ui()

                def log_page_older(self):
                        self._ensure_log_page_state()
                        self.log_page_start = max(0, int(self.log_page_start) - int(self.log_page_size))
                        self._refresh_ui()

                def log_page_newer(self):
                        self._ensure_log_page_state()
                        max_start = max(0, len(self.log) - int(self.log_page_size))
                        self.log_page_start = min(max_start, int(self.log_page_start) + int(self.log_page_size))
                        self._refresh_ui()

                def can_log_page_older(self):
                        self._ensure_log_page_state()
                        return int(self.log_page_start) > 0

                def can_log_page_newer(self):
                        self._ensure_log_page_state()
                        return int(self.log_page_start) + int(self.log_page_size) < len(self.log)

                def log_rows_for_ui(self):
                        self._ensure_log_page_state()
                        start = int(self.log_page_start)
                        end = min(len(self.log), start + int(self.log_page_size))
                        rows = []
                        for line in self.log[start:end]:
                                rows.append(self.debug_markup_text(line))
                        return rows

                def log_page_label(self):
                        self._ensure_log_page_state()
                        total = len(self.log)
                        if total <= 0:
                                return "0-0 / 0"
                        start = int(self.log_page_start)
                        end = min(total, start + int(self.log_page_size))
                        return "%d-%d / %d" % (start + 1, end, total)

                def bind_renderer(self, renderer_obj):
                        self.renderer = renderer_obj
                        self.view = renderer_obj

                        loaded_saved = False
                        try:
                                loaded_saved = self.load_saved_render_tune(announce=False)
                        except Exception:
                                loaded_saved = False

                        if not loaded_saved:
                                self._notify_renderer("bind", force=True)

                        self._log("Renderer bound%s" % (" + saved tune" if loaded_saved else ""))
                        self._refresh_ui()
                        return True

                def _notify_renderer(self, reason="state", force=False):
                        if self.renderer is None:
                                return False

                        try:
                                if hasattr(self.renderer, "world"):
                                        self.renderer.world = self.world

                                if hasattr(self.renderer, "_cache"):
                                        self.renderer._cache = None
                                if hasattr(self.renderer, "_cache_key"):
                                        self.renderer._cache_key = None
                                if hasattr(self.renderer, "_dirty"):
                                        self.renderer._dirty = True

                                if hasattr(self.renderer, "on_world_changed"):
                                        return bool(self.renderer.on_world_changed(reason=reason, force=force))

                                if hasattr(self.renderer, "mark_dirty"):
                                        self.renderer.mark_dirty()
                                        return True

                        except Exception as e:
                                self._log("Renderer notify EXC: %r" % (e,))

                        return False

                # --------------------------------------------------
                # UI toggles
                # --------------------------------------------------
                def toggle_controls(self):
                        self.show_controls = not self.show_controls
                        self._refresh_ui()

                def toggle_map(self):
                        self.show_map = not self.show_map
                        self._refresh_ui()

                def toggle_log(self):
                        self.show_log = not self.show_log
                        self._refresh_ui()

                def toggle_tests(self):
                        self.show_tests = not self.show_tests
                        self._refresh_ui()

                def toggle_render_tune(self):
                        self.show_render_tune = not self.show_render_tune
                        self._refresh_ui()

                def toggle_generator_ui(self):
                        self.show_generator_ui = not self.show_generator_ui
                        self._log("Generator UI: %s" % ("ON" if self.show_generator_ui else "OFF"))
                        self._refresh_ui()

                # --------------------------------------------------
                # Renderer tuning (if renderer exposes fields)
                # --------------------------------------------------
                def _renderer_vals(self):
                        r = self.renderer
                        if r is None:
                                return None
                        return {
                                "fov_deg": float(getattr(r, "fov_deg", 74.0)),
                                "proj_scale": float(getattr(r, "proj_scale", 0.58)),
                                "near_clip_dist": float(getattr(r, "near_clip_dist", 0.18)),
                                "wall_height_world": float(getattr(r, "wall_height_world", 1.0)),
                                "cell_size_world": float(getattr(r, "cell_size_world", 1.0)),
                                "distance_soften": float(getattr(r, "distance_soften", 0.2)),
                                "door_height_ratio": float(getattr(r, "door_height_ratio", 0.78)),
                                "door_frame_ratio": float(getattr(r, "door_frame_ratio", 0.12)),
                                "door_inset_ratio": float(getattr(r, "door_inset_ratio", 0.18)),
                                "door_ajar_angle_deg": float(getattr(r, "door_ajar_angle_deg", 36.0)),
                                "columns_cap": int(getattr(r, "columns_cap", 220)),
                                "render_ms_last": float(getattr(r, "render_ms_last", 0.0)),
                                "render_ms_avg": float(getattr(r, "render_ms_avg", 0.0)),
                        }

                def _renderer_tune_keys(self):
                        return [
                                "fov_deg",
                                "proj_scale",
                                "near_clip_dist",
                                "wall_height_world",
                                "cell_size_world",
                                "distance_soften",
                                "door_height_ratio",
                                "door_frame_ratio",
                                "door_inset_ratio",
                                "door_ajar_angle_deg",
                                "columns_cap",
                        ]

                def _get_saved_renderer_vals(self):
                        try:
                                p = getattr(rp.store, "persistent", None)
                                if p is None:
                                        return None
                                data = getattr(p, "yc_render_tune_v1", None)
                                if not isinstance(data, dict):
                                        return None

                                out = {}
                                for k in self._renderer_tune_keys():
                                        if k in data:
                                                out[k] = data[k]
                                if not out:
                                        return None
                                return out
                        except Exception as e:
                                self._log("Render tune persistent read EXC: %r" % (e,))
                                return None

                def has_saved_render_tune(self):
                        return self._get_saved_renderer_vals() is not None

                def save_render_tune(self, announce=True):
                        vals = self._renderer_vals()
                        if not vals:
                                if announce:
                                        self._log("Render tune save skipped: no renderer")
                                self._refresh_ui()
                                return False

                        data = {}
                        for k in self._renderer_tune_keys():
                                if k in vals:
                                        data[k] = vals[k]

                        try:
                                p = getattr(rp.store, "persistent", None)
                                if p is None:
                                        if announce:
                                                self._log("Render tune save skipped: persistent unavailable")
                                        self._refresh_ui()
                                        return False

                                setattr(p, "yc_render_tune_v1", data)
                                try:
                                        rp.save_persistent()
                                except Exception:
                                        pass

                                if announce:
                                        self._log("Render tune saved")
                                self._refresh_ui()
                                return True

                        except Exception as e:
                                self._log("Render tune save EXC: %r" % (e,))
                                self._refresh_ui()
                                return False

                def load_saved_render_tune(self, announce=True):
                        data = self._get_saved_renderer_vals()
                        if not data:
                                if announce:
                                        self._log("Render tune load skipped: no saved profile")
                                self._refresh_ui()
                                return False

                        ok = self._apply_renderer_vals(data, "render_load_saved")
                        if ok and announce:
                                self._log("Render tune loaded")
                        return ok

                def clear_saved_render_tune(self):
                        try:
                                p = getattr(rp.store, "persistent", None)
                                if p is None:
                                        self._log("Render tune clear skipped: persistent unavailable")
                                        self._refresh_ui()
                                        return False

                                setattr(p, "yc_render_tune_v1", None)
                                try:
                                        rp.save_persistent()
                                except Exception:
                                        pass

                                self._log("Render tune saved profile cleared")
                                self._refresh_ui()
                                return True

                        except Exception as e:
                                self._log("Render tune clear EXC: %r" % (e,))
                                self._refresh_ui()
                                return False

                def _apply_renderer_vals(self, updates, reason="render_tune"):
                        r = self.renderer
                        if r is None:
                                return False

                        try:
                                if "fov_deg" in updates and hasattr(r, "fov_deg"):
                                        v = float(updates["fov_deg"])
                                        if v < 40.0: v = 40.0
                                        if v > 110.0: v = 110.0
                                        r.fov_deg = v

                                if "proj_scale" in updates and hasattr(r, "proj_scale"):
                                        v = float(updates["proj_scale"])
                                        if v < 0.20: v = 0.20
                                        if v > 1.40: v = 1.40
                                        r.proj_scale = v

                                if "near_clip_dist" in updates and hasattr(r, "near_clip_dist"):
                                        v = float(updates["near_clip_dist"])
                                        if v < 0.05: v = 0.05
                                        if v > 0.50: v = 0.50
                                        r.near_clip_dist = v

                                if "wall_height_world" in updates and hasattr(r, "wall_height_world"):
                                        v = float(updates["wall_height_world"])
                                        if v < 0.20: v = 0.20
                                        if v > 3.50: v = 3.50
                                        r.wall_height_world = v

                                if "cell_size_world" in updates and hasattr(r, "cell_size_world"):
                                        v = float(updates["cell_size_world"])
                                        if v < 0.20: v = 0.20
                                        if v > 3.50: v = 3.50
                                        r.cell_size_world = v

                                if "distance_soften" in updates and hasattr(r, "distance_soften"):
                                        v = float(updates["distance_soften"])
                                        if v < 0.0: v = 0.0
                                        if v > 2.0: v = 2.0
                                        r.distance_soften = v

                                if "door_height_ratio" in updates and hasattr(r, "door_height_ratio"):
                                        v = float(updates["door_height_ratio"])
                                        if v < 0.45: v = 0.45
                                        if v > 0.98: v = 0.98
                                        r.door_height_ratio = v

                                if "door_frame_ratio" in updates and hasattr(r, "door_frame_ratio"):
                                        v = float(updates["door_frame_ratio"])
                                        if v < 0.04: v = 0.04
                                        if v > 0.30: v = 0.30
                                        r.door_frame_ratio = v

                                if "door_inset_ratio" in updates and hasattr(r, "door_inset_ratio"):
                                        v = float(updates["door_inset_ratio"])
                                        if v < 0.0: v = 0.0
                                        if v > 0.60: v = 0.60
                                        r.door_inset_ratio = v

                                if "door_ajar_angle_deg" in updates and hasattr(r, "door_ajar_angle_deg"):
                                        v = float(updates["door_ajar_angle_deg"])
                                        if v < 0.0: v = 0.0
                                        if v > 89.0: v = 89.0
                                        r.door_ajar_angle_deg = v

                                if "columns_cap" in updates and hasattr(r, "columns_cap"):
                                        v = int(updates["columns_cap"])
                                        if v < 48: v = 48
                                        if v > 1200: v = 1200
                                        r.columns_cap = v

                                self._notify_renderer(reason, force=True)
                                self._refresh_ui()
                                return True

                        except Exception as e:
                                self._log("Render tune EXC: %r" % (e,))
                                self._refresh_ui()
                                return False

                def tune_fov_minus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"fov_deg": vals["fov_deg"] - 4.0}, "fov-")

                def tune_fov_plus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"fov_deg": vals["fov_deg"] + 4.0}, "fov+")

                def tune_proj_minus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"proj_scale": vals["proj_scale"] - 0.04}, "proj-")

                def tune_proj_plus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"proj_scale": vals["proj_scale"] + 0.04}, "proj+")

                def tune_near_minus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"near_clip_dist": vals["near_clip_dist"] - 0.02}, "near-")

                def tune_near_plus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"near_clip_dist": vals["near_clip_dist"] + 0.02}, "near+")

                def tune_wallh_minus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"wall_height_world": vals["wall_height_world"] - 0.10}, "wallh-")

                def tune_wallh_plus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"wall_height_world": vals["wall_height_world"] + 0.10}, "wallh+")

                def tune_cellm_minus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"cell_size_world": vals["cell_size_world"] - 0.10}, "cellm-")

                def tune_cellm_plus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"cell_size_world": vals["cell_size_world"] + 0.10}, "cellm+")

                def tune_soft_minus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"distance_soften": vals["distance_soften"] - 0.05}, "soft-")

                def tune_soft_plus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"distance_soften": vals["distance_soften"] + 0.05}, "soft+")

                def tune_doorh_minus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"door_height_ratio": vals["door_height_ratio"] - 0.02}, "doorh-")

                def tune_doorh_plus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"door_height_ratio": vals["door_height_ratio"] + 0.02}, "doorh+")

                def tune_frame_minus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"door_frame_ratio": vals["door_frame_ratio"] - 0.01}, "frame-")

                def tune_frame_plus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"door_frame_ratio": vals["door_frame_ratio"] + 0.01}, "frame+")

                def tune_inset_minus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"door_inset_ratio": vals["door_inset_ratio"] - 0.02}, "inset-")

                def tune_inset_plus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"door_inset_ratio": vals["door_inset_ratio"] + 0.02}, "inset+")

                def tune_ajar_minus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"door_ajar_angle_deg": vals["door_ajar_angle_deg"] - 3.0}, "ajar-")

                def tune_ajar_plus(self):
                        vals = self._renderer_vals()
                        if vals: self._apply_renderer_vals({"door_ajar_angle_deg": vals["door_ajar_angle_deg"] + 3.0}, "ajar+")

                def tune_cols_minus(self):
                        vals = self._renderer_vals()
                        if vals:
                                cur = vals["columns_cap"]
                                step = 32 if cur >= 256 else 16
                                self._apply_renderer_vals({"columns_cap": cur - step}, "cols-")

                def tune_cols_plus(self):
                        vals = self._renderer_vals()
                        if vals:
                                cur = vals["columns_cap"]
                                step = 32 if cur >= 256 else 16
                                self._apply_renderer_vals({"columns_cap": cur + step}, "cols+")

                def tune_render_reset(self):
                        self._apply_renderer_vals({
                                "fov_deg": 74.0,
                                "proj_scale": 0.58,
                                "near_clip_dist": 0.18,
                                "wall_height_world": 1.0,
                                "cell_size_world": 1.0,
                                "distance_soften": 0.20,
                                "door_height_ratio": 0.78,
                                "door_frame_ratio": 0.12,
                                "door_inset_ratio": 0.18,
                                "door_ajar_angle_deg": 36.0,
                                "columns_cap": 220,
                        }, "render_reset")

                def tune_render_home(self):
                        self._apply_renderer_vals({
                                "fov_deg": 78.0,
                                "proj_scale": 0.48,
                                "near_clip_dist": 0.18,
                                "wall_height_world": 1.0,
                                "cell_size_world": 1.25,
                                "distance_soften": 0.35,
                                "door_height_ratio": 0.80,
                                "door_frame_ratio": 0.12,
                                "door_inset_ratio": 0.22,
                                "door_ajar_angle_deg": 38.0,
                                "columns_cap": 320,
                        }, "render_home")

                def tune_render_save(self):
                        self.save_render_tune(announce=True)

                def tune_render_load(self):
                        self.load_saved_render_tune(announce=True)

                def tune_render_clear_saved(self):
                        self.clear_saved_render_tune()


                def test_status_label(self, ok):
                        return "OK" if ok else "FAIL"

                def test_status_color(self, ok):
                        return "#57d957" if ok else "#ff5a5a"

                def last_test_rows(self, limit=10):
                        rows = []
                        try:
                                src = list(self.test_results)
                        except Exception:
                                src = []
                        if limit and limit > 0:
                                src = src[-limit:]
                        for item in reversed(src):
                                try:
                                        name, ok, msg = item
                                except Exception:
                                        continue
                                rows.append({
                                        "name": name,
                                        "ok": bool(ok),
                                        "status": self.test_status_label(ok),
                                        "status_color": self.test_status_color(ok),
                                        "msg": msg or "",
                                })
                        return rows

                def _surface_debug_label(self, profile):
                        if profile is None:
                                return "none"
                        try:
                                material_id = getattr(profile, "material_id", None)
                                color = getattr(profile, "color", None)
                        except Exception:
                                material_id = None
                                color = None
                        if material_id is None and isinstance(profile, dict):
                                material_id = profile.get("material_id")
                                color = profile.get("color")
                        if material_id is None:
                                material_id = "unknown"
                        if color:
                                return "%s %s" % (material_id, color)
                        return str(material_id)

                def _current_zone_debug_lines(self):
                        lines = []
                        try:
                                p = self.world.player
                                r = self.world.room
                                z = r.get_zone_at(p.x, p.y) if hasattr(r, "get_zone_at") else None
                                if z is None:
                                        lines.append("Zone: none")
                                        return lines
                                shell = "interior" if getattr(z, "is_interior", True) else "exterior"
                                lines.append("Zone: %s (%s) level=%s shell=%s" % (
                                        getattr(z, "name", z.zone_id),
                                        getattr(z, "zone_type", "unknown"),
                                        getattr(z, "level_id", 0),
                                        shell,
                                ))
                                fp = getattr(z, "floor_profile", None)
                                cp = getattr(z, "ceiling_profile", None)
                                lines.append("Floor: %s" % self._surface_debug_label(fp))
                                if getattr(z, "is_interior", True):
                                        lines.append("Ceiling: %s | H %.2f" % (
                                                self._surface_debug_label(cp),
                                                float(getattr(z, "ceiling_height", 0.0)),
                                        ))
                                else:
                                        lines.append("Ceiling: none (open sky)")
                        except Exception as e:
                                lines.append("Zone EXC: %r" % (e,))
                        return lines


                # --------------------------------------------------
                # HUD / debug info
                # --------------------------------------------------
                def ascii_map(self):
                        return self.world.room.ascii_overview(self.world.player)

                def ascii_map_window(self, cell_radius=5):
                        try:
                                cell_radius = max(1, int(cell_radius))
                        except Exception:
                                cell_radius = 5
                        char_span = (cell_radius * 4) + 3
                        return self.ascii_map_fit(char_span, char_span)

                def ascii_map_fit(self, max_cols, max_rows):
                        try:
                                raw = self.ascii_map()
                                lines = raw.splitlines()
                                if not lines:
                                        return ""

                                max_cols = max(1, int(max_cols))
                                max_rows = max(1, int(max_rows))

                                p = self.world.player
                                center_x = int(p.x) * 2 + 1
                                center_y = int(p.y) * 2 + 1

                                full_w = max(len(line) for line in lines)
                                full_h = len(lines)

                                start_x = max(0, center_x - (max_cols // 2))
                                start_y = max(0, center_y - (max_rows // 2))

                                if start_x + max_cols > full_w:
                                        start_x = max(0, full_w - max_cols)
                                if start_y + max_rows > full_h:
                                        start_y = max(0, full_h - max_rows)

                                end_x = min(full_w, start_x + max_cols)
                                end_y = min(full_h, start_y + max_rows)

                                cropped = []
                                for line in lines[start_y:end_y]:
                                        padded = line.ljust(full_w)
                                        cropped.append(padded[start_x:end_x].rstrip())

                                return "\n".join(cropped)
                        except Exception as e:
                                return "ASCII EXC: %r" % (e,)

                def hud_lines(self):
                        p = self.world.player
                        r = self.world.room
                        lines = []
                        lines.append("Room: %s" % r.name)
                        lines.append("Pos: (%d, %d)" % (p.x, p.y))
                        lines.append("Facing: %s" % p.facing)
                        lines.append("Pitch: %s" % getattr(p, "pitch", 0))
                        lines.append("Tick: %s" % getattr(self.world, "tick", 0))
                        lines.append("Last move: %s" % getattr(self.world, "last_move_result", ""))
                        for zline in self._current_zone_debug_lines():
                                lines.append(zline)
                        lines.append(self._front_boundary_debug_text())

                        vals = self._renderer_vals()
                        if vals:
                                lines.append("FOV %.1f | Proj %.2f | Near %.2f" % (vals["fov_deg"], vals["proj_scale"], vals["near_clip_dist"]))
                                lines.append("WallH %.2f | CellM %.2f | Soft %.2f" % (vals["wall_height_world"], vals["cell_size_world"], vals["distance_soften"]))
                                lines.append("Cols %d | Render %.2f ms | Avg %.2f ms" % (vals["columns_cap"], vals["render_ms_last"], vals["render_ms_avg"]))
                                lines.append("RenderTune saved: %s" % ("YES" if self.has_saved_render_tune() else "NO"))

                        return lines


                def _front_boundary_debug_text(self):
                        try:
                                p = self.world.player
                                be = self.world.room.get_boundary(p.x, p.y, p.facing)
                                if be is None:
                                        return "Ahead: none"
                                return "Ahead: %s state=%s move_block=%s vision_block=%s zones=(%s,%s)" % (
                                        getattr(be, "boundary_type", None),
                                        getattr(be, "door_state", None),
                                        getattr(be, "blocks_movement", None),
                                        getattr(be, "blocks_vision", None),
                                        getattr(be, "zone_a", None),
                                        getattr(be, "zone_b", None),
                                )
                        except Exception as e:
                                return "Ahead EXC: %r" % (e,)

                # --------------------------------------------------
                # Generator actions
                # --------------------------------------------------
                def _load_generated_world(self, w, label):
                        self.world = w
                        self._log("Generator loaded: %s" % label)
                        self._log("World: %s" % self.world.room.name)
                        self._notify_renderer("generator", force=True)
                        self._refresh_ui()

                def do_gen_house_floor_mvp(self):
                        try:
                                w = yc_generate_house_floor_mvp_world()
                                self._load_generated_world(w, "house_floor_mvp")
                                if "yc_floor_mvp_summary" in globals():
                                        self._log(yc_floor_mvp_summary())
                        except Exception as e:
                                self._log("GEN house_floor_mvp EXC: %r" % (e,))
                                self._refresh_ui()

                def do_gen_demo_room(self):
                        try:
                                self._load_generated_world(generate_demo_room(), "demo")
                        except Exception as e:
                                self._log("GEN demo EXC: %r" % (e,))
                                self._refresh_ui()

                def do_gen_maze(self):
                        try:
                                self._load_generated_world(yc_generate_maze_world(with_doors=False), "maze")
                        except Exception as e:
                                self._log("GEN maze EXC: %r" % (e,))
                                self._refresh_ui()

                def do_gen_maze_doors(self):
                        try:
                                self._load_generated_world(yc_generate_maze_world(with_doors=True), "maze_doors")
                        except Exception as e:
                                self._log("GEN maze_doors EXC: %r" % (e,))
                                self._refresh_ui()

                def do_gen_tunnel(self):
                        try:
                                self._load_generated_world(yc_generate_tunnel_world(with_doors=False), "tunnel")
                        except Exception as e:
                                self._log("GEN tunnel EXC: %r" % (e,))
                                self._refresh_ui()

                def do_gen_tunnel_doors(self):
                        try:
                                self._load_generated_world(yc_generate_tunnel_world(with_doors=True), "tunnel_doors")
                        except Exception as e:
                                self._log("GEN tunnel_doors EXC: %r" % (e,))
                                self._refresh_ui()

                def do_gen_vertical_house(self):
                        try:
                                w = yc_generate_vertical_house_world()
                                self._load_generated_world(w, "vertical_house")
                                self._log(yc_vertical_house_summary(w))
                        except Exception as e:
                                self._log("GEN vertical_house EXC: %r" % (e,))
                                self._refresh_ui()

                # --------------------------------------------------
                # Movement (safe wrappers)
                # --------------------------------------------------
                def _move_world_dir(self, d, label):
                        try:
                                # If World has generic step_dir use it, otherwise fallback
                                if hasattr(self.world, "step_dir"):
                                        ok, why = self.world.step_dir(d)
                                else:
                                        ok, why = self.world.room.can_move(self.world.player.x, self.world.player.y, d)
                                        self.world.last_move_result = why
                                        if ok:
                                                dx, dy = DIR_VEC[d]
                                                self.world.player.x += dx
                                                self.world.player.y += dy
                                                if hasattr(self.world.player, "settle_pitch_one_step"):
                                                        self.world.player.settle_pitch_one_step()
                                                if hasattr(self.world, "_touch_logic"):
                                                        self.world._touch_logic()

                                self._log("%s: %s (%s)" % (label, "OK" if ok else "BLOCK", why))
                                self._notify_renderer(label.lower(), force=True)
                                self._refresh_ui()
                                return ok

                        except Exception as e:
                                self._log("%s EXC: %r" % (label, e))
                                self._refresh_ui()
                                return False

                def do_forward(self):
                        try:
                                ok, why = self.world.step_forward()
                                self._log("Forward: %s (%s)" % ("OK" if ok else "BLOCK", why))
                                self._notify_renderer("forward", force=True)
                                self._refresh_ui()
                        except Exception as e:
                                self._log("Forward EXC: %r" % (e,))
                                self._refresh_ui()
                        return None

                def do_backward(self):
                        try:
                                facing = self.world.player.facing
                                d = OPPOSITE.get(facing, "S")
                                self._move_world_dir(d, "Back")
                        except Exception as e:
                                self._log("Back EXC: %r" % (e,))
                                self._refresh_ui()
                        return None

                def do_strafe_left(self):
                        try:
                                facing = self.world.player.facing
                                d = LEFT_OF.get(facing, "W")
                                self._move_world_dir(d, "StrafeL")
                        except Exception as e:
                                self._log("StrafeL EXC: %r" % (e,))
                                self._refresh_ui()
                        return None

                def do_strafe_right(self):
                        try:
                                facing = self.world.player.facing
                                d = RIGHT_OF.get(facing, "E")
                                self._move_world_dir(d, "StrafeR")
                        except Exception as e:
                                self._log("StrafeR EXC: %r" % (e,))
                                self._refresh_ui()
                        return None

                def do_turn_left(self):
                        try:
                                self.world.turn_left()
                                self._log("Turn left")
                                self._notify_renderer("turn_left", force=True)
                                self._refresh_ui()
                        except Exception as e:
                                self._log("TurnL EXC: %r" % (e,))
                                self._refresh_ui()
                        return None

                def do_turn_right(self):
                        try:
                                self.world.turn_right()
                                self._log("Turn right")
                                self._notify_renderer("turn_right", force=True)
                                self._refresh_ui()
                        except Exception as e:
                                self._log("TurnR EXC: %r" % (e,))
                                self._refresh_ui()
                        return None

                def do_look_up(self):
                        try:
                                changed = self.world.look_up()
                                self._log("Look up: %s" % ("OK" if changed else "limit"))
                                self._notify_renderer("look_up", force=True)
                                self._refresh_ui()
                        except Exception as e:
                                self._log("LookUp EXC: %r" % (e,))
                                self._refresh_ui()
                        return None

                def do_look_down(self):
                        try:
                                changed = self.world.look_down()
                                self._log("Look down: %s" % ("OK" if changed else "limit"))
                                self._notify_renderer("look_down", force=True)
                                self._refresh_ui()
                        except Exception as e:
                                self._log("LookDown EXC: %r" % (e,))
                                self._refresh_ui()
                        return None

                def do_look_center(self):
                        try:
                                changed = self.world.look_center()
                                self._log("Look center: %s" % ("OK" if changed else "already"))
                                self._notify_renderer("look_center", force=True)
                                self._refresh_ui()
                        except Exception as e:
                                self._log("LookCenter EXC: %r" % (e,))
                                self._refresh_ui()
                        return None

                # --------------------------------------------------
                # Front edge / doors
                # --------------------------------------------------
                def _front_edge(self):
                        p = self.world.player
                        c = self.world.room.get(p.x, p.y)
                        if c is None:
                                return None, None
                        try:
                                if hasattr(self.world.room, "get_edge"):
                                        e = self.world.room.get_edge(p.x, p.y, p.facing)
                                else:
                                        e = c.edges.get(p.facing, None)
                        except Exception:
                                e = c.edges.get(p.facing, None)
                        return c, e

                def can_interact_door(self):
                        try:
                                _c, e = self._front_edge()
                                if e is None:
                                        return False
                                et, _op = _edge_type_open(e)
                                return et == EDGE_DOOR
                        except Exception:
                                return False

                def _door_set_front_state(self, target_state, log_msg):
                        try:
                                p = self.world.player
                                room = self.world.room
                                _c, e = self._front_edge()

                                if e is None:
                                        self._log("Door: nothing ahead")
                                        self._refresh_ui()
                                        return False

                                et, _op = _edge_type_open(e)
                                if et != EDGE_DOOR:
                                        self._log("Door: no door ahead")
                                        self._refresh_ui()
                                        return False

                                ds = _door_state(e)
                                if ds == DOOR_LOCKED:
                                        self._log("Door: locked")
                                        self._refresh_ui()
                                        return False

                                ok = False

                                if hasattr(room, "set_door_state_mirrored"):
                                        ok = bool(room.set_door_state_mirrored(p.x, p.y, p.facing, target_state))

                                elif isinstance(e, dict):
                                        # compat local+mirror update
                                        e["door_state"] = target_state
                                        e["state"] = target_state
                                        e["open"] = bool(target_state in (DOOR_AJAR, DOOR_OPEN))
                                        ok = True

                                        dx, dy = DIR_VEC[p.facing]
                                        nx, ny = p.x + dx, p.y + dy
                                        nc = room.get(nx, ny)
                                        if nc is not None:
                                                nd = OPPOSITE[p.facing]
                                                ne = nc.edges.get(nd, None)
                                                if isinstance(ne, dict):
                                                        ne["door_state"] = target_state
                                                        ne["state"] = target_state
                                                        ne["open"] = bool(target_state in (DOOR_AJAR, DOOR_OPEN))

                                if ok:
                                        self._log(log_msg)
                                        if hasattr(self.world, "_touch_logic"):
                                                self.world._touch_logic()
                                        self._notify_renderer("door_state", force=True)
                                else:
                                        self._log("Door: sync fail")

                                self._refresh_ui()
                                return ok

                        except Exception as e:
                                self._log("Door set EXC: %r" % (e,))
                                self._refresh_ui()
                                return False

                # old UI compat
                def do_door_open(self):
                        return self._door_set_front_state(DOOR_OPEN, "Door: opened")

                def do_door_close(self):
                        return self._door_set_front_state(DOOR_CLOSED, "Door: closed")

                def do_door_ajar(self):
                        return self._door_set_front_state(DOOR_AJAR, "Door: ajar")

                def do_door_toggle(self):
                        try:
                                _c, e = self._front_edge()
                                if e is None:
                                        self._log("Door: nothing ahead")
                                        self._refresh_ui()
                                        return False

                                et, _op = _edge_type_open(e)
                                if et != EDGE_DOOR:
                                        self._log("Door: no door ahead")
                                        self._refresh_ui()
                                        return False

                                ds = _door_state(e)
                                if ds == DOOR_LOCKED:
                                        self._log("Door: locked")
                                        self._refresh_ui()
                                        return False

                                if ds == DOOR_CLOSED:
                                        return self.do_door_ajar()
                                elif ds == DOOR_AJAR:
                                        return self.do_door_open()
                                elif ds == DOOR_OPEN:
                                        return self.do_door_close()
                                else:
                                        # fallback for old edges without state
                                        if isinstance(e, dict):
                                                if bool(e.get("open", False)):
                                                        return self.do_door_close()
                                                else:
                                                        return self.do_door_open()

                                self._refresh_ui()
                                return False

                        except Exception as e:
                                self._log("Door toggle EXC: %r" % (e,))
                                self._refresh_ui()
                                return False

                def do_interact(self):
                        try:
                                self.do_door_toggle()
                        except Exception as e:
                                self._log("Interact EXC: %r" % (e,))
                                self._refresh_ui()
                        return None

                def do_load_demo_hotkey(self):
                        return self.do_gen_demo_room()

                def do_load_house_hotkey(self):
                        return self.do_gen_house_floor_mvp()

                def do_load_maze_hotkey(self):
                        return self.do_gen_maze()

                def do_load_maze_doors_hotkey(self):
                        return self.do_gen_maze_doors()

                def do_load_tunnel_hotkey(self):
                        return self.do_gen_tunnel()

                def do_load_tunnel_doors_hotkey(self):
                        return self.do_gen_tunnel_doors()

                def do_load_vertical_house_hotkey(self):
                        return self.do_gen_vertical_house()

                # --------------------------------------------------
                # Tests API
                # --------------------------------------------------
                def available_tests(self):
                        reg = get_test_registry()
                        return [t["name"] for t in reg["tests"]]

                def run_test(self, test_name):
                        reg = get_test_registry()
                        item = reg["by_name"].get(test_name)

                        if item is None:
                                self.test_results.append((test_name, False, "not found"))
                                self._log("Test missing: %s" % test_name)
                                self._refresh_ui()
                                return False

                        try:
                                ok = bool(item["fn"]())
                                msg = item.get("desc", "")
                        except Exception as e:
                                ok = False
                                msg = "EXC: %r" % (e,)

                        self.test_results.append((test_name, ok, msg))
                        self._log("Test %s: %s" % (test_name, "OK" if ok else "FAIL"))
                        self._refresh_ui()
                        return ok

                def run_all_tests(self):
                        self.test_results = []
                        ok_all = True

                        for tname in self.available_tests():
                                if not self.run_test(tname):
                                        ok_all = False

                        self._log("All tests: %s" % ("OK" if ok_all else "FAIL"))
                        self._refresh_ui()
                        return ok_all

                def do_run_test(self, test_name):
                        try:
                                self.run_test(test_name)
                        except Exception as e:
                                self._log("Run test wrapper EXC: %r" % (e,))
                                self._refresh_ui()
                        return None

                def do_run_all_tests(self):
                        try:
                                self.run_all_tests()
                        except Exception as e:
                                self._log("Run all tests wrapper EXC: %r" % (e,))
                                self._refresh_ui()
                        return None