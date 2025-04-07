from sdk.api import UpAPI

import sys, time

sys.path.append("..")
from uprobot_movement import Movement

# 参数
grayscale_threshold = 2000  # 灰度传感器检测阈值
init_position = [2150, 2200, 600, 2200, 2150, 2150, 3300, 2200]  # 架拳
stop_position = [2150, 2150, 650, 2670, 2150, 2200, 3600, 2900]  # 举右手
servo_run_time = 2

# 初始化移动控制和传感器
movement = Movement()
sensor = UpAPI(grayscale_threshold=grayscale_threshold)

# 初始化手臂
movement.call_servo_control(init_position, servo_run_time)
time.sleep(3.0)

# 主循环
while True:

    # 获取灰度传感器数据
    grayscale_data = sensor.grayscale_data()
    print(f"灰度传感器数字量：{grayscale_data}")

    # 移动
    if grayscale_data[2] or grayscale_data[3] or grayscale_data[4]:
        movement.stop()
        movement.call_servo_control(stop_position, servo_run_time)
        time.sleep(3.0)

    elif grayscale_data[5] or grayscale_data[6]:
        movement.move_right(4)

    elif grayscale_data[0] or grayscale_data[1]:
        movement.move_left(4)
