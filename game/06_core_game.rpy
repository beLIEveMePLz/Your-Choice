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
                        self.show_log = True
                        self.show_tests = True
                        self.show_generator_ui = False

                        self.log = []
                        self.test_results = []

                        self._log("Game init OK")
                        self._log("World: %s" % self.world.room.name)
                        self._log("Input: W/S/A/D move, Q/E turn, F interact, 1 demo, 2 house, 3 maze, 4 maze+doors, 5 tunnel, 6 tunnel+doors")

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

                # --------------------------------------------------
                # HUD / debug info
                # --------------------------------------------------
                def ascii_map(self):
                        return self.world.room.ascii_overview(self.world.player)

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