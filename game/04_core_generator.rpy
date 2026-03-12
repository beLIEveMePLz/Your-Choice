# 04_core_generator.rpy
# ============================================================
# Core: demo generator helpers + MVP floor generator
# Core-first update: assigns zone_id and boundary metadata
# ============================================================

init -20 python:
        def _open_between(room, x, y, d, edge_type=EDGE_OPEN, open_state=True):
                if room.in_bounds(x, y):
                        room.set_edge_mirrored(x, y, d, EDGE_OPEN, True)

        def _carve_rect(room, x1, y1, x2, y2):
                x1 = max(0, min(room.w - 1, int(x1)))
                y1 = max(0, min(room.h - 1, int(y1)))
                x2 = max(0, min(room.w - 1, int(x2)))
                y2 = max(0, min(room.h - 1, int(y2)))
                if x2 <= x1 or y2 <= y1:
                        return False
                for y in range(y1, y2 + 1):
                        for x in range(x1, x2 + 1):
                                if x < x2:
                                        room.set_edge_mirrored(x, y, "E", EDGE_OPEN)
                                if y < y2:
                                        room.set_edge_mirrored(x, y, "S", EDGE_OPEN)
                return True

        def _assign_zone_rect(room, zone_id, zone_name, zone_type, x1, y1, x2, y2):
                room.define_zone(zone_id, zone_name, zone_type)
                for y in range(int(y1), int(y2) + 1):
                        for x in range(int(x1), int(x2) + 1):
                                room.set_zone(x, y, zone_id)

        def _carve_corridor(room, x1, y1, x2, y2):
                x = int(x1)
                y = int(y1)
                while x != int(x2):
                        d = "E" if x < int(x2) else "W"
                        room.set_edge_mirrored(x, y, d, EDGE_OPEN)
                        x += 1 if d == "E" else -1
                while y != int(y2):
                        d = "S" if y < int(y2) else "N"
                        room.set_edge_mirrored(x, y, d, EDGE_OPEN)
                        y += 1 if d == "S" else -1
                return True

        def _fill_all_walls(room):
                for y in range(room.h):
                        for x in range(room.w):
                                for d in DIRS:
                                        room.set_edge_mirrored(x, y, d, EDGE_WALL, False)

        def generate_demo_room(seed=0):
                r = Room(9, 7, name="demo")
                _fill_all_walls(r)
                _carve_rect(r, 1, 1, 6, 5)
                _carve_corridor(r, 6, 3, 8, 3)
                r.set_edge_mirrored(6, 3, "E", EDGE_DOOR, False)

                # minimal zones for demo (single interior zone + corridor tail zone)
                _assign_zone_rect(r, 1, "demo_room", "interior", 1, 1, 6, 5)
                _assign_zone_rect(r, 2, "demo_corridor", "interior", 7, 3, 8, 3)
                r.rebuild_zone_memberships()
                r.refresh_all_boundary_zone_links()

                r.place_object(2, 2, "sink")
                r.place_object(3, 2, "shelf")
                r.place_object(5, 4, "closet")

                p = Player(2, 4, "N")
                w = World(r, p)
                return w

        def _door(room, x, y, d, is_open=False):
                room.set_edge_mirrored(int(x), int(y), d, EDGE_DOOR, bool(is_open))

        def yc_generate_house_floor_mvp_world(seed=0):
                """
                One floor MVP with explicit zones and boundary-driven movement.
                """
                r = Room(14, 13, name="house_floor_mvp")
                _fill_all_walls(r)

                # Geometry carve
                _carve_rect(r, 6, 1, 7, 11)      # corridor
                _carve_rect(r, 1, 1, 5, 3)       # kitchen
                _carve_rect(r, 1, 4, 5, 6)       # bathroom
                _carve_rect(r, 1, 7, 5, 11)      # bedroom1
                _carve_rect(r, 8, 1, 12, 5)      # salon
                _carve_rect(r, 8, 6, 12, 7)      # toilet
                _carve_rect(r, 8, 8, 12, 11)     # bedroom2

                # Doors between zones
                _door(r, 5, 2, "E", False)
                _door(r, 5, 5, "E", False)
                _door(r, 5, 9, "E", False)
                _door(r, 8, 3, "W", False)
                _door(r, 8, 6, "W", False)
                _door(r, 8, 9, "W", False)

                # Zone assignments (zone_id is now explicit and stable)
                _assign_zone_rect(r, 10, "corridor", "corridor", 6, 1, 7, 11)
                _assign_zone_rect(r, 11, "kitchen", "kitchen", 1, 1, 5, 3)
                _assign_zone_rect(r, 12, "bathroom", "bathroom", 1, 4, 5, 6)
                _assign_zone_rect(r, 13, "bedroom1", "bedroom", 1, 7, 5, 11)
                _assign_zone_rect(r, 14, "salon", "living_room", 8, 1, 12, 5)
                _assign_zone_rect(r, 15, "toilet", "toilet", 8, 6, 12, 7)
                _assign_zone_rect(r, 16, "bedroom2", "bedroom", 8, 8, 12, 11)
                r.rebuild_zone_memberships()
                r.refresh_all_boundary_zone_links()

                # Debug landmarks
                r.place_object(2, 2, "kitchen")
                r.place_object(3, 5, "bath")
                r.place_object(3, 9, "bed")
                r.place_object(10, 3, "sofa")
                r.place_object(10, 6, "toilet")
                r.place_object(10, 9, "bed")

                p = Player(6, 10, "N")
                return World(r, p)

        def yc_floor_mvp_summary():
                return "MVP floor: zone+boundary core active (corridor + 6 rooms)"