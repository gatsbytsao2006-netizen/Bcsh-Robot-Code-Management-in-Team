import sys
sys.path.append("..")
from uprobot_movement import Movement

import time

if __name__ == '__main__':
    #init movement
    mv = Movement()
    
    print("Action 0 !!!")
    mv.deal_action(0)
    time.sleep(1.0)

    print("Action 1 !!!")
    mv.deal_action(1)
    time.sleep(1.0)

    print("Action 2 !!!")
    mv.deal_action(2)
    time.sleep(1.0)

    print("Action 3 !!!")
    mv.deal_action(3)
    time.sleep(1.0)

    print("Action 4 !!!")
    mv.deal_action(4)
    time.sleep(1.0)

    print("Action 5 !!!")
    mv.deal_action(5)
    time.sleep(1.0)

    print("Action 6 !!!")
    mv.deal_action(6)
    time.sleep(1.0)

    print("Action 7 !!!")
    mv.deal_action(7)
    time.sleep(1.0)    

    print("Action 8 !!!")
    mv.deal_action(78)
    time.sleep(1.0) 

    while True:
        print("Testing...")
        break