from sdk.data_layer.arm import arm_action_factory as arm_action
from sdk.api import UpAPI
from sdk.model import YoloModel
from sdk.logic_layer.cross_planner import CrossLocator
from sdk.logic_layer.pid import PIDController
from sdk.logic_layer.time_meter import TimeMeter
from enum import Enum, auto
import time


class MainState(Enum):
    """一级状态机：主状态（行动状态）"""
    IDLE = auto()
    TRANSITION = auto()
    LOCATION = auto()
    RELOCATION = auto()
    RECOGNITION = auto()
    FINISH = auto()


class TargetState(Enum):
    """一级状态机：目标状态（行动区域）"""
    APRIL_TAG = auto()
    GESTURE = auto()
    YOLO = auto()
    FACE = auto()
    BACK_HOME_1 = auto()  # 回家第一阶段：后退到十字并右转
    BACK_HOME_2 = auto()  # 回家第二阶段：直行遇到第3个十字


class TransitionState(Enum):
    """二级状态机：转场状态"""
    EXIT_CROSS = auto()  # 驶出十字
    MOVE_FORWARD = auto()  # 在白色区域中行驶
    SPAN = auto()  # 旋转


class RelocationState(Enum):
    """二级状态机：重定位状态"""
    LONG = auto()  # 长距离后退，YOLO 和人脸检测区域使用
    SHORT = auto()  # 短距离后退，其余区域使用
    COMPLETE = auto()  # 重定位完成


class RecognitionState(Enum):
    """二级状态机：识别状态"""
    TURN_LEFT = auto()  # 仅有 YOLO 检测之前使用
    PREPARE = auto()
    AIM = auto()
    EXECUTE = auto()


class SpanState(Enum):
    """三级状态机：转场的旋转状态"""
    FORWARD = auto()
    BACKWARD = auto()
    LEFT = auto()
    RIGHT = auto()


