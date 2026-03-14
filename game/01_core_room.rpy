# 01_core_room.rpy
# ============================================================
# Core: Cell + Room (zone + boundary core, compat with renderer/UI)
# First core step for YC Kanwa: boundaries are source-of-truth for movement
# Extended with future-safe vertical link data core (stairs / elevator / ladder)
# ============================================================

init -20 python:

        class SurfaceProfile(object):
                def __init__(self, material_id="default", color="#777777", shade=1.0, texture_id=None, tags=None, meta=None):
                        self.material_id = material_id
                        self.color = color
                        self.shade = float(shade)
                        self.texture_id = texture_id
                        self.tags = set(tags or [])
                        self.meta = dict(meta or {})

                def clone(self):
                        return SurfaceProfile(
                                material_id=self.material_id,
                                color=self.color,
                                shade=self.shade,
                                texture_id=self.texture_id,
                                tags=set(self.tags),
                                meta=dict(self.meta),
                        )

                def to_dict(self):
                        return {
                                "material_id": self.material_id,
                                "color": self.color,
                                "shade": self.shade,
                                "texture_id": self.texture_id,
                                "tags": sorted(list(self.tags)),
                                "meta": dict(self.meta),
                        }


        class Level(object):
                def __init__(self, level_id, name=None, elevation=0.0, floor_z=0.0, ceiling_z=3.0, meta=None):
                        self.level_id = int(level_id)
                        self.name = name or ("level_%s" % level_id)
                        self.elevation = float(elevation)
                        self.floor_z = float(floor_z)
                        self.ceiling_z = float(ceiling_z)
                        self.meta = dict(meta or {})


        class Zone(object):
                def __init__(self, zone_id, name=None, zone_type="room", level_id=0, parent_zone_id=None,
                             tags=None, meta=None, is_interior=True, floor_profile=None,
                             ceiling_profile=None, ceiling_height=3.0):
                        self.zone_id = int(zone_id)
                        self.name = name or ("zone_%s" % zone_id)
                        self.zone_type = zone_type
                        self.level_id = int(level_id)
                        self.parent_zone_id = parent_zone_id
                        self.tags = set(tags or [])
                        self.meta = dict(meta or {})
                        self.is_interior = bool(is_interior)
                        self.floor_profile = floor_profile
                        self.ceiling_profile = ceiling_profile
                        self.ceiling_height = float(ceiling_height)
                        self.cells = set()


        class VerticalLinkEndpoint(object):
                def __init__(self, zone_id, level_id=0, entry_cells=None, anchor_tag=None, facing=None, meta=None):
                        self.zone_id = int(zone_id)
                        self.level_id = int(level_id)
                        self.entry_cells = list(entry_cells or [])
                        self.anchor_tag = anchor_tag
                        self.facing = facing
                        self.meta = dict(meta or {})


        class VerticalLink(object):
                def __init__(self, link_id, zone_a=None, zone_b=None, link_type="stairs", meta=None,
                             endpoint_a=None, endpoint_b=None, is_bidirectional=True,
                             travel_mode=None, travel_time=1.0, requires_free_hands=False,
                             requires_power=False, locked=False, access_tag=None,
                             shaft_zone_ids=None):
                        self.link_id = link_id
                        self.link_type = link_type
                        self.meta = dict(meta or {})

                        self.endpoint_a = endpoint_a
                        self.endpoint_b = endpoint_b

                        # Legacy compatibility with the earlier simple zone_a / zone_b model.
                        if zone_a is None and endpoint_a is not None:
                                zone_a = endpoint_a.zone_id
                        if zone_b is None and endpoint_b is not None:
                                zone_b = endpoint_b.zone_id

                        self.zone_a = zone_a
                        self.zone_b = zone_b
                        self.is_bidirectional = bool(is_bidirectional)
                        self.travel_mode = travel_mode or self._default_travel_mode(link_type)
                        self.travel_time = float(travel_time)
                        self.requires_free_hands = bool(requires_free_hands)
                        self.requires_power = bool(requires_power)
                        self.locked = bool(locked)
                        self.access_tag = access_tag
                        self.shaft_zone_ids = list(shaft_zone_ids or [])

                def _default_travel_mode(self, link_type):
                        if link_type == "elevator":
                                return "ride"
                        if link_type == "ladder":
                                return "climb"
                        return "walk"


        class CeilingOpening(object):
                def __init__(self, opening_id, level_a, level_b, cells=None, opening_type="stair_void",
                             blocks_movement=True, blocks_vision=False, blocks_fall=False, meta=None):
                        self.opening_id = opening_id
                        self.level_a = int(level_a)
                        self.level_b = int(level_b)
                        self.cells = set(cells or [])
                        self.opening_type = opening_type
                        self.blocks_movement = bool(blocks_movement)
                        self.blocks_vision = bool(blocks_vision)
                        self.blocks_fall = bool(blocks_fall)
                        self.meta = dict(meta or {})


        class VisibilityPortal(object):
                def __init__(self, portal_id, from_zone_id, to_zone_id, opening_id=None,
                             portal_type="vertical_void", meta=None):
                        self.portal_id = portal_id
                        self.from_zone_id = int(from_zone_id)
                        self.to_zone_id = int(to_zone_id)
                        self.opening_id = opening_id
                        self.portal_type = portal_type
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
                        self.boundaries = {}          # canonical boundary edges
                        self.vertical_links = []      # stairs / elevator / ladder connections
                        self.levels = {}
                        self.ceiling_openings = {}
                        self.visibility_portals = {}
                        self.define_level(0, name="ground")

                # ---------- base grid ----------
                def in_bounds(self, x, y):
                        return 0 <= int(x) < self.w and 0 <= int(y) < self.h

                def get(self, x, y):
                        if not self.in_bounds(x, y):
                                return None
                        return self.grid[int(y)][int(x)]

                # ---------- levels ----------
                def define_level(self, level_id, name=None, elevation=0.0, floor_z=0.0, ceiling_z=3.0, meta=None):
                        lid = int(level_id)
                        lvl = self.levels.get(lid)
                        if lvl is None:
                                lvl = Level(lid, name=name, elevation=elevation, floor_z=floor_z, ceiling_z=ceiling_z, meta=meta)
                                self.levels[lid] = lvl
                        else:
                                if name is not None:
                                        lvl.name = name
                                lvl.elevation = float(elevation)
                                lvl.floor_z = float(floor_z)
                                lvl.ceiling_z = float(ceiling_z)
                                if meta:
                                        lvl.meta.update(meta)
                        return lvl

                def get_level(self, level_id):
                        return self.levels.get(int(level_id))

                # ---------- zones ----------

                def _surface_profile_from_value(self, value):
                        if value is None:
                                return None
                        if isinstance(value, SurfaceProfile):
                                return value.clone()
                        if isinstance(value, dict):
                                return SurfaceProfile(
                                        material_id=value.get("material_id", "default"),
                                        color=value.get("color", "#777777"),
                                        shade=value.get("shade", 1.0),
                                        texture_id=value.get("texture_id"),
                                        tags=value.get("tags", []),
                                        meta=value.get("meta", {}),
                                )
                        return SurfaceProfile(material_id=str(value))

                def _default_zone_shell_type(self, zone_type, tags=None):
                        zt = (zone_type or "").lower()
                        tagset = set(tags or [])
                        if "exterior" in tagset or zt in ("exterior", "outdoor", "yard", "garden", "street", "roof_open", "outside"):
                                return "exterior"
                        return "interior"

                def _default_floor_profile(self, zone_type="room", tags=None, shell_type="interior"):
                        zt = (zone_type or "").lower()
                        tagset = set(tags or [])
                        if shell_type == "exterior":
                                if "garden" in tagset or zt in ("garden", "yard"):
                                        return SurfaceProfile("grass", "#5f7f52", shade=0.95, tags=["ground", "exterior", "grass"])
                                if zt in ("street", "road"):
                                        return SurfaceProfile("asphalt", "#5e6168", shade=0.92, tags=["ground", "exterior", "street"])
                                return SurfaceProfile("concrete_outdoor", "#7c7c79", shade=0.94, tags=["ground", "exterior"])
                        if zt in ("kitchen", "bathroom", "utility"):
                                return SurfaceProfile("tile", "#8c8f93", shade=0.98, tags=["interior", "tile"])
                        if zt in ("hall", "corridor", "stairwell"):
                                return SurfaceProfile("hall_floor", "#7f735f", shade=0.97, tags=["interior", "hall"])
                        return SurfaceProfile("wood_floor", "#80664d", shade=1.0, tags=["interior", "wood"])

                def _default_ceiling_profile(self, zone_type="room", tags=None, shell_type="interior"):
                        if shell_type != "interior":
                                return None
                        zt = (zone_type or "").lower()
                        if zt == "stairwell":
                                return SurfaceProfile("painted_ceiling", "#c9c9c4", shade=0.99, tags=["interior", "ceiling", "stairwell"])
                        return SurfaceProfile("painted_ceiling", "#d7d5cf", shade=1.0, tags=["interior", "ceiling"])

                def define_zone(self, zone_id, name=None, zone_type="room", level_id=0, parent_zone_id=None,
                                tags=None, meta=None, is_interior=None, floor_profile=None,
                                ceiling_profile=None, ceiling_height=None):
                        zid = int(zone_id)
                        tagset = set(tags or [])
                        shell_type = self._default_zone_shell_type(zone_type, tagset)
                        interior_flag = (shell_type != "exterior") if is_interior is None else bool(is_interior)

                        z = self.zones.get(zid)
                        if z is None:
                                z = Zone(
                                        zid,
                                        name=name,
                                        zone_type=zone_type,
                                        level_id=level_id,
                                        parent_zone_id=parent_zone_id,
                                        tags=tagset,
                                        meta=meta,
                                        is_interior=interior_flag,
                                        floor_profile=self._surface_profile_from_value(floor_profile),
                                        ceiling_profile=self._surface_profile_from_value(ceiling_profile),
                                        ceiling_height=(3.0 if ceiling_height is None else ceiling_height),
                                )
                                self.zones[zid] = z
                        else:
                                if name is not None:
                                        z.name = name
                                if zone_type is not None:
                                        z.zone_type = zone_type
                                z.level_id = int(level_id)
                                z.parent_zone_id = parent_zone_id
                                if tags is not None:
                                        z.tags = set(tags)
                                if meta:
                                        z.meta.update(meta)
                                if is_interior is not None:
                                        z.is_interior = bool(is_interior)
                                if floor_profile is not None:
                                        z.floor_profile = self._surface_profile_from_value(floor_profile)
                                if ceiling_profile is not None:
                                        z.ceiling_profile = self._surface_profile_from_value(ceiling_profile)
                                if ceiling_height is not None:
                                        z.ceiling_height = float(ceiling_height)

                        if int(level_id) not in self.levels:
                                self.define_level(int(level_id))

                        if z.floor_profile is None:
                                z.floor_profile = self._default_floor_profile(z.zone_type, z.tags, "interior" if z.is_interior else "exterior")
                        if z.is_interior:
                                if z.ceiling_profile is None:
                                        z.ceiling_profile = self._default_ceiling_profile(z.zone_type, z.tags, "interior")
                                if ceiling_height is None and getattr(z, "ceiling_height", None) is None:
                                        z.ceiling_height = 3.0
                        else:
                                z.ceiling_profile = None

                        if "shell_type" not in z.meta:
                                z.meta["shell_type"] = "interior" if z.is_interior else "exterior"

                        return z

                def get_zone(self, zone_id):
                        if zone_id is None:
                                return None
                        return self.zones.get(int(zone_id))

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

                def get_zone_level_id(self, zone_id, default=None):
                        z = self.get_zone(zone_id)
                        if z is None:
                                return default
                        return z.level_id


                def get_zone_at(self, x, y):
                        zid = self.get_zone_id(x, y)
                        if zid is None:
                                return None
                        return self.get_zone(zid)

                def set_zone_floor_profile(self, zone_id, profile):
                        z = self.get_zone(zone_id)
                        if z is None:
                                return False
                        z.floor_profile = self._surface_profile_from_value(profile)
                        return True

                def set_zone_ceiling_profile(self, zone_id, profile):
                        z = self.get_zone(zone_id)
                        if z is None:
                                return False
                        if not getattr(z, "is_interior", True):
                                z.ceiling_profile = None
                                return False
                        z.ceiling_profile = self._surface_profile_from_value(profile)
                        return True

                def get_zone_floor_profile(self, zone_id):
                        z = self.get_zone(zone_id)
                        if z is None:
                                return None
                        return getattr(z, "floor_profile", None)

                def get_zone_ceiling_profile(self, zone_id):
                        z = self.get_zone(zone_id)
                        if z is None:
                                return None
                        return getattr(z, "ceiling_profile", None)

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

                # ---------- vertical links / openings / portals ----------
                def add_vertical_link(self, link):
                        if link is None:
                                return False
                        self.vertical_links.append(link)
                        return True

                def build_vertical_link(self, link_id, zone_a, zone_b, link_type="stairs",
                                        level_a=None, level_b=None, entry_cells_a=None, entry_cells_b=None,
                                        anchor_tag_a=None, anchor_tag_b=None, facing_a=None, facing_b=None,
                                        is_bidirectional=True, travel_mode=None, travel_time=1.0,
                                        requires_free_hands=False, requires_power=False,
                                        locked=False, access_tag=None, shaft_zone_ids=None, meta=None):
                        if level_a is None:
                                level_a = self.get_zone_level_id(zone_a, default=0)
                        if level_b is None:
                                level_b = self.get_zone_level_id(zone_b, default=0)
                        ep_a = VerticalLinkEndpoint(zone_a, level_id=level_a, entry_cells=entry_cells_a, anchor_tag=anchor_tag_a, facing=facing_a)
                        ep_b = VerticalLinkEndpoint(zone_b, level_id=level_b, entry_cells=entry_cells_b, anchor_tag=anchor_tag_b, facing=facing_b)
                        link = VerticalLink(
                                link_id,
                                zone_a=zone_a,
                                zone_b=zone_b,
                                link_type=link_type,
                                meta=meta,
                                endpoint_a=ep_a,
                                endpoint_b=ep_b,
                                is_bidirectional=is_bidirectional,
                                travel_mode=travel_mode,
                                travel_time=travel_time,
                                requires_free_hands=requires_free_hands,
                                requires_power=requires_power,
                                locked=locked,
                                access_tag=access_tag,
                                shaft_zone_ids=shaft_zone_ids,
                        )
                        self.vertical_links.append(link)
                        return link

                def get_vertical_link(self, link_id):
                        for link in self.vertical_links:
                                if getattr(link, "link_id", None) == link_id:
                                        return link
                        return None

                def add_ceiling_opening(self, opening):
                        if opening is None:
                                return False
                        self.ceiling_openings[opening.opening_id] = opening
                        return True

                def build_ceiling_opening(self, opening_id, level_a, level_b, cells=None, opening_type="stair_void",
                                          blocks_movement=True, blocks_vision=False, blocks_fall=False, meta=None):
                        opening = CeilingOpening(
                                opening_id,
                                level_a,
                                level_b,
                                cells=cells,
                                opening_type=opening_type,
                                blocks_movement=blocks_movement,
                                blocks_vision=blocks_vision,
                                blocks_fall=blocks_fall,
                                meta=meta,
                        )
                        self.ceiling_openings[opening.opening_id] = opening
                        return opening

                def get_ceiling_opening(self, opening_id):
                        return self.ceiling_openings.get(opening_id)

                def add_visibility_portal(self, portal):
                        if portal is None:
                                return False
                        self.visibility_portals[portal.portal_id] = portal
                        return True

                def build_visibility_portal(self, portal_id, from_zone_id, to_zone_id, opening_id=None,
                                            portal_type="vertical_void", meta=None):
                        portal = VisibilityPortal(
                                portal_id,
                                from_zone_id,
                                to_zone_id,
                                opening_id=opening_id,
                                portal_type=portal_type,
                                meta=meta,
                        )
                        self.visibility_portals[portal.portal_id] = portal
                        return portal

                def get_visibility_portal(self, portal_id):
                        return self.visibility_portals.get(portal_id)

                def vertical_core_checker(self):
                        errors = []

                        for lid, lvl in self.levels.items():
                                if lid != int(getattr(lvl, "level_id", lid)):
                                        errors.append("level_id_mismatch %r" % (lid,))
                                if float(lvl.ceiling_z) <= float(lvl.floor_z):
                                        errors.append("level_bad_z_range %r" % (lid,))

                        for zid, zone in self.zones.items():
                                if zone.level_id not in self.levels:
                                        errors.append("zone_missing_level %r" % (zid,))
                                if zone.parent_zone_id is not None and zone.parent_zone_id not in self.zones:
                                        errors.append("zone_missing_parent %r" % (zid,))

                        seen_link_ids = set()
                        for link in self.vertical_links:
                                lid = getattr(link, "link_id", None)
                                if lid in seen_link_ids:
                                        errors.append("dup_vertical_link %r" % (lid,))
                                seen_link_ids.add(lid)

                                if link.zone_a is None or link.zone_b is None:
                                        errors.append("vertical_link_missing_zone %r" % (lid,))
                                else:
                                        if link.zone_a not in self.zones:
                                                errors.append("vertical_link_bad_zone_a %r" % (lid,))
                                        if link.zone_b not in self.zones:
                                                errors.append("vertical_link_bad_zone_b %r" % (lid,))

                                if link.endpoint_a is not None and link.endpoint_a.zone_id != link.zone_a:
                                        errors.append("vertical_link_endpoint_a_zone_mismatch %r" % (lid,))
                                if link.endpoint_b is not None and link.endpoint_b.zone_id != link.zone_b:
                                        errors.append("vertical_link_endpoint_b_zone_mismatch %r" % (lid,))

                                if link.endpoint_a is not None and link.endpoint_a.level_id not in self.levels:
                                        errors.append("vertical_link_endpoint_a_bad_level %r" % (lid,))
                                if link.endpoint_b is not None and link.endpoint_b.level_id not in self.levels:
                                        errors.append("vertical_link_endpoint_b_bad_level %r" % (lid,))

                        for oid, opening in self.ceiling_openings.items():
                                if opening.level_a not in self.levels or opening.level_b not in self.levels:
                                        errors.append("opening_bad_level %r" % (oid,))
                                if int(opening.level_a) == int(opening.level_b):
                                        errors.append("opening_same_level %r" % (oid,))

                        for pid, portal in self.visibility_portals.items():
                                if portal.from_zone_id not in self.zones:
                                        errors.append("portal_bad_from_zone %r" % (pid,))
                                if portal.to_zone_id not in self.zones:
                                        errors.append("portal_bad_to_zone %r" % (pid,))
                                if portal.opening_id is not None and portal.opening_id not in self.ceiling_openings:
                                        errors.append("portal_missing_opening %r" % (pid,))

                        return {"ok": len(errors) == 0, "errors": errors}


                def surface_core_checker(self):
                        errors = []
                        for zid, zone in self.zones.items():
                                if getattr(zone, "floor_profile", None) is None:
                                        errors.append("zone_missing_floor_profile %r" % (zid,))
                                if getattr(zone, "is_interior", True):
                                        if getattr(zone, "ceiling_profile", None) is None:
                                                errors.append("interior_zone_missing_ceiling %r" % (zid,))
                                        if float(getattr(zone, "ceiling_height", 0.0)) <= 0.0:
                                                errors.append("zone_bad_ceiling_height %r" % (zid,))
                                else:
                                        if getattr(zone, "ceiling_profile", None) is not None:
                                                errors.append("exterior_zone_has_ceiling %r" % (zid,))
                        return {"ok": len(errors) == 0, "errors": errors}


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
