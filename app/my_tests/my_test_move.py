from sdk.application_layer.action import Action
import time


def stop_robot(api):
    """
    停止底盘。
    """
    api.move_translation(angle=0, speed=0, run_time=10)
    time.sleep(0.5)


def run_translation_test(api, name, angle):
    """
    测试一个平移方向。
    """
    print(f"开始测试：{name}")

    api.move_translation(
        angle=angle,
        speed=10,
        run_time=1000
    )

    time.sleep(1)

    stop_robot(api)

    print(f"结束测试：{name}")
    time.sleep(1)


def run_rotation_test(api, name, turn_rate):
    """
    测试一个旋转方向。
    """
    print(f"开始测试：{name}")

    api.move_rotation(
        speed=0,
        turn_rate=turn_rate,
        run_time=1000
    )

    time.sleep(1)

    stop_robot(api)

    print(f"结束测试：{name}")
    time.sleep(1)


if __name__ == "__main__":
    api = None

    try:
        # 直接使用底盘 Action，不加载 YOLO 模型
        api = Action()

        run_translation_test(api, "前进", 0)
        run_translation_test(api, "后退", 180)
        run_translation_test(api, "左移", 90)
        run_translation_test(api, "右移", 270)

        run_rotation_test(api, "左旋", 20)
        run_rotation_test(api, "右旋", -20)

        print("全部底盘动作测试完成")

    except KeyboardInterrupt:
        print("\n检测到 Ctrl+C，正在停止机器人")

    except Exception as error:
        print(f"\n程序发生错误：{error}")

    finally:
        if api is not None:
            try:
                stop_robot(api)
                api.clean_up()
            except Exception as error:
                print(f"停止或清理资源时发生错误：{error}")

        print("程序结束，底盘已停止")