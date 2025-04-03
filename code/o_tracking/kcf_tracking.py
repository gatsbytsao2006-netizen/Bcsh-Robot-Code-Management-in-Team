import cv2
import sys

sys.path.append("..")
from uprobot_movement import Movement

"""
创建一个 KCF 跟踪器实例
返回:
    tracker (cv2.legacy.TrackerKCF): 一个 KCF 跟踪器实例
"""
def create_kcf_tracker():
    return cv2.legacy.TrackerKCF_create()


"""
使用第一帧和边界框初始化 KCF 跟踪器
参数:
    tracker (cv2.legacy.TrackerKCF): KCF 跟踪器实例
    frame (numpy.ndarray): 包含目标的初始帧
    bbox (tuple): 目标的边界框 (x, y, width, height)
返回:
    bool: 初始化成功返回 True，否则返回 False
"""
def initialize_tracker(tracker, frame, bbox):
    return tracker.init(frame, bbox)


"""
更新 KCF 跟踪器，传入当前帧
参数:
    tracker (cv2.legacy.TrackerKCF): KCF 跟踪器实例
    frame (numpy.ndarray): 当前帧，用于更新跟踪
返回:
    success (bool): 跟踪成功返回 True，否则返回 False
    bbox (tuple): 更新后的边界框 (x, y, width, height)
"""
def update_tracker(tracker, frame):
    success, bbox = tracker.update(frame)
    return success, bbox


"""
跟踪移动
参数:
    movement (Movement): Movement 实例
    frame (numpy.ndarray): 当前帧，用于更新跟踪
    p1 (tuple(int, int)): 目标区域左上角顶点坐标
    p2 (numpy.ndarray): 目标区域右下角顶点坐标
"""
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


# 初始化动作控制
movement = Movement()

# 打开视频或摄像头
cap = cv2.VideoCapture(0)  # 使用摄像头，也可以替换为视频文件路径

# 读取初始帧
ret, frame = cap.read()
if not ret:
    print("无法读取视频")
    cap.release()
    exit()

# 选择初始跟踪对象的区域
cv2.namedWindow("Select ROI")
bbox = cv2.selectROI("Select ROI", frame, fromCenter=False, showCrosshair=False)
cv2.destroyWindow("Select ROI")

# 创建并初始化 KCF 跟踪器
tracker = create_kcf_tracker()
initialize_tracker(tracker, frame, bbox)

# 开始跟踪
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 更新跟踪状态
    success, bbox = update_tracker(tracker, frame)

    if success:
        # 如果跟踪成功，绘制跟踪框
        p1 = (int(bbox[0]), int(bbox[1]))
        p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
        cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)

        follow(movement, frame, p1, p2)
    else:
        # 跟踪失败
        cv2.putText(frame, "Failed", (50, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

    # 显示跟踪结果
    cv2.imshow("KCF", frame)

    # 按 ESC 键退出
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
