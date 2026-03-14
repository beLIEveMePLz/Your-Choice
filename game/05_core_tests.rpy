# 05_core_tests.rpy
# ============================================================
# Core: test registry + tests
# Updated for zone+boundary core step
# ============================================================

init -20 python:
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



        def _test_zone_surface_defaults_interior():
                r = Room(4, 4, name="surface_defaults_interior")
                z = r.define_zone(1, name="room_1", zone_type="room", level_id=0)
                if z is None:
                        return False
                if not getattr(z, "is_interior", False):
                        return False
                if getattr(z, "floor_profile", None) is None:
                        return False
                if getattr(z, "ceiling_profile", None) is None:
                        return False
                return float(getattr(z, "ceiling_height", 0.0)) > 0.0

        def _test_zone_surface_defaults_exterior():
                r = Room(4, 4, name="surface_defaults_exterior")
                z = r.define_zone(2, name="yard", zone_type="yard", level_id=0, tags=["exterior", "yard"], is_interior=False)
                if z is None:
                        return False
                if getattr(z, "is_interior", True):
                        return False
                if getattr(z, "floor_profile", None) is None:
                        return False
                return getattr(z, "ceiling_profile", None) is None

        def _test_zone_surface_profile_setters_roundtrip():
                r = Room(4, 4, name="surface_setters_roundtrip")
                r.define_zone(3, name="hall", zone_type="hall", level_id=0)
                ok1 = r.set_zone_floor_profile(3, {"material_id": "hall_tile", "color": "#888888", "shade": 0.97})
                ok2 = r.set_zone_ceiling_profile(3, {"material_id": "white_paint", "color": "#eeeeee", "shade": 1.00})
                if (not ok1) or (not ok2):
                        return False
                fp = r.get_zone_floor_profile(3)
                cp = r.get_zone_ceiling_profile(3)
                if fp is None or cp is None:
                        return False
                return getattr(fp, "material_id", None) == "hall_tile" and getattr(cp, "material_id", None) == "white_paint"

        def _test_vertical_house_surface_profiles_present():
                W = yc_generate_vertical_house_world()
                r = W.room
                for zid in (10, 11, 12, 20, 110, 111, 112, 120):
                        z = r.get_zone(zid)
                        if z is None:
                                return False
                        if getattr(z, "floor_profile", None) is None:
                                return False
                        if getattr(z, "is_interior", True):
                                if getattr(z, "ceiling_profile", None) is None:
                                        return False
                                if float(getattr(z, "ceiling_height", 0.0)) <= 0.0:
                                        return False
                return True

        def _test_vertical_house_surface_core_checker():
                W = yc_generate_vertical_house_world()
                r = W.room
                if not hasattr(r, "surface_core_checker"):
                        return False
                rep = r.surface_core_checker()
                return bool(rep.get("ok", False))


        def _test_renderer_surface_palette_changes_between_zones():
                W = yc_generate_vertical_house_world()
                rr = make_renderer(W)

                W.player.x = 2
                W.player.y = 2
                p_living = rr._active_surface_palette()

                W.player.x = 10
                W.player.y = 2
                p_kitchen = rr._active_surface_palette()

                return p_living.get("floor_rgba") != p_kitchen.get("floor_rgba")

        def _test_renderer_surface_palette_exterior_sky_fallback():
                W = generate_demo_room()
                r = W.room
                if not hasattr(r, "define_zone"):
                        return False

                z = r.define_zone(91, name="yard", zone_type="yard", level_id=0, tags=["exterior", "yard"], is_interior=False)
                if z is None:
                        return False

                for y in range(r.h):
                        for x in range(r.w):
                                r.set_zone(x, y, 91)

                if hasattr(r, "rebuild_zone_memberships"):
                        r.rebuild_zone_memberships()

                rr = make_renderer(W)
                pal = rr._active_surface_palette()
                return pal.get("ceiling_rgba") == (90, 118, 154, 255)

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

        add("player_in_bounds", _test_player_in_bounds, "Spawned player starts within room bounds.")
        add("edge_symmetry_scan", _test_edge_symmetry_scan, "Mirrored edges stay consistent (no one-way walls).")
        add("boundary_checker_demo", _test_boundary_checker_demo, "Boundary checker passes on demo map.")
        add("boundary_checker_house_floor", _test_boundary_checker_house_floor, "Boundary checker passes on house floor MVP.")
        add("zone_membership_nonempty", _test_zone_membership_nonempty, "Zones exist and have cells.")
        add("renderer_contract", _test_renderer_contract, "Renderer contract placeholder.")

        add("zone_surface_defaults_interior", _test_zone_surface_defaults_interior, "Interior zones get default floor and ceiling profiles.")
        add("zone_surface_defaults_exterior", _test_zone_surface_defaults_exterior, "Exterior zones keep a floor profile and no ceiling by default.")
        add("zone_surface_profile_setters_roundtrip", _test_zone_surface_profile_setters_roundtrip, "Zone floor/ceiling profile setters roundtrip material ids.")
        add("vertical_house_surface_profiles_present", _test_vertical_house_surface_profiles_present, "Vertical house generator assigns floor and ceiling profiles to its zones.")
        add("vertical_house_surface_core_checker", _test_vertical_house_surface_core_checker, "Surface checker passes on generated vertical house.")
        add("renderer_surface_palette_changes_between_zones", _test_renderer_surface_palette_changes_between_zones, "Renderer picks different floor colors for different active zones.")
        add("renderer_surface_palette_exterior_sky_fallback", _test_renderer_surface_palette_exterior_sky_fallback, "Exterior zones without a ceiling profile fall back to sky color.")
        add("house_floor_closed_door_blocks", _test_house_floor_closed_door_blocks, "Closed door blocks corridor-to-room movement.")
        add("house_floor_open_door_allows", _test_house_floor_open_door_allows, "Opened door allows corridor-to-room movement.")
        add("view_key_match", _test_view_key_match, "View key is stable without changes.")
        add("pitch_bounds", _test_pitch_bounds, "Player pitch clamps to [-2..2].")
        add("pitch_affects_view_key", _test_pitch_affects_view_key, "Pitch change invalidates view cache key.")