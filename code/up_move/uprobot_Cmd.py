
class UPComBotCommand():
    
    #运动命令，角度，速度，自旋速度，时长四个参数
    def Move(self, angle=0, speed=0, turn=0, time=500):
        data = [0]*8
        data[0] = angle&0xFF
        data[1] = (angle>>8)&0xFF
        data[2] = speed&0xFF
        data[3] = (speed>>8)&0xFF
        data[4] = turn&0xFF
        data[5] = (turn>>8)&0xFF
        data[6] = time&0xFF
        data[7] = (time>>8)&0xFF
        buffer, length = self.GenerateCmd(0x08, 0x02, 0x08, data)
        return buffer
    
    #舵机控制命令，8个舵机的位置数组，运行时长
    def Servo(self, servo_position, run_time):
        data = [0]*22
        data[0] = servo_position[0]&0xFF
        data[1] = (servo_position[0]>>8)&0xFF
        data[2] = servo_position[1]&0xFF
        data[3] = (servo_position[1]>>8)&0xFF        
        data[4] = servo_position[2]&0xFF
        data[5] = (servo_position[2]>>8)&0xFF
        data[6] = servo_position[3]&0xFF
        data[7] = (servo_position[3]>>8)&0xFF
        data[8] = 0x00
        data[9] = 0x00
        data[10] = 0x00
        data[11] = 0x00
        data[12] = servo_position[4]&0xFF
        data[13] = (servo_position[4]>>8)&0xFF
        data[14] = servo_position[5]&0xFF
        data[15] = (servo_position[5]>>8)&0xFF        
        data[16] = servo_position[6]&0xFF
        data[17] = (servo_position[6]>>8)&0xFF
        data[18] = servo_position[7]&0xFF
        data[19] = (servo_position[7]>>8)&0xFF
        data[20] = run_time&0xFF
        data[21] = run_time&0xFF        
        buffer, length = self.GenerateCmd(0x07, 0x5F, 0x16, data)
        return buffer                                
        
    #生成下发的命令，1,2字节帧头，3字节设备地址，4字节cmd，5字节指令长度，6-N字节具体的指令数据，最后一字节校验位，为3-N字节求和取反
    def GenerateCmd(self, device, cmd, len, data):
        #帧长度
        buffer = [0]*(len+6)
        #帧头1字节
        buffer[0] = 0xF5
        #帧头2字节
        buffer[1] = 0x5F
        #设备号1字节
        buffer[2] = device & 0xFF
        #设备号加到校验位
        check = buffer[2]
        #指令名1字节
        buffer[3] = cmd & 0xFF
        #指令名加到校验位
        check = check+buffer[3]
        #指令长度1
        buffer[4] = len & 0xFF
        #指令长度加到校验位
        check = check+buffer[4]
        #6到N为具体指令
        for i in range(len):
            buffer[5+i] = data[i]
            check = check+buffer[5+i]
        #校验位取反1位
        buffer[len+5] = (~check) & 0xFF
        return buffer, len+6

    def Do_Action(self, id):
        data = [0] * 1
        data[0] = id & 0xFF
        buffer, length = self.GenerateCmd(0x07, 0x55, 0x01, data)
        print(type(buffer))
        return buffer        

    #校验数据是否满足校验位（3~N位求和取反与最后一位比较）
    def Check_operation(self, data):
        l = len(data)
        check = data[2]
        check = check+data[3]
        check = check+data[4]
        for i in range(data[4]-1):
            check = check+data[5+i]
        print("data calculated:", data[l-1])
        if data[l-1] == (~check) & 0xFF:
            print("OK")
            return True
        else:
            return False
    
