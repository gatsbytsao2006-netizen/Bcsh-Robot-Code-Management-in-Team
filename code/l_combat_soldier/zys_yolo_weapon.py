import cv2
import sys
import time

from rknn_func_weapon.rknnpool import rknnPoolExecutor
from rknn_func_weapon.func import myFunc

sys.path.append("..")
from uprobot_movement import Movement


class YoloDetect:
    def __init__(self):
        self.target = "hammer"
        self.arm_actions = {
            "clamp": [2048, 2048, 620, 2670, 600, 2048, 3500, 1400],
            "pre_hit": [2048, 2048, 620, 2670, 1200, 1800, 3500, 2500],
            "hit": [2048, 2048, 620, 2670, 3000, 1800, 3500, 2050]
        }

        self.movement = Movement()

        # 打开摄像头，使用默认摄像头（索引为0）
        self.cap = cv2.VideoCapture(0)

        modelPath = sys.path[0] + "/rknnModel/combat_quantized_mmse.rknn"

        # 线程数, 增大可提高帧率
        TPEs = 4
        # 初始化rknn池
        self.pool = rknnPoolExecutor(rknnModel=modelPath, TPEs=TPEs, func=myFunc)

        # 设置一个窗口来显示图像  
        self.result_name = "Yolo Detect Image"
        cv2.namedWindow(self.result_name, cv2.WINDOW_NORMAL)

        if not self.cap.isOpened():
            self.isOpen = False
            print("无法打开摄像头,请检查线路连接!!!")
        else:
            self.isOpen = True
            print("成功打开摄像头")

        if self.isOpen:

            # 初始化异步所需要的帧
            for i in range(TPEs + 1):
                ret, frame = self.cap.read()
                frame = cv2.resize(frame, (640, 480))
                self.pool.put(frame)

            while True:

                ret, frame = self.cap.read()
                frame = cv2.resize(frame, (640, 480))
                result = self.update_frame(frame)

                cv2.imshow(self.result_name, result)

                key = cv2.waitKey(30) & 0xFF  # 等待1ms，并获取按键信息 

                if key == ord('q'):  # 如果按下'q'键，则退出循环 
                    self.cleanup()
                    break

    # yolo检测，输入图像
    def update_frame(self, frame):
        self.pool.put(frame)
        (frame, center_list, class_list), flag = self.pool.get()

        for center, name in zip(center_list, class_list):
            if name == self.target:
                screen_center_x = frame.shape[1] / 2
                offset = center[0] - screen_center_x
                self.hit_target(offset)

            else:
                self.movement.call_servo_control(self.arm_actions["clamp"], 10)

        result = frame.copy()
        return result

    def hit_target(self, offset):
        if offset >= 40:
            self.movement.move_right(20, 10)
        elif offset <= -40:
            self.movement.move_left(20, 10)
        else:
            self.movement.call_servo_control(self.arm_actions["pre_hit"], 10)
            time.sleep(2.0)
            self.movement.call_servo_control(self.arm_actions["hit"], 10)
            time.sleep(2.0)

    def cleanup(self):
        # 关闭OpenCV窗口  
        cv2.destroyAllWindows()
        self.pool.release()


if __name__ == '__main__':
    yolo_detect = YoloDetect()
