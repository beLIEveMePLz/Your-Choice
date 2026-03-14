# 05_core_tests.rpy
# ============================================================
# Core: test registry + tests
# Updated for zone+boundary core step
# + renderer tune persistence / door render tests
# ============================================================

init -20 python:
        import renpy as rp

        def get_test_registry():
                reg = getattr(get_test_registry, "_reg", None)
                if reg is None:
                        reg = {"tests": [], "by_name": {}}
                        get_test_registry._reg = reg
                return reg

        def add(name, fn, desc=""):
                reg = get_test_registry()
                item = {"name": name, "fn": fn, "desc": desc}
                reg["tests"].append(item)
                reg["by_name"][name] = item

        def _approx(a, b, eps=0.0001):
                return abs(float(a) - float(b)) <= float(eps)

        def _snapshot_saved_render_tune():
                try:
                        p = getattr(rp.store, "persistent", None)
                        if p is None:
                                return (False, None)
                        if hasattr(p, "yc_render_tune_v1"):
                                old = getattr(p, "yc_render_tune_v1", None)
                                if isinstance(old, dict):
                                        old = dict(old)
                                return (True, old)
                        return (False, None)
                except Exception:
                        return (False, None)

        def _restore_saved_render_tune(snapshot):
                try:
                        had_attr, old = snapshot
                        p = getattr(rp.store, "persistent", None)
                        if p is None:
                                return False
                        if had_attr:
                                setattr(p, "yc_render_tune_v1", old)
                        else:
                                setattr(p, "yc_render_tune_v1", None)
                        try:
                                rp.save_persistent()
                        except Exception:
                                pass
                        return True
                except Exception:
                        return False

        def _test_player_in_bounds():
                W = generate_demo_room()
                p = W.player
                return W.room.in_bounds(p.x, p.y)

        def _test_edge_symmetry_scan():
                W = generate_demo_room()
                r = W.room
                for y in range(r.h):
                        for x in range(r.w):
                                for d in DIRS:
                                        e = r.get_edge(x, y, d)
                                        dx, dy = DIR_VEC[d]
                                        nx = x + dx
                                        ny = y + dy
                                        if r.in_bounds(nx, ny):
                                                ne = r.get_edge(nx, ny, OPPOSITE[d])
                                                et, op = _edge_type_open(e)
                                                net, nop = _edge_type_open(ne)
                                                if et != net or bool(op) != bool(nop):
                                                        return False
                return True

        def _test_boundary_checker_demo():
                W = generate_demo_room()
                rep = W.room.boundary_checker_mvp()
                return bool(rep.get("ok", False))

        def _test_boundary_checker_house_floor():
                W = yc_generate_house_floor_mvp_world()
                rep = W.room.boundary_checker_mvp()
                return bool(rep.get("ok", False))

        def _test_zone_membership_nonempty():
                W = yc_generate_house_floor_mvp_world()
                r = W.room
                if not r.zones:
                        return False
                total = 0
                for z in r.zones.values():
                        total += len(z.cells)
                return total > 0

        def _test_renderer_contract():
                return True

        def _test_house_floor_closed_door_blocks():
                W = yc_generate_house_floor_mvp_world()
                ok, why = W.room.can_move(6, 2, "W")
                return (ok is False) and (why == "blocked_boundary")

        def _test_house_floor_open_door_allows():
                W = yc_generate_house_floor_mvp_world()
                r = W.room
                if not r.set_door_state_mirrored(6, 2, "W", DOOR_OPEN):
                        return False
                ok, why = r.can_move(6, 2, "W")
                return (ok is True) and (why == "ok")

        def _test_game_front_door_actions_cycle():
            G = Game()
            G.world.player.x = 6
            G.world.player.y = 2
            G.world.player.facing = "W"
            room = G.world.room

            if not G.do_door_ajar():
                    return False
            e = room.get_edge(6, 2, "W")
            if _door_state(e) != DOOR_AJAR:
                    return False

            if not G.do_door_open():
                    return False
            e = room.get_edge(6, 2, "W")
            if _door_state(e) != DOOR_OPEN:
                    return False

            if not G.do_door_close():
                    return False
            e = room.get_edge(6, 2, "W")
            return _door_state(e) == DOOR_CLOSED


        def _test_view_key_match():
                W = generate_demo_room()
                k1 = W.state_view_key()
                k2 = W.state_view_key()
                return k1 == k2

        def _test_pitch_bounds():
                p = Player(0, 0, "N")
                for _ in range(10):
                        p.look_up()
                if p.pitch < -2:
                        return False
                for _ in range(10):
                        p.look_down()
                if p.pitch > 2:
                        return False
                return True

        def _test_pitch_affects_view_key():
                W = generate_demo_room()
                k0 = W.state_view_key()
                W.look_down()
                k1 = W.state_view_key()
                return k0 != k1

        def _test_renderer_door_profile_affects_cache_key():
                W = generate_demo_room()
                R = StepRayRenderer(W)
                k0 = R._make_cache_key(320, 200)
                R.door_height_ratio = float(R.door_height_ratio) + 0.02
                k1 = R._make_cache_key(320, 200)
                if k0 == k1:
                        return False
                R.door_height_ratio = 0.78
                k2 = R._make_cache_key(320, 200)
                R.door_ajar_angle_deg = float(R.door_ajar_angle_deg) + 3.0
                k3 = R._make_cache_key(320, 200)
                return k2 != k3

        def _test_renderer_passthrough_door_hit_classification():
                W = generate_demo_room()
                R = StepRayRenderer(W)
                ajar_hit = {
                        "edge": {"type": EDGE_DOOR, "door_state": DOOR_AJAR},
                        "hit_x": 1.0,
                        "hit_y": 1.0,
                }
                open_hit = {
                        "edge": {"type": EDGE_DOOR, "door_state": DOOR_OPEN},
                        "hit_x": 1.0,
                        "hit_y": 1.0,
                }
                closed_hit = {
                        "edge": {"type": EDGE_DOOR, "door_state": DOOR_CLOSED},
                        "hit_x": 1.0,
                        "hit_y": 1.0,
                }
                wall_hit = {
                        "edge": {"type": EDGE_WALL},
                        "hit_x": 1.0,
                        "hit_y": 1.0,
                }
                if not R._is_passthrough_door_hit(ajar_hit):
                        return False
                if not R._is_passthrough_door_hit(open_hit):
                        return False
                if R._is_passthrough_door_hit(closed_hit):
                        return False
                if R._is_passthrough_door_hit(wall_hit):
                        return False
                return True

        def _test_render_tune_save_load_roundtrip():
                snap = _snapshot_saved_render_tune()
                try:
                        G = Game()
                        R = StepRayRenderer(G.world)
                        G.bind_renderer(R)

                        seed = {
                                "fov_deg": 82.0,
                                "proj_scale": 0.63,
                                "near_clip_dist": 0.24,
                                "wall_height_world": 1.18,
                                "cell_size_world": 1.00,
                                "distance_soften": 0.27,
                                "door_height_ratio": 0.81,
                                "door_frame_ratio": 0.16,
                                "door_inset_ratio": 0.23,
                                "door_ajar_angle_deg": 45.0,
                                "columns_cap": 188,
                        }
                        if not G._apply_renderer_vals(seed, "test_seed"):
                                return False
                        if not G.save_render_tune(announce=False):
                                return False

                        changed = {
                                "fov_deg": 68.0,
                                "proj_scale": 0.51,
                                "near_clip_dist": 0.12,
                                "wall_height_world": 0.92,
                                "distance_soften": 0.11,
                                "door_height_ratio": 0.72,
                                "door_frame_ratio": 0.08,
                                "door_inset_ratio": 0.12,
                                "door_ajar_angle_deg": 30.0,
                                "columns_cap": 104,
                        }
                        if not G._apply_renderer_vals(changed, "test_changed"):
                                return False
                        if not G.load_saved_render_tune(announce=False):
                                return False

                        vals = G._renderer_vals()
                        if not vals:
                                return False
                        for k, v in seed.items():
                                if k == "columns_cap":
                                        if int(vals.get(k, -1)) != int(v):
                                                return False
                                else:
                                        if not _approx(vals.get(k, None), v):
                                                return False
                        return True
                finally:
                        _restore_saved_render_tune(snap)

        def _test_render_tune_bind_autoload():
                snap = _snapshot_saved_render_tune()
                try:
                        p = getattr(rp.store, "persistent", None)
                        if p is None:
                                return False

                        seed = {
                                "fov_deg": 86.0,
                                "proj_scale": 0.66,
                                "near_clip_dist": 0.20,
                                "wall_height_world": 1.14,
                                "cell_size_world": 1.00,
                                "distance_soften": 0.29,
                                "door_height_ratio": 0.84,
                                "door_frame_ratio": 0.14,
                                "door_inset_ratio": 0.26,
                                "door_ajar_angle_deg": 42.0,
                                "columns_cap": 176,
                        }
                        setattr(p, "yc_render_tune_v1", dict(seed))
                        try:
                                rp.save_persistent()
                        except Exception:
                                pass

                        G = Game()
                        R = StepRayRenderer(G.world)
                        G.bind_renderer(R)

                        vals = G._renderer_vals()
                        if not vals:
                                return False
                        for k, v in seed.items():
                                if k == "columns_cap":
                                        if int(vals.get(k, -1)) != int(v):
                                                return False
                                else:
                                        if not _approx(vals.get(k, None), v):
                                                return False
                        return True
                finally:
                        _restore_saved_render_tune(snap)

        add("player_in_bounds", _test_player_in_bounds, "Spawned player starts within room bounds.")
        add("edge_symmetry_scan", _test_edge_symmetry_scan, "Mirrored edges stay consistent (no one-way walls).")
        add("boundary_checker_demo", _test_boundary_checker_demo, "Boundary checker passes on demo map.")
        add("boundary_checker_house_floor", _test_boundary_checker_house_floor, "Boundary checker passes on house floor MVP.")
        add("zone_membership_nonempty", _test_zone_membership_nonempty, "Zones exist and have cells.")
        add("renderer_contract", _test_renderer_contract, "Renderer contract placeholder.")
        add("house_floor_closed_door_blocks", _test_house_floor_closed_door_blocks, "Closed door blocks corridor-to-room movement.")
        add("house_floor_open_door_allows", _test_house_floor_open_door_allows, "Opened door allows corridor-to-room movement.")
        add("game_front_door_actions_cycle", _test_game_front_door_actions_cycle, "Door action helpers can set ajar/open/closed on the front door.")
        add("view_key_match", _test_view_key_match, "View key is stable without changes.")
        add("pitch_bounds", _test_pitch_bounds, "Player pitch clamps to [-2..2].")
        add("pitch_affects_view_key", _test_pitch_affects_view_key, "Pitch change invalidates view cache key.")
        add("renderer_door_profile_affects_cache_key", _test_renderer_door_profile_affects_cache_key, "Door render tune values invalidate renderer cache key.")
        add("renderer_passthrough_door_hit_classification", _test_renderer_passthrough_door_hit_classification, "Renderer treats ajar/open door hits as passthrough but not closed doors or walls.")
        add("render_tune_save_load_roundtrip", _test_render_tune_save_load_roundtrip, "Saved render tune restores the same values after local changes.")
        add("render_tune_bind_autoload", _test_render_tune_bind_autoload, "Renderer bind auto-loads the saved render tune profile.")
