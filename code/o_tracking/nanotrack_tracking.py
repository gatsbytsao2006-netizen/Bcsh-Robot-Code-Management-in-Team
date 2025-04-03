import os
import time
import cv2
import numpy as np
import sys

# 设置窗口尺寸和名称
WINDOW_W = 640
WINDOW_H = 480
WINDOW_NAME = "Project J: Object Tracking"

# 将当前目录添加到系统路径，以便导入本地模块
sys.path.append(os.getcwd())
from core.config import cfg
from models.rknnlite_rk3588_tracker import NnoTracker_RKNNLite

sys.path.append("..")
from uprobot_movement import Movement

# 用于管理初始选择区域和跟踪状态的变量
init_rect = []
selecting = False
tracker_initialized = False


# 鼠标事件回调函数，用于选择目标跟踪区域
def on_mouse(event, x, y, flags, param):
    global init_rect, selecting, tracker_initialized
    if event == cv2.EVENT_LBUTTONDOWN:
        # 开始选择区域
        init_rect = [(x, y)]
        selecting = True
    elif event == cv2.EVENT_MOUSEMOVE and selecting:
        # 拖动时更新选择矩形
        if len(init_rect) == 1:
            init_rect.append((x, y))
        else:
            init_rect[1] = (x, y)
    elif event == cv2.EVENT_LBUTTONUP:
        # 完成选择
        init_rect[1] = (x, y)
        selecting = False
        tracker_initialized = False


# 移动跟踪
def follow(movement, frame, p1, p2):
    screen_center_x = frame.shape[1] / 2
    target_center_x = p2[0] - p1[0]

    offset = screen_center_x - target_center_x
    if offset > 40:
        movement.move_and_rotate(30, -50)
    elif offset < -40:
        movement.move_and_rotate(30, 50)
    else:
        movement.move_forward(30)


# 主程序入口
def main():
    global tracker_initialized, init_rect

    # 初始化运动控制
    movement = Movement()

    # 加载配置文件
    cfg.merge_from_file('./models/config/config.yaml')

    # 加载跟踪器权重文件
    Tback_weight = './weights/track_backbone_T.rknn'
    Xback_weight = './weights/track_backbone_X.rknn'
    Head_weight = './weights/head.rknn'

    # 初始化跟踪器
    tracker = NnoTracker_RKNNLite(Tback_weight, Xback_weight, Head_weight)
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, WINDOW_W, WINDOW_H)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse)

    # 打开摄像头
    cap = cv2.VideoCapture(0)
    for i in range(5):  # 预读几帧以确保摄像头稳定
        cap.read()

    while True:
        # 读取当前帧
        ret, frame = cap.read()
        if not ret:
            break

        # 如果已选择区域且尚未初始化跟踪器
        if len(init_rect) == 2 and not selecting and not tracker_initialized:
            x1, y1 = init_rect[0]
            x2, y2 = init_rect[1]
            init_rect = [x1, y1, x2 - x1, y2 - y1]
            tracker.init(frame, init_rect)
            tracker_initialized = True
            init_rect = []

        # 如果跟踪器已初始化，进行目标跟踪
        if tracker_initialized:
            t1 = time.time()
            outputs = tracker.track(frame)  # 跟踪对象
            fps = 1. / (time.time() - t1)  # 计算帧率

            # 显示跟踪结果
            if 'polygon' in outputs:
                # 显示多边形掩膜
                polygon = np.array(outputs['polygon']).astype(np.int32)
                cv2.polylines(frame, [polygon.reshape((-1, 1, 2))], True, (0, 255, 0), 3)
                mask = (outputs['mask'] > cfg.TRACK.MASK_THERSHOLD).astype(np.uint8) * 255
                mask = np.stack([mask, mask * 255, mask]).transpose(1, 2, 0)
                frame = cv2.addWeighted(frame, 0.77, mask, 0.23, -1)
            else:
                # 显示边界框
                bbox = list(map(int, outputs['bbox']))
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[0] + bbox[2], bbox[1] + bbox[3]), (0, 255, 0), 3)

            # 显示帧率信息
            fps_text = f"FPS: {fps:.2f}"
            cv2.putText(frame, fps_text, (frame.shape[1] - 150, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # 显示选择框并跟踪
        if selecting and len(init_rect) == 2:
            x1, y1 = init_rect[0]
            x2, y2 = init_rect[1]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

            follow(movement, frame, (x1, y1), (x2, y2))

        # 显示窗口
        cv2.imshow(WINDOW_NAME, frame)
        key = cv2.waitKey(30) & 0xFF
        if key == ord("q"):  # 按下“q”键退出
            break

    # 释放资源
    cap.release()
    tracker.release()
    cv2.destroyAllWindows()


# 程序入口
if __name__ == '__main__':
    main()