class Controller:
    def __init__(self):
        # 参数设置
        self.grayscale_threshold = 800  # 灰度传感器检测阈值 ## 2200->400

        self.speed_follow_line = 18.2  # 巡线前进移动速度 (曲线)
        self.speed_follow_line_straight = 20  # 巡线前进移动速度 (直线, 新增)
        self.speed_move_in_white = 27  # 在白色区域前进移动速度27
        self.speed_hit_position = 30  # 进入退出击打位置的速度
        self.speed_locate_move = 19  # 定位移动速度12
        self.speed_locate_turn = 22  # 定位旋转速度22
        self.speed_spin = 193  # 自旋速度  ##100->50
        self.speed_aim = 8  # 瞄准移动速度

        self.time_init = 600  # 初始化时间，单位毫秒
        self.time_left_turn = 895  # 向左转时间，单位毫秒1600
        self.time_right_turn = 905  # 向右转时间，单位毫秒1650
        self.time_backward_turn = 1825  # 向后转时间，单位毫秒
        self.time_arm_action = 1200  # 手臂做动作时间，单位毫秒
        self.time_hit_position = 270  # 进入退出击打状态的移动时间，单位毫秒
        self.time_back_short = 150  # 重定位短距离后退，单位毫秒
        self.time_back_long = 350  # 重定位长距离后退，单位毫秒
        self.time_white_forward = 650  # 白色区域前进时间，单位毫秒

        # 巡线 PID 参数 (直线/小偏移)
        self.k_p = 30  # 巡线比例参数
        self.k_i = 0.005  # 巡线积分参数
        self.k_d = 50  # 巡线微分参数
        self.april_action_started = False
        self.gesture_action_started = False

        # 巡线 PID 参数 (曲线/大偏移)
        self.k_p_curve = 22
        self.k_i_curve = 0.003
        self.k_d_curve = 120

        # 分段 PID 控制判断阈值，基于转向幅度 (turn_rate)
        self.turn_rate_threshold = 25

        self.target_face = "t_0"  # 人脸识别标签
        self.target_yolo = "tank"  # 车辆识别标签
        self.target_id = 1  # April Tag 识别 ID  （实际是 1 号）
        self.target_number_right = 0  # 手势识别数字，举右手
        self.target_number_both = 5  # 手势识别数字，举右手

        self.target_center_offset = 18  # 目标中心与屏幕中心偏移量，单位像素

        # YOLO 目标参数
        self.yolo_model = YoloModel.VEHICLE

        # 手臂动作
        self.left_arm_actions = {
            "clamp": arm_action.left_arm_clamp(),
            "up": arm_action.left_arm_raise()
        }
        self.right_arm_actions = {
            "clamp": arm_action.right_arm_clamp(),
            "up": arm_action.right_arm_raise(),
            "pre_hit": arm_action.right_arm_prepare_beat(),
            "hit": arm_action.right_arm_beat()
        }

        # 状态机
        self.state_main = MainState.IDLE
        self.state_target = TargetState.APRIL_TAG
        self.state_transition = TransitionState.EXIT_CROSS
        self.state_relocation = RelocationState.COMPLETE
        self.state_recognition = RecognitionState.PREPARE
        self.state_span = SpanState.FORWARD

        # 传感器和执行器
        self.api = UpAPI(yolo_model=self.yolo_model, grayscale_threshold=self.grayscale_threshold)

        # 逻辑处理器
        self.locator = CrossLocator()

        # 直线 PID 控制器
        self.pid_straight = PIDController(k_p=self.k_p, k_i=self.k_i, k_d=self.k_d)
        # 曲线 PID 控制器
        self.pid_curve = PIDController(k_p=self.k_p_curve, k_i=self.k_i_curve, k_d=self.k_d_curve)

        # 计时器
        self.initializer = TimeMeter(self.time_init)  # 初始化
        self.spanner_left = TimeMeter(self.time_left_turn)  # 向左转
        self.spanner_right = TimeMeter(self.time_right_turn)  # 向右转
        self.spanner_backward = TimeMeter(self.time_backward_turn)  # 向后转
        self.timer_arm_action = TimeMeter(self.time_arm_action)  # 手臂做动作
        self.timer_back_short = TimeMeter(self.time_back_short)  # 短距离重定位
        self.timer_back_long = TimeMeter(self.time_back_long)  # 长距离重定位
        self.timer_white_forward = TimeMeter(self.time_white_forward)  # 白色区域前进计时

        # 相机稳定
        self.count_stable = 0  # 相机稳定计数器
        self.count_continuous_stable = 36  # 相机连续稳定阈值

        # 已经定位十字的次数
        self.count_cross_pass = 0  # 十字定位次数计数器

        # 定位旋转超出预计的次数
        self.count_locate_spin_left = 0
        self.count_locate_spin_right = 0
        self.count_max_locate_spin = 50

        # 白色区域前进标志
        self.white_forward_started = False

        # 回家十字计数
        self.home_cross_count = 0

        # 用户确认标志：初始化完成后需用户按回车或输入 y 才继续
        self._confirmed = False

    def run(self):
        while True:
            # 传感器数据
            grayscale_data = self.api.get_grayscale_data()

            # 状态机
            if self.state_main == MainState.IDLE:
                if self.initializer.complete():
                    # 如果尚未确认，则等待用户输入确认（按回车或输入 y）
                    if not self._confirmed:
                        try:
                            # 显示明确提示
                            print("初始化完成。按回车或输入 'y' 并回车以继续程序，输入其他任意键并回车将继续等待。")
                            user_input = input().strip()
                        except Exception:
                            # 在某些运行环境下 input 可能抛异常，视为确认（避免无限阻塞）
                            user_input = ''
                        if user_input.lower() in ('', 'y'):
                            print("确认继续。")
                            self._confirmed = True
                        else:
                            print("未确认，继续等待用户确认...")
                            # 继续下一次循环，保持在 IDLE
                            time.sleep(0.1)
                            continue

                    # 确认过后才进入下一状态
                    print("初始化完成")
                    self.state_main = MainState.TRANSITION
                    self.state_transition = TransitionState.EXIT_CROSS
                else:
                    print("初始化中...")
                    self.__clamp_arms()

            elif self.state_main == MainState.TRANSITION:
                if self.state_transition == TransitionState.EXIT_CROSS:
                    if self.locator.detect_black(grayscale_data):
                        print("检测到黑色")
                        self.api.move_forward(self.speed_move_in_white)
                    else:
                        print("准备进入白色区域前进")
                        self.state_main = MainState.TRANSITION
                        self.state_transition = TransitionState.MOVE_FORWARD

                elif self.state_transition == TransitionState.MOVE_FORWARD:
                    if self.locator.detect_black(grayscale_data):
                        print("检测到黑色，进入定位环节")
                        self.state_main = MainState.LOCATION
                        self.api.stop()
                    else:
                        print("白色区域中前进")
                        self.api.move_forward(self.speed_move_in_white)

                elif self.state_transition == TransitionState.SPAN:
                    if self.state_span == SpanState.FORWARD:
                        print("向前进，准备驶出十字")
                        self.state_main = MainState.TRANSITION
                        self.state_transition = TransitionState.EXIT_CROSS

                    elif self.state_span == SpanState.BACKWARD:
                        if not self.spanner_backward.in_progress:
                            self.spanner_backward.start()
                        if self.spanner_backward.complete():
                            print("向后转完成，准备进入短距离重定位")
                            self.state_main = MainState.RELOCATION
                            self.state_relocation = RelocationState.SHORT
                        else:
                            print("向后转中")
                            self.api.spin_left(self.speed_spin)

                    elif self.state_span == SpanState.LEFT:
                        if not self.spanner_left.in_progress:
                            self.spanner_left.start()
                        if self.spanner_left.complete():
                            print("向左转完成，准备进入短距离重定位")
                            self.state_main = MainState.RELOCATION
                            self.state_relocation = RelocationState.SHORT
                        else:
                            print("向左转中")
                            self.api.spin_left(self.speed_spin)

                    elif self.state_span == SpanState.RIGHT:
                        if not self.spanner_right.in_progress:
                            self.spanner_right.start()
                        if self.spanner_right.complete():
                            # 根据目标状态决定下一步
                            if self.state_target == TargetState.BACK_HOME_1:
                                print("第一次右转完成，准备后退到十字")
                                self.state_main = MainState.RELOCATION
                                self.state_relocation = RelocationState.LONG
                            elif self.state_target == TargetState.BACK_HOME_2:
                                print("第二次右转完成，准备进入白色区域前进")
                                self.state_main = MainState.TRANSITION
                                self.state_transition = TransitionState.MOVE_FORWARD
                            else:
                                # 其他情况的右转
                                if (self.state_target == TargetState.FACE):
                                    print("向右转完成，准备进入长距离重定位")
                                    self.state_main = MainState.RELOCATION
                                    self.state_relocation = RelocationState.LONG
                                elif self.state_target == TargetState.YOLO:
                                    print("向右转完成，准备进入短距离重定位")
                                    self.state_main = MainState.RELOCATION
                                    self.state_relocation = RelocationState.SHORT
                        else:
                            print("向右转中")
                            self.api.spin_right(self.speed_spin)

            elif self.state_main == MainState.LOCATION:
                if self.locator.translate_to_center(grayscale_data):
                    # 中心对齐了
                    if self.locator.reach_target(grayscale_data, False):
                        print("定位成功!!!")
                        self.api.stop()
                        self.__correct_direction()

                        if self.state_relocation == RelocationState.COMPLETE:
                            if self.state_target == TargetState.APRIL_TAG:
                                if self.count_cross_pass < 1:
                                    print("到达 April Tag 识别前的一个十字，准备左转")
                                    self.count_cross_pass += 1
                                    self.state_main = MainState.TRANSITION
                                    self.state_transition = TransitionState.SPAN
                                    self.state_span = SpanState.LEFT
                                else:
                                    print("到达 April Tag 识别十字，准备进入识别程序")
                                    self.count_cross_pass = 0
                                    self.state_main = MainState.RECOGNITION
                                    self.state_recognition = RecognitionState.PREPARE

                            elif self.state_target == TargetState.GESTURE:
                                if self.count_cross_pass < 1:
                                    print("到达手势识别前的一个十字，准备继续前进")
                                    self.count_cross_pass += 1
                                    self.state_main = MainState.TRANSITION
                                    self.state_transition = TransitionState.EXIT_CROSS
                                else:
                                    print("到达手势识别十字，准备进入识别程序")
                                    self.count_cross_pass = 0
                                    self.state_main = MainState.RECOGNITION
                                    self.state_recognition = RecognitionState.PREPARE

                            elif self.state_target == TargetState.YOLO:
                                if self.count_cross_pass < 1:
                                    print("到达 YOLO 识别前的一个十字，准备右转")
                                    self.count_cross_pass += 1
                                    self.state_main = MainState.TRANSITION
                                    self.state_transition = TransitionState.SPAN
                                    self.state_span = SpanState.RIGHT
                                else:
                                    print("到达 YOLO 识别十字，准备先左转，再进入识别程序")
                                    self.count_cross_pass = 0
                                    self.state_main = MainState.RECOGNITION
                                    self.state_recognition = RecognitionState.TURN_LEFT

                            elif self.state_target == TargetState.FACE:
                                print("到达人脸识别十字，进入识别程序")
                                self.state_main = MainState.RECOGNITION
                                self.state_recognition = RecognitionState.PREPARE

                            elif self.state_target == TargetState.BACK_HOME_1:
                                print("后退到十字完成，准备第二次右转")
                                self.state_main = MainState.TRANSITION
                                self.state_transition = TransitionState.SPAN
                                self.state_span = SpanState.RIGHT
                                self.state_target = TargetState.BACK_HOME_2

                            elif self.state_target == TargetState.BACK_HOME_2:
                                self.home_cross_count += 1
                                print(f"到达回家路上的第 {self.home_cross_count} 个十字")
                                if self.home_cross_count >= 3:
                                    print("到达第3个十字，任务完成。")
                                    self.state_main = MainState.FINISH
                                else:
                                    print("继续前进到下一个十字")
                                    self.state_main = MainState.TRANSITION
                                    self.state_transition = TransitionState.EXIT_CROSS
                        else:
                            print("重定位完成，准备向前驶出十字")
                            self.state_relocation = RelocationState.COMPLETE
                            self.state_main = MainState.TRANSITION
                            self.state_transition = TransitionState.EXIT_CROSS
                    else:
                        if self.locator.seeking_left(grayscale_data):
                            print("中心是黑色了，前进左转")
                            self.count_locate_spin_left += 1
                            self.api.spin_left(self.speed_locate_turn)
                        elif self.locator.seeking_right(grayscale_data):
                            self.count_locate_spin_right += 1
                            print("中心是黑色了，前进右转")
                            self.api.spin_right(self.speed_locate_turn)
                        else:
                            print("中心是黑色，继续前进")
                            self.api.move_forward(int(self.speed_locate_move))
                else:
                    # 中心未对齐，但会出现都是 False 的情况，应当先解决次情况
                    if self.locator.move_straight(grayscale_data):
                        print("All False")
                        self.api.move_forward(self.speed_locate_move)
                    else:
                        if self.locator.move_left(grayscale_data):
                            print("中心未检测到黑色，左平移")
                            self.api.move_left(self.speed_locate_move)
                        elif self.locator.move_right(grayscale_data):
                            print("中心未检测到黑色，右平移")
                            self.api.move_right(self.speed_locate_move)
                        else:
                            print("无法判断了")
                            pass

            elif self.state_main == MainState.RELOCATION:
                if self.state_relocation == RelocationState.SHORT:
                    if not self.timer_back_short.in_progress:
                        self.timer_back_short.start()
                    if self.timer_back_short.complete():
                        print("短距离后退完成，准备在白色区域中前进")
                        self.api.stop()
                        self.state_main = MainState.TRANSITION
                        self.state_transition = TransitionState.MOVE_FORWARD
                    else:
                        print("短距离后退中")
                        self.api.move_backward(self.speed_move_in_white)

                elif self.state_relocation == RelocationState.LONG:
                    if not self.timer_back_long.in_progress:
                        self.timer_back_long.start()
                    if self.timer_back_long.complete():
                        print("长距离后退完成，准备定位十字")
                        self.api.stop()
                        self.state_main = MainState.LOCATION
                    else:
                        print("长距离后退中")
                        self.api.move_backward(self.speed_move_in_white)

            elif self.state_main == MainState.RECOGNITION:
                if self.state_recognition == RecognitionState.TURN_LEFT:
                    if not self.spanner_left.in_progress:
                        self.spanner_left.start()
                    if self.spanner_left.complete():
                        print("YOLO 识别前，左转完成")
                        self.state_main = MainState.RECOGNITION
                        self.state_recognition = RecognitionState.PREPARE
                    else:
                        print("YOLO 识别前，左转中")
                        self.api.spin_left(self.speed_spin)

                elif self.state_recognition == RecognitionState.PREPARE:
                    if self.count_stable < self.count_continuous_stable:
                        print("等待相机稳定")
                        self.api.stop()
                        self.count_stable += 1
                        self.__clamp_arms()
                        continue

                    if self.state_target == TargetState.APRIL_TAG:
                        print("演习区域，准备识别 April Tag")
                        # 不在此处启动计时，等真正识别到标签后再启动手臂计时
                        self.april_action_started = False
                        self.state_main = MainState.RECOGNITION
                        self.state_recognition = RecognitionState.EXECUTE

                    elif self.state_target == TargetState.GESTURE:
                        print("演习区域，准备识别手势图像")
                        # 手势动作计时在真正识别到手势后再启动
                        self.timer_arm_action.start()
                        self.state_main = MainState.RECOGNITION
                        self.state_recognition = RecognitionState.EXECUTE

                    elif self.state_target == TargetState.YOLO:
                        print("YOLO 识别区域，预加载图像中")
                        preload_complete = self.api.preload_yolo_pool()
                        if preload_complete:
                            print("预加载图像完成，准备瞄准")
                            self.state_main = MainState.RECOGNITION
                            self.state_recognition = RecognitionState.AIM

                    elif self.state_target == TargetState.FACE:
                        print("人脸识别区域，准备瞄准")
                        self.state_main = MainState.RECOGNITION
                        self.state_recognition = RecognitionState.AIM

                elif self.state_recognition == RecognitionState.AIM:
                    if self.state_target == TargetState.YOLO:
                        print("YOLO 预加载图像完成，准备瞄准")
                        find_target, offset_x = self.api.detect_yolo(label=self.target_yolo)
                        if find_target:
                            self.__aim_target(offset_x)

                    elif self.state_target == TargetState.FACE:
                        print("人脸识别区域，准备瞄准")
                        find_target, offset_x = self.api.detect_face(label=self.target_face)
                        if find_target:
                            self.__aim_target(offset_x)

                elif self.state_recognition == RecognitionState.EXECUTE:
                    if self.state_target == TargetState.APRIL_TAG:
                        find_tag, tag_id, offset = self.api.detect_apriltag()
                        # 如果检测到 tag 且尚未启动动作（计时器未在进行），则开始动作并启动计时
                        if not self.april_action_started:
                            if find_tag:
                                print(f"找到 April Tag：{tag_id}，开始执行手臂动作")
                                self.april_action_started = True
                                self.timer_arm_action.start()
                                self.__do_arm_action(tag_id)
                            else:
                                print("未找到 April Tag，继续等待")
                        else:
                            if self.timer_arm_action.complete():
                                print("April Tag 动作完成")
                                self.__clamp_arms()
                                self.count_stable = 0
                                self.state_main = MainState.TRANSITION
                                self.state_transition = TransitionState.SPAN
                                self.state_span = SpanState.BACKWARD
                                self.state_target = TargetState.GESTURE
                                self.state_relocation = RelocationState.SHORT
                                self.api.close_tag_window()
                                self.april_action_started = False
                            else:
                                print("二维码动作执行中")

                    elif self.state_target == TargetState.GESTURE:
                        find_target, number = self.api.detect_gesture()
                        # 如果检测到手势且动作尚未开始，则开始动作并启动计时
                        if number != 5:
                            number = 0
                        if self.timer_arm_action.complete():
                            print("手势动作完成")
                            self.__clamp_arms()
                            self.state_main = MainState.TRANSITION
                            self.state_transition = TransitionState.SPAN
                            self.state_span = SpanState.BACKWARD
                            self.state_target = TargetState.YOLO
                            self.state_relocation = RelocationState.SHORT
                            self.api.close_gesture_window()
                            self.__do_arm_action(5)
                            time.sleep(self.time_arm_action / 1000)
                            self.__clamp_arms()
                        else:
                            print("做手势动作中")
                            if find_target:
                                print(f"找到手势动作：{number}")
                                self.__do_arm_action(number)

                    elif self.state_target == TargetState.YOLO:
                        print(f"开始击打 YOLO 目标：{self.target_yolo}")
                        self.__hit_actions()
                        self.state_main = MainState.TRANSITION
                        self.state_transition = TransitionState.SPAN
                        self.state_span = SpanState.RIGHT
                        self.state_target = TargetState.FACE
                        self.state_relocation = RelocationState.LONG
                        self.__reset_yolo()

                    elif self.state_target == TargetState.FACE:
                        print(f"开始击打人脸目标：{self.target_face}")
                        self.__hit_actions()
                        # 人脸识别击打完成后：第一次右转 → 后退到十字 → 第二次右转 → 直行 → 遇到第3个十字停下
                        print("人脸识别完成，开始回家流程")
                        self.home_cross_count = 0
                        # 第一次右转
                        self.state_main = MainState.TRANSITION
                        self.state_transition = TransitionState.SPAN
                        self.state_span = SpanState.RIGHT
                        self.state_target = TargetState.BACK_HOME_1  # 第一阶段：后退到十字
                        self.api.close_face_window()

            elif self.state_main == MainState.FINISH:
                print("任务完成")
                self.api.stop()
                break

    def __aim_target(self, offset):
        if offset is not None:
            if offset >= self.target_center_offset:
                self.api.move_right(self.speed_aim)
            elif offset <= -self.target_center_offset:
                self.api.move_left(self.speed_aim)
            else:
                self.api.stop()
                self.state_recognition = RecognitionState.EXECUTE
        else:
            print(f"没有发现目标")
            self.api.stop()

    def __correct_direction(self):
        if self.count_locate_spin_left > self.count_max_locate_spin:
            print("右转矫正方向")
            self.api.spin_right(self.speed_spin, self.time_right_turn)
            time.sleep(self.time_right_turn / 1000)
        elif self.count_locate_spin_right > self.count_max_locate_spin:
            print("左转矫正方向")
            self.api.spin_left(self.speed_spin, self.time_left_turn)
            time.sleep(self.time_left_turn / 1000)
        else:
            print("不需要矫正方向")
        self.count_locate_spin_left = 0
        self.count_locate_spin_right = 0

    def __hit_actions(self):
        # 前进
        self.api.move_forward(speed=self.speed_hit_position, run_time=self.time_hit_position)
        time.sleep(self.time_hit_position / 1000)
        # 击打动作序列
        self.__pre_hit()
        time.sleep(self.time_arm_action / 1000)
        self.__hit()
        time.sleep(self.time_arm_action / 1000)
        self.__clamp_arms()
        # 后退
        self.api.move_backward(speed=self.speed_hit_position, run_time=self.time_hit_position)
        time.sleep(self.time_hit_position / 1000)

    def __do_arm_action(self, number):
        if number == self.target_id:
            # 举左手
            left_action = self.left_arm_actions["up"]
            right_action = self.right_arm_actions["clamp"]
            self.api.execute_arm_action(left_action, right_action)
        elif number == self.target_number_right:
            # 举右手
            left_action = self.left_arm_actions["clamp"]
            right_action = self.right_arm_actions["up"]
            self.api.execute_arm_action(left_action, right_action)
        elif number == self.target_number_both:
            # 举双手放下
            left_action = self.left_arm_actions["up"]
            right_action = self.right_arm_actions["up"]
            self.api.execute_arm_action(left_action, right_action)

    def __clamp_arms(self):
        left_action = self.left_arm_actions["clamp"]
        right_action = self.right_arm_actions["clamp"]
        self.api.execute_arm_action(left_action, right_action)

    def __pre_hit(self):
        left_action = self.left_arm_actions["clamp"]
        right_action = self.right_arm_actions["pre_hit"]
        self.api.execute_arm_action(left_action, right_action)

    def __hit(self):
        left_action = self.left_arm_actions["clamp"]
        right_action = self.right_arm_actions["hit"]
        self.api.execute_arm_action(left_action, right_action)

    def __reset_yolo(self):
        self.api.close_yolo_window()
        self.api.reset_yolo_pool()


if __name__ == '__main__':
    controller = Controller()
    controller.run()