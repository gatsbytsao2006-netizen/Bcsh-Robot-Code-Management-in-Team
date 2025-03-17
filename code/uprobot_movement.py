import time

from up_move.uprobot_Cmd import UPComBotCommand
from up_move.uprobot_serOp import serOp

'''
# _______________move_______________底盘移动控制命令
# (direction, speed, turn_speed, time)
# move_forward(0, 10, 0, 500) 10的速度前进500ms
# move_left(90, 10, 0, 500) 10的速度左平移500ms
# move_right(270, 10, 0, 500) 10的速度右平移500ms
# move_backward(180, 10, 0, 500) 10的速度后退500ms
# turn_left(0, 0, 100, 500) 100的速度左旋500ms
# turn_right(0, 0, -100, 500) 100的速度右旋500ms
# move_and_rotate(10, 100) 10的速度前进的同时，100的速度左旋，需要同时调整速度和方向时使用         
# stop() 停止运动
   

# _______________call_action_______________按照id执行动作
# deal_action(id) id可为0~8,对应9个预先设定好的动作，动作可在动作编辑器中编辑
# call_servo_control(servo_position, run_time) 指定8个舵机的position以及运行时长


# _______________voice_____________
# set_volume(vol)  设置音量，可选0~31
# play_sound(folder, track) 播放指定文件夹中的指定文件，folder为文件夹1~9，track为文件1~999

'''


class Movement:

    isOpen = False

    def __init__(self):
        self.isOpen = True
        self.cmd = UPComBotCommand()
        self.action = serOp()
  
    #向前平移指令，参数为速度，时间
    def move_forward(self, speed=10, times=500):
        if self.isOpen:
            command = self.cmd.Move(0, speed, 0, times)
            self.action.write_serial(command)
            return True
        return False

    #向左平移指令，参数为速度，时间
    def move_left(self, speed=10, times=500):
        if self.isOpen:
            command = self.cmd.Move(90, speed, 0, times)
            self.action.write_serial(command)
            return True
        return False

    #向右平移指令，参数为速度，时间
    def move_right(self, speed=10, times=500):
        if self.isOpen:
            command = self.cmd.Move(270, speed, 0, times)
            self.action.write_serial(command)
            return True
        return False

    #后退指令，参数为速度，时间
    def move_backward(self, speed=10, times=500):
        if self.isOpen:
            command = self.cmd.Move(180, speed, 0, times)
            self.action.write_serial(command)
            return True
        return False

    #左转指令，参数为速度，时间
    def turn_left(self, speed=10, times=500):
        if self.isOpen:
            command = self.cmd.Move(0, 0, speed*10, times)
            self.action.write_serial(command)
            return True
        return False

    #右转指令，参数为速度，时间
    def turn_right(self, speed=10, times=500):
        if self.isOpen:
            command = self.cmd.Move(0, 0, -speed*10, times)
            self.action.write_serial(command)
            return True
        return False

    #同时移动和自旋
    def move_and_rotate(self, move_speed, rotate_speed):
        if self.isOpen:
            command = self.cmd.Move(0, move_speed, rotate_speed, 500)
            self.action.write_serial(command)
            return True
        return False  

    #停止
    def stop(self):
        if self.isOpen:
            command = self.cmd.Move(0, 0, 0, 500)
            self.action.write_serial(command)
            return True
        return False

 
    #按照ID执行动作，可选0~8，分别代表不同的动作
    def deal_action(self, id):
        if self.isOpen:
            command = self.cmd.Do_Action(id)
            self.action.write_serial(command)
            time.sleep(3)
            return True
        return False  

    #设定一组舵机动作,data代表舵机的目标位置和执行速度,22字节
    def call_servo_control(self, servo_position, run_time):
        if self.isOpen:
            command = self.cmd.Servo(servo_position, run_time)
            self.action.write_serial(command)            
            return True
        return False          

    #设置音量
    def set_volume(self, vol):
        data = [0] * 1
        data[0] = vol & 0xFF
        buffer, len = self.cmd.GenerateCmd(0x01, 0x08, 0x01, data)
        self.action.write_serial(buffer)

    #播放音乐
    def play_sound(self, folder, track):
        data = [0] * 2
        data[0] = folder & 0xFF
        data[1] = track & 0xFF
        buffer, len = self.cmd.GenerateCmd(0x01, 0x42, 0x02, data)
        self.action.write_serial(buffer)
    