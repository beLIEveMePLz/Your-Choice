# 06_core_game.rpy
# ============================================================
# Core: Game controller / facade (debug-safe)
# + movement: W/S forward/back, A/D strafe, Q/E turn, F interact
# + compat doors API (old UI + new interact)
# + renderer refresh after every action
# ============================================================

init -20 python:
        import renpy as rp

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
                        self._log("Input: W/S/A/D move, Q/E turn, F interact, 1 demo, 2 house")

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
                        self._notify_renderer("bind", force=True)
                        self._log("Renderer bound")
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
                                "columns_cap": int(getattr(r, "columns_cap", 220)),
                                "render_ms_last": float(getattr(r, "render_ms_last", 0.0)),
                                "render_ms_avg": float(getattr(r, "render_ms_avg", 0.0)),
                        }

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
                                "columns_cap": 320,
                        }, "render_home")

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