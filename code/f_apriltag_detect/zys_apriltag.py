import cv2
import apriltag
import sys
sys.path.append("..")

from uprobot_movement import Movement


class TagDetect:
    def __init__(self):
        
        options = apriltag.DetectorOptions(families='tag36h11')
        
        self.tag_detector = apriltag.Detector(options) 
        
        # 打开摄像头，使用默认摄像头（索引为0）
        self.cap = cv2.VideoCapture(0)
        
        self.movement = Movement()

        self.target_tag_id = 3

        # 设置一个窗口来显示图像  
        self.result_name = "Apritag Detect Image" 
        
        cv2.namedWindow(self.result_name, cv2.WINDOW_NORMAL) 
        
        if not self.cap.isOpened():
            self.isOpen = False
            print("无法打开摄像头,请检查线路连接!!!")
        else:
            self.isOpen = True
            print("成功打开摄像头")

        if(self.isOpen):
            
            while(True):

                ret, frame = self.cap.read()
                
                frame = cv2.resize(frame, (640, 480))
                
                if (ret):
                    result = self.update_frame(frame)
                    
                    cv2.imshow(self.result_name, result)

                key = cv2.waitKey(30) & 0xFF  # 等待1ms，并获取按键信息  
                if key == ord('q'):  # 如果按下'q'键，则退出循环 
                    self.cleanup() 
                    break
        
    #tag检测，输入图像，反馈tag的数组
    def update_frame(self, frame):
        
        result = frame.copy()
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 
        
        apriltag_detect_results = self.tag_detector.detect(gray) 
        
        for tag_result in apriltag_detect_results:
            
            tag_id = tag_result.tag_id
            
            if(tag_id == self.target_tag_id):
                
                top_left, top_right, bottom_right, bottom_left = tag_result.corners
                center_x = (top_left[0] + bottom_right[0]) / 2  
                center_y = (top_left[1] + bottom_right[1]) / 2 
                
                print(center_x, center_y)

                self.draw_rect(result, int(top_left[0]), int(top_left[1]), int(bottom_right[0]-top_left[0]), int(bottom_right[1]-top_left[1]))
                self.draw_cross(result, (int(center_x), int(center_y)), 20)

                #计算tag中心相对于图像中心的像素距离
                offset_x = center_x - frame.shape[1] / 2
                if(offset_x >= 40):
                    self.movement.move_right(20,100)
                elif(offset_x <= -40):
                    self.movement.move_left(20,100)
                else:
                    self.movement.hold()
                    
        return result 

    def cleanup(self):  
        # 关闭OpenCV窗口  
        cv2.destroyAllWindows()  

    #在图像中画十字
    def draw_cross(self, frame, point, size):   
        thickness = 2  # 线条粗度  
        color = (0, 0, 255)  # 红色，BGR格式  
        # 计算十字的四个端点坐标  
        x, y = point
        x = int(x)
        y = int(y)  
        p1 = (x - size, y)  
        p2 = (x + size, y)  
        p3 = (x, y - size)  
        p4 = (x, y + size)  
        # 在图像上画十字  
        cv2.line(frame, p1, p2, color, thickness)  
        cv2.line(frame, p3, p4, color, thickness)

    #在图像中画方块
    def draw_rect(self, frame, x, y, w, h):
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)    
    
    #在图像中画圆
    def draw_circle(self, frame, x, y, radius):
        cv2.circle(frame, (x, y), radius, (255, 0, 0), -1)

if __name__ == '__main__':
    apriltag_detect = TagDetect()
            
