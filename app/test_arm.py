from sdk.api import UpAPI
from sdk.data_layer.arm import arm_action_factory as data_arm
import time


def get_time_ms():
    return int(time.time() * 1000)


class Controller:
    BOTH_DOWN, BOTH_UP, LEFT_UP_RIGHT_DOWN, LEFT_DOWN_RIGHT_UP, HOVER, OPEN_ARM, HUG, FINISH = range(8)

    def __init__(self):
        self.state = self.BOTH_DOWN
        self.start_action_time = get_time_ms()
        self.action_interval = 1000

    def update(self):
        if self.state == self.BOTH_DOWN:
            if self.is_complete():
                self.state = self.BOTH_UP

        elif self.state == self.BOTH_UP:
            if self.is_complete():
                self.state = self.LEFT_UP_RIGHT_DOWN

        elif self.state == self.LEFT_UP_RIGHT_DOWN:
            if self.is_complete():
                self.state = self.LEFT_DOWN_RIGHT_UP

        elif self.state == self.LEFT_DOWN_RIGHT_UP:
            if self.is_complete():
                self.state = self.HOVER

        elif self.state == self.HOVER:
            if self.is_complete():
                self.state = self.FINISH

        elif self.state == self.OPEN_ARM:
            if self.is_complete():
                self.state = self.HUG

        elif self.state == self.HUG:
            if self.is_complete():
                self.state = self.FINISH

        elif self.state == self.FINISH:
            pass

    def is_complete(self):
        current_time = get_time_ms()
        if current_time - self.start_action_time >= self.action_interval:
            self.start_action_time = current_time
            return True
        return False


if __name__ == '__main__':
    api = UpAPI()
    controller = Controller()

    while True:

        controller.update()

        if controller.state == controller.BOTH_DOWN:
            api.put_down_arms()

        elif controller.state == controller.BOTH_UP:
            api.raise_arms()

        elif controller.state == controller.LEFT_UP_RIGHT_DOWN:
            api.raise_left_arm()

        elif controller.state == controller.LEFT_DOWN_RIGHT_UP:
            api.raise_right_arm()

        elif controller.state == controller.HOVER:
            api.hover_arms()

        elif controller.state == controller.OPEN_ARM:
            api.open_arms()

        elif controller.state == controller.HUG:
            api.hug_arms()

        elif controller.state == controller.FINISH:
            print("finish")
            api.hover_arms()
            break
