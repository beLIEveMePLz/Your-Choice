# 01_core_room.rpy
# ============================================================
# Core: Cell + Room (zone + boundary core, compat with renderer/UI)
# First core step for YC Kanwa: boundaries are source-of-truth for movement
# ============================================================

init -20 python:
        class Zone(object):
                def __init__(self, zone_id, name=None, zone_type="room"):
                        self.zone_id = int(zone_id)
                        self.name = name or ("zone_%s" % zone_id)
                        self.zone_type = zone_type
                        self.cells = set()

        class VerticalLink(object):
                def __init__(self, link_id, zone_a, zone_b, link_type="stairs", meta=None):
                        self.link_id = link_id
                        self.zone_a = zone_a
                        self.zone_b = zone_b
                        self.link_type = link_type
                        self.meta = dict(meta or {})

        class BoundaryEdge(object):
                def __init__(self, key, x, y, d, boundary_type=EDGE_UNKNOWN, zone_a=None, zone_b=None,
                             door_state=None, blocks_movement=None, blocks_vision=None, height_class="full"):
                        self.key = key
                        self.x = int(x)
                        self.y = int(y)
                        self.d = d
                        self.boundary_type = boundary_type
                        self.zone_a = zone_a
                        self.zone_b = zone_b
                        self.height_class = height_class
                        self.door_state = door_state
                        self.blocks_movement = bool(blocks_movement) if blocks_movement is not None else True
                        self.blocks_vision = bool(blocks_vision) if blocks_vision is not None else True

                def to_edge_dict(self):
                        if self.boundary_type == EDGE_DOOR:
                                ds = self.door_state or DOOR_CLOSED
                                return _edge_dict(EDGE_DOOR, _door_open_flag_from_state(ds), door_state=ds)
                        return _edge_dict(self.boundary_type, not self.blocks_movement)

        class Cell(object):
                def __init__(self, x, y):
                        self.x = int(x)
                        self.y = int(y)
                        self.zone_id = None
                        self.edges = {d: _edge_dict(EDGE_UNKNOWN, False) for d in DIRS}
                        self.objects = []
                        self.object_blocker = False

                def set_edge(self, d, edge_type, open_state=False):
                        self.edges[d] = _edge_dict(edge_type, open_state)

        class Room(object):
                def __init__(self, w, h, name="Room"):
                        self.w = int(w)
                        self.h = int(h)
                        self.name = name
                        self.grid = [[Cell(x, y) for x in range(self.w)] for y in range(self.h)]
                        self.zones = {}
                        self.boundaries = {}      # canonical boundary edges
                        self.vertical_links = []  # placeholder for future floors/stairs/elevator

                # ---------- base grid ----------
                def in_bounds(self, x, y):
                        return 0 <= int(x) < self.w and 0 <= int(y) < self.h

                def get(self, x, y):
                        if not self.in_bounds(x, y):
                                return None
                        return self.grid[int(y)][int(x)]

                # ---------- zones ----------
                def define_zone(self, zone_id, name=None, zone_type="room"):
                        zid = int(zone_id)
                        z = self.zones.get(zid)
                        if z is None:
                                z = Zone(zid, name=name, zone_type=zone_type)
                                self.zones[zid] = z
                        else:
                                if name is not None:
                                        z.name = name
                                if zone_type is not None:
                                        z.zone_type = zone_type
                        return z

                def set_zone(self, x, y, zone_id):
                        c = self.get(x, y)
                        if c is None:
                                return False
                        zid = None if zone_id is None else int(zone_id)
                        c.zone_id = zid
                        return True

                def get_zone_id(self, x, y):
                        c = self.get(x, y)
                        return None if c is None else c.zone_id

                def rebuild_zone_memberships(self):
                        for z in self.zones.values():
                                z.cells = set()
                        for y in range(self.h):
                                for x in range(self.w):
                                        c = self.get(x, y)
                                        zid = c.zone_id
                                        if zid is None:
                                                continue
                                        if zid not in self.zones:
                                                self.define_zone(zid)
                                        self.zones[zid].cells.add((x, y))

                # ---------- boundaries (source of truth) ----------
                def _canonical_boundary_key(self, x, y, d):
                        x = int(x); y = int(y)
                        d = str(d)
                        if d == "W" and self.in_bounds(x - 1, y):
                                return (x - 1, y, "E")
                        if d == "N" and self.in_bounds(x, y - 1):
                                return (x, y - 1, "S")
                        return (x, y, d)

                def _boundary_target(self, x, y, d):
                        dx, dy = DIR_VEC[d]
                        nx = int(x) + dx
                        ny = int(y) + dy
                        if self.in_bounds(nx, ny):
                                return (nx, ny)
                        return None

                def _compute_boundary_flags(self, boundary_type, door_state=None):
                        if boundary_type == EDGE_OPEN or boundary_type == EDGE_PORTAL:
                                return False, False
                        if boundary_type == EDGE_DOOR:
                                ds = door_state or DOOR_CLOSED
                                is_open = _door_open_flag_from_state(ds)
                                return (not is_open), False
                        if boundary_type in (EDGE_WINDOW, EDGE_WINDOW_VIEW):
                                return True, False
                        if boundary_type == EDGE_UNKNOWN:
                                return True, True
                        return True, True

                def _boundary_zone_pair(self, x, y, d):
                        zone_a = self.get_zone_id(x, y)
                        tgt = self._boundary_target(x, y, d)
                        zone_b = None if tgt is None else self.get_zone_id(tgt[0], tgt[1])
                        return zone_a, zone_b

                def _sync_cell_edges_from_boundary(self, be):
                        edge_dict = be.to_edge_dict()
                        c = self.get(be.x, be.y)
                        if c is not None:
                                c.edges[be.d] = dict(edge_dict)
                        tgt = self._boundary_target(be.x, be.y, be.d)
                        if tgt is not None:
                                nc = self.get(tgt[0], tgt[1])
                                if nc is not None:
                                        nc.edges[OPPOSITE[be.d]] = dict(edge_dict)

                def set_boundary_mirrored(self, x, y, d, boundary_type, door_state=None):
                        c = self.get(x, y)
                        if c is None:
                                return False
                        key = self._canonical_boundary_key(x, y, d)
                        kx, ky, kd = key
                        zone_a, zone_b = self._boundary_zone_pair(kx, ky, kd)
                        blocks_movement, blocks_vision = self._compute_boundary_flags(boundary_type, door_state=door_state)
                        be = BoundaryEdge(
                                key=key,
                                x=kx, y=ky, d=kd,
                                boundary_type=boundary_type,
                                zone_a=zone_a,
                                zone_b=zone_b,
                                door_state=door_state if boundary_type == EDGE_DOOR else None,
                                blocks_movement=blocks_movement,
                                blocks_vision=blocks_vision,
                                height_class="full",
                        )
                        self.boundaries[key] = be
                        self._sync_cell_edges_from_boundary(be)
                        return True

                def set_edge_mirrored(self, x, y, d, edge_type, open_state=False):
                        # Compat wrapper used by existing generator code.
                        if edge_type == EDGE_DOOR:
                                ds = DOOR_OPEN if bool(open_state) else DOOR_CLOSED
                                return self.set_boundary_mirrored(x, y, d, EDGE_DOOR, door_state=ds)
                        return self.set_boundary_mirrored(x, y, d, edge_type)

                def get_boundary(self, x, y, d):
                        c = self.get(x, y)
                        if c is None:
                                return None
                        key = self._canonical_boundary_key(x, y, d)
                        return self.boundaries.get(key)

                def get_edge(self, x, y, d):
                        be = self.get_boundary(x, y, d)
                        if be is None:
                                return None
                        return be.to_edge_dict()

                def get_front_edge(self, player):
                        if player is None:
                                return None
                        return self.get_edge(player.x, player.y, player.facing)

                def refresh_all_boundary_zone_links(self):
                        for be in self.boundaries.values():
                                be.zone_a, be.zone_b = self._boundary_zone_pair(be.x, be.y, be.d)
                                self._sync_cell_edges_from_boundary(be)

                def set_door_state_mirrored(self, x, y, d, door_state):
                        be = self.get_boundary(x, y, d)
                        if be is None or be.boundary_type != EDGE_DOOR:
                                return False
                        be.door_state = door_state
                        be.blocks_movement, be.blocks_vision = self._compute_boundary_flags(EDGE_DOOR, door_state=door_state)
                        self._sync_cell_edges_from_boundary(be)
                        return True

                # ---------- objects ----------
                def place_object(self, x, y, obj_tag):
                        c = self.get(x, y)
                        if c is None:
                                return False
                        c.objects.append(obj_tag)
                        if obj_tag in ("closet", "wardrobe", "fridge", "table_big"):
                                c.object_blocker = True
                        return True

                # ---------- movement ----------
                def can_move(self, x, y, d):
                        c = self.get(x, y)
                        if c is None:
                                return (False, "out_of_bounds")

                        be = self.get_boundary(x, y, d)
                        if be is None:
                                return (False, "blocked_no_boundary")
                        if be.blocks_movement:
                                return (False, "blocked_boundary")

                        dx, dy = DIR_VEC[d]
                        nx = int(x) + dx
                        ny = int(y) + dy
                        if not self.in_bounds(nx, ny):
                                return (False, "blocked_bounds")

                        nc = self.get(nx, ny)
                        if nc is not None and getattr(nc, "object_blocker", False):
                                return (False, "blocked_object")

                        return (True, "ok")

                # ---------- checker (MVP) ----------
                def boundary_checker_mvp(self):
                        errors = []

                        # Ensure every directed cell-side can resolve to a boundary.
                        for y in range(self.h):
                                for x in range(self.w):
                                        for d in DIRS:
                                                be = self.get_boundary(x, y, d)
                                                if be is None:
                                                        errors.append("missing_boundary (%s,%s,%s)" % (x, y, d))
                                                        continue
                                                # Symmetry via cached edges must match
                                                e1 = self.get_edge(x, y, d)
                                                tgt = self._boundary_target(x, y, d)
                                                if tgt is not None:
                                                        e2 = self.get_edge(tgt[0], tgt[1], OPPOSITE[d])
                                                        t1, o1 = _edge_type_open(e1)
                                                        t2, o2 = _edge_type_open(e2)
                                                        if t1 != t2 or bool(o1) != bool(o2):
                                                                errors.append("asym_edge (%s,%s,%s)" % (x, y, d))
                                                # Zone metadata on boundary should reflect cells
                                                za, zb = self._boundary_zone_pair(be.x, be.y, be.d)
                                                if be.zone_a != za or be.zone_b != zb:
                                                        errors.append("zone_mismatch %r" % (be.key,))

                        # Zone membership consistency
                        for zid, zone in self.zones.items():
                                for (x, y) in zone.cells:
                                        c = self.get(x, y)
                                        if c is None or c.zone_id != zid:
                                                errors.append("zone_membership_bad %s (%s,%s)" % (zid, x, y))
                        for y in range(self.h):
                                for x in range(self.w):
                                        zid = self.get_zone_id(x, y)
                                        if zid is None:
                                                continue
                                        z = self.zones.get(zid)
                                        if z is None or (x, y) not in z.cells:
                                                errors.append("zone_cell_unindexed %s (%s,%s)" % (zid, x, y))

                        return {"ok": len(errors) == 0, "errors": errors}

                # ---------- debug ----------
                def ascii_overview(self, player=None):
                        w = self.w
                        h = self.h
                        out = []

                        for y in range(h):
                                top = []
                                for x in range(w):
                                        c = self.get(x, y)
                                        top.append(" ")
                                        top.append(_edge_glyph(c.edges.get("N"), d="N"))
                                top.append(" ")
                                out.append("".join(top))

                                mid = []
                                for x in range(w):
                                        c = self.get(x, y)
                                        mid.append(_edge_glyph(c.edges.get("W"), d="W"))

                                        ch = "."
                                        if c.zone_id is not None:
                                                # small zone hint: last digit/letter only (keeps map readable)
                                                ch = str(c.zone_id)[-1]
                                        if getattr(c, "object_blocker", False):
                                                ch = "O"
                                        if player is not None and int(player.x) == x and int(player.y) == y:
                                                ch = _player_glyph(getattr(player, "facing", "N"))

                                        mid.append(ch)

                                c_last = self.get(w - 1, y)
                                mid.append(_edge_glyph(c_last.edges.get("E"), d="E"))
                                out.append("".join(mid))

                        bot = []
                        y = h - 1
                        for x in range(w):
                                c = self.get(x, y)
                                bot.append(" ")
                                bot.append(_edge_glyph(c.edges.get("S"), d="S"))
                        bot.append(" ")
                        out.append("".join(bot))

                        return "\n".join(out)