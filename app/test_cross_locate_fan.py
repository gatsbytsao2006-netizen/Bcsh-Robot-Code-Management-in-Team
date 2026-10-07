from sdk.logic_layer.cross_planner import CrossLocator
from sdk.api import UpAPI
from enum import Enum, auto
import time


class State(Enum):
    LINE = auto()
    LOCATION = auto()


if __name__ == '__main__':
    locate_speed = 4
    line_follower_speed = 8
    turn_speed = 20

    # 暂定容错时间，需要结合实际探头间距、速度验证
    lost_line_timeout = 0.3
    loop_interval = 0.02

    state = State.LINE
    api = UpAPI(grayscale_threshold=650)
    locator = CrossLocator()

    lost_since = None
    last_action = None

    def execute_action(action):
        """执行动作，同时记录上一次定位方向。"""
        global last_action
        last_action = action

        if action == "left":
            api.move_left(locate_speed)
        elif action == "right":
            api.move_right(locate_speed)
        elif action == "spin_left":
            api.spin_left(turn_speed)
        elif action == "spin_right":
            api.spin_right(turn_speed)
        elif action == "forward":
            api.move_forward(locate_speed)

    try:
        while True:
            grayscale_data = api.get_grayscale_data()
            print(f"grayscale_data: {grayscale_data}")

            # 数据格式异常时停止，不沿用运动指令
            if grayscale_data is None or len(grayscale_data) != 7:
                print("传感器数据异常，停车")
                break

            if state == State.LINE:
                if locator.detect_black(grayscale_data):
                    print("检测到黑线，进入定位阶段")
                    api.stop()
                    state = State.LOCATION
                    lost_since = None

                    # 根据首次检测到黑线的位置，记录后续修正方向
                    if grayscale_data[3]:
                       last_action = "forward"
                    elif any(grayscale_data[:3]):
                        last_action = "left"
                    elif any(grayscale_data[4:]):
                        last_action = "right"
                    else:
                        last_action = None
                    print("接近黑线，前进")
                    api.move_forward(line_follower_speed)

            elif state == State.LOCATION:
                if not any(grayscale_data):
                    # 第一次丢线时开始计时
                    if lost_since is None:
                        lost_since = time.monotonic()

                    lost_duration = time.monotonic() - lost_since

                    if lost_duration >= lost_line_timeout:
                        print("持续丢线超过容错时间，停车")
                        break

                    if last_action is None:
                        print("丢线且没有可参考的方向，停车")
                        break

                    print(
                        f"短暂丢线 {lost_duration:.2f} 秒，"
                        f"保持上一次动作：{last_action}"
                    )
                    execute_action(last_action)

                else:
                    # 再次检测到黑线，清除丢线计时
                    lost_since = None

                    if locator.translate_to_center(grayscale_data):
                        if locator.reach_target(grayscale_data):
                            print("定位完成，停车")
                            break

                        elif locator.translate_left(grayscale_data):
                            print("中心检测到黑线，左平移")
                            execute_action("left")

                        elif locator.translate_right(grayscale_data):
                            print("中心检测到黑线，右平移")
                            execute_action("right")

                        elif locator.seeking_left(grayscale_data):
                            print("中心检测到黑线，原地左旋")
                            execute_action("spin_left")

                        elif locator.seeking_right(grayscale_data):
                            print("中心检测到黑线，原地右旋")
                            execute_action("spin_right")

                        else:
                            print("中心检测到黑线，前进")
                            execute_action("forward")

                    elif any(grayscale_data[:3]):
                        print("中心未检测到黑线，左平移")
                        execute_action("left")

                    elif any(grayscale_data[4:]):
                        print("中心未检测到黑线，右平移")
                        execute_action("right")

                    else:
                        print("无法判断修正方向，停车")
                        break

            else:
                print("未知状态，停车")
                break

            time.sleep(loop_interval)

    except KeyboardInterrupt:
        print("\n手动结束程序")

    finally:
        api.stop()
        print("已发送停车指令")
