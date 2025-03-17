import sys
sys.path.append("..")
from uprobot_movement import Movement

import time

if __name__ == '__main__':
    #init movement
    mv = Movement()
    
    print("Left UP Right Down !!!")
    servo_position = [0, 0, 0, 1100, 0, 0, 0, 1300]
    run_time = 10
    mv.call_servo_control(servo_position, run_time)
    time.sleep(5.0)

    print("Left Down Right Up !!!")
    servo_position = [0, 0, 0, 2700, 0, 0, 0, 3000]
    run_time = 10
    mv.call_servo_control(servo_position, run_time)
    time.sleep(5.0)

    print("Both UP !!!")
    servo_position = [0, 0, 0, 1100, 0, 0, 0, 3000]
    run_time = 10
    mv.call_servo_control(servo_position, run_time)
    time.sleep(5.0)
    
    print("Hover !!!")
    servo_position = [0, 0, 0, 1900, 0, 0, 0, 2150]
    run_time = 10
    mv.call_servo_control(servo_position, run_time)
    time.sleep(5.0)
    
    print("Open Arm !!!")
    servo_position = [0, 0, 1900, 1900, 0, 0, 1900, 2150]
    run_time = 10
    mv.call_servo_control(servo_position, run_time)
    time.sleep(5.0)    

    print("Hug !!!")
    servo_position = [0, 0, 500, 1900, 0, 0, 3500, 2150]
    run_time = 10
    mv.call_servo_control(servo_position, run_time)
    time.sleep(5.0)  
    
    while True:
        print("Testing...")
        break