# 00_core_utils.rpy
# ============================================================
# Core utils + constants (compat version)
# ============================================================

init -20 python:
        import renpy as rp

        DIRS = ("N", "E", "S", "W")
        DIR_VEC = {
                "N": (0, -1),
                "E": (1, 0),
                "S": (0, 1),
                "W": (-1, 0),
        }
        LEFT_OF = {"N": "W", "W": "S", "S": "E", "E": "N"}
        RIGHT_OF = {"N": "E", "E": "S", "S": "W", "W": "N"}
        OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}

        EDGE_WALL = "wall"
        EDGE_OPEN = "open"
        EDGE_DOOR = "door"
        DOOR_LOCKED = "locked"
        DOOR_CLOSED = "closed"
        DOOR_AJAR = "ajar"
        DOOR_OPEN = "open"
        EDGE_UNKNOWN = "unknown"
        # Compat edge types used by renderer variants
        EDGE_WINDOW_VIEW = "window_view"   # window with outside/sky view
        EDGE_WINDOW = "window"             # plain window / opaque window
        EDGE_PORTAL = "portal"             # reserved for room-to-room links

        def _edge_dict(edge_type, open_state=False, door_state=None):
                e = {"type": edge_type, "open": bool(open_state)}
                if edge_type == EDGE_DOOR:
                        if door_state is None:
                                if bool(open_state):
                                        door_state = DOOR_OPEN
                                else:
                                        door_state = DOOR_CLOSED
                        e["door_state"] = door_state
                        e["open"] = bool(door_state in (DOOR_AJAR, DOOR_OPEN))
                return e

        def _edge_type_open(edge):
                # Compat: supports dict or old tuple form (type, open)
                if isinstance(edge, dict):
                        return edge.get("type", EDGE_UNKNOWN), bool(edge.get("open", False))
                if isinstance(edge, (tuple, list)) and len(edge) >= 2:
                        return edge[0], bool(edge[1])
                return EDGE_UNKNOWN, False

        def _door_state(edge):
                if isinstance(edge, dict):
                        if edge.get("type") != EDGE_DOOR:
                                return None
                        ds = edge.get("door_state", None)
                        if ds in (DOOR_LOCKED, DOOR_CLOSED, DOOR_AJAR, DOOR_OPEN):
                                return ds
                        return DOOR_OPEN if bool(edge.get("open", False)) else DOOR_CLOSED
                return None

        def _door_open_flag_from_state(door_state):
                return bool(door_state in (DOOR_AJAR, DOOR_OPEN))

        def _edge_is_traversable(edge, open_state=None):
                # Compat:
                # - new usage: _edge_is_traversable(edge_dict)
                # - old usage: _edge_is_traversable(edge_type, open_state)
                if isinstance(edge, dict) or isinstance(edge, (tuple, list)):
                        edge_type, op = _edge_type_open(edge)
                else:
                        edge_type = edge
                        op = bool(open_state)

                if edge_type == EDGE_OPEN:
                        return True
                if edge_type == EDGE_DOOR:
                        ds = _door_state(edge)
                        if ds is not None:
                                return ds in (DOOR_AJAR, DOOR_OPEN)
                        return bool(op)
                return False

        def _edge_glyph(edge, open_state=None, d="N"):
                # Compat for dict or (type,open) or (type, open, d old call style)
                if isinstance(edge, dict) or isinstance(edge, (tuple, list)):
                        edge_type, op = _edge_type_open(edge)
                        direction = d
                else:
                        edge_type = edge
                        op = bool(open_state)
                        direction = d

                if edge_type == EDGE_OPEN:
                        return " "
                if edge_type == EDGE_DOOR:
                        ds = _door_state(edge)
                        if ds == DOOR_LOCKED:
                                return "X"
                        if ds == DOOR_CLOSED:
                                return "/"
                        if ds == DOOR_AJAR:
                                return "\\"
                        return " "
                return "|" if direction in ("E", "W") else "-" 

        def _player_glyph(facing):
                return {"N": "^", "E": ">", "S": "v", "W": "<"}.get(facing, "@")