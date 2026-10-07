from sdk.application_layer.action import Action
import time

api = None

try:
    api = Action()

    print("开始低速前进测试，观察右轮是否转动")
    api.move_translation(angle=0, speed=5, run_time=300)
    time.sleep(1)

    print("停止")
    api.move_translation(angle=0, speed=0, run_time=10)
    time.sleep(1)

except KeyboardInterrupt:
    print("收到 Ctrl+C，停止机器人")

except Exception as error:
    print("发生错误：", error)

finally:
    if api is not None:
        try:
            api.move_translation(angle=0, speed=0, run_time=10)
            api.clean_up()
        except Exception as error:
            print("清理时发生错误：", error)

    print("测试结束")