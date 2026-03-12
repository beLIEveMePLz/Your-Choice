# 02_core_player.rpy
# ============================================================
# Core: Player
# Extracted from 00_core.rpy (Stable_001 baseline)
# ============================================================

init -20 python:
        class Player(object):
                def __init__(self, x=0, y=0, facing="N"):
                        self.x = int(x)
                        self.y = int(y)
                        self.facing = facing if facing in DIRS else "N"

                        # pitch: -2..+2 (look up/down). Settles toward 0 after movement.
                        self.pitch = 0

                def turn_left(self):
                        self.facing = LEFT_OF[self.facing]

                def turn_right(self):
                        self.facing = RIGHT_OF[self.facing]

                def look_up(self):
                        if self.pitch > -2:
                                self.pitch -= 1
                                return True
                        return False

                def look_down(self):
                        if self.pitch < 2:
                                self.pitch += 1
                                return True
                        return False

                def look_center(self):
                        if self.pitch != 0:
                                self.pitch = 0
                                return True
                        return False

                def settle_pitch_one_step(self):
                        if self.pitch < 0:
                                self.pitch += 1
                        elif self.pitch > 0:
                                self.pitch -= 1