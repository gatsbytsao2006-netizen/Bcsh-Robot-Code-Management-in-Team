import sys
sys.path.append("..")
from uprobot_movement import Movement

import time

if __name__ == '__main__':
    # init movement
    mv = Movement()
    
    print("Left UP Right Down !!!")
    servo_position = [2150, 2150, 650, 1200, 2150, 2200, 3600, 1400]
    run_time = 2
    mv.call_servo_control(servo_position, run_time)
    time.sleep(3.0)

    print("Left Down Right Up !!!")
    servo_position = [2150, 2150, 650, 2670, 2150, 2200, 3600, 2900]
    run_time = 2
    mv.call_servo_control(servo_position, run_time)
    time.sleep(3.0)

    print("Both UP !!!")
    servo_position = [2150, 2150, 650, 1200, 2150, 2200, 3600, 2900]
    run_time = 2
    mv.call_servo_control(servo_position, run_time)
    time.sleep(3.0)
    
    print("Hover !!!")
    servo_position = [2150, 2200, 600, 2200, 2150, 2150, 3300, 2200]
    run_time = 2
    mv.call_servo_control(servo_position, run_time)
    time.sleep(3.0)
    
    print("Open Arm !!!")
    servo_position = [2140, 3440, 1900, 2200, 3400, 600, 2030, 2200]
    run_time = 2
    mv.call_servo_control(servo_position, run_time)
    time.sleep(3.0)

    print("Hug !!!")
    servo_position = [0, 0, 500, 1900, 0, 0, 3500, 2150]
    run_time = 2
    mv.call_servo_control(servo_position, run_time)
    time.sleep(3.0)
    
    while True:
        print("Testing...")
        break