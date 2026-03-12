# 03_core_world.rpy
# ============================================================
# Core: World (state + movement)
# + generic directional step for strafe/back
# ============================================================

init -20 python:
        class World(object):
                def __init__(self, room, player):
                        self.room = room
                        self.player = player
                        self.last_move_result = "init"
                        self.tick = 0
                        self.logic_revision = 0

                def state_view_key(self):
                        p = self.player
                        return (self.room.name, p.x, p.y, p.facing, p.pitch)

                def _touch_logic(self):
                        self.tick += 1
                        self.logic_revision += 1

                def step_dir(self, d):
                        # Generic movement in any compass direction (N/E/S/W)
                        ok, why = self.room.can_move(self.player.x, self.player.y, d)
                        self.last_move_result = why
                        if ok:
                                dx, dy = DIR_VEC[d]
                                self.player.x += dx
                                self.player.y += dy
                                # keep same behavior as forward: pitch settles after movement
                                self.player.settle_pitch_one_step()
                                self._touch_logic()
                        return ok, why

                def step_forward(self):
                        return self.step_dir(self.player.facing)

                def turn_left(self):
                        self.player.turn_left()
                        self._touch_logic()

                def turn_right(self):
                        self.player.turn_right()
                        self._touch_logic()

                def look_up(self):
                        changed = self.player.look_up()
                        if changed:
                                self._touch_logic()
                        return changed

                def look_down(self):
                        changed = self.player.look_down()
                        if changed:
                                self._touch_logic()
                        return changed

                def look_center(self):
                        changed = self.player.look_center()
                        if changed:
                                self._touch_logic()
                        return changed