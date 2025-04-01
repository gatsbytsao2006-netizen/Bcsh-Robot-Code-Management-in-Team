# main.py
import time

import cv2
from face_reid import FaceDetector

import sys

sys.path.append("..")
from uprobot_movement import Movement

debug = True

offset_limit = 30

arm_actions = {
    "clamp": [2048, 2048, 620, 2670, 600, 2048, 3500, 1400],
    "pre_hit": [2048, 2048, 620, 2670, 1200, 1800, 3500, 2500],
    "hit": [2048, 2048, 620, 2670, 3000, 1800, 3500, 2050]
}

# 初始化移动控制
mv = Movement()

# 初始化检测器
face_detector = FaceDetector()

# 启动摄像头
cap = cv2.VideoCapture(0)

try:
    while True:
        ret, frame = cap.read()

        if not ret:
            print("没有图像,检查摄像头,程序将会退出")
            break

        # frame = cv2.flip(frame,-1)

        # 进行识别, 并打印识别结果
        detections = face_detector.detect_faces_in_image(frame, sim_threshold=0.4)

        for name, box, center in detections:
            print(f"检测到 {name}; 其边框坐标 {box}; 中心点坐标 {center}")

            if name == "t_0":
                screen_center_x = frame.shape[1] / 2
                center_x = center[0]

                offset_x = center_x - screen_center_x
                if offset_x >= offset_limit:
                    mv.move_right(10, 50)
                elif offset_x <= -offset_limit:
                    mv.move_left(10, 50)
                else:
                    mv.call_servo_control(arm_actions["pre_hit"], 10)
                    time.sleep(2.0)
                    mv.call_servo_control(arm_actions["hit"], 10)
                    time.sleep(2.0)

            else:
                mv.call_servo_control(arm_actions["clamp"], 10)
                time.sleep(2.0)

        if debug:
            image = face_detector.draw_bounding_boxes(frame, detections)
            cv2.imshow('Face', image)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

except KeyboardInterrupt:
    cap.release()
