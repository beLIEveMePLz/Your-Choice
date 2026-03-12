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
        add("view_key_match", _test_view_key_match, "View key is stable without changes.")
        add("pitch_bounds", _test_pitch_bounds, "Player pitch clamps to [-2..2].")
        add("pitch_affects_view_key", _test_pitch_affects_view_key, "Pitch change invalidates view cache key.")