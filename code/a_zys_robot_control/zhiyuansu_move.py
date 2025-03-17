import sys
sys.path.append("..")
from uprobot_movement import Movement


import time

if __name__ == '__main__':
    #init movement
    mv = Movement()
    time.sleep(1.0)

    mv.move_forward(10, 1000)
    time.sleep(2.0)

    mv.move_backward(10, 1000)
    time.sleep(2.0)
    
    mv.move_left(10, 1000)
    time.sleep(2.0)
    
    mv.move_right(10, 1000)
    time.sleep(2.0)
    
    mv.turn_left(20, 1000)
    time.sleep(2.0)
    
    mv.turn_right(20, 1000)
    time.sleep(2.0)

    while True:
        print("Testing...")
        break