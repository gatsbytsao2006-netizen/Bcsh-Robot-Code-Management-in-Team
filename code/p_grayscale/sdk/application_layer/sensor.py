from ..hardware_layer.manager.serial_manager import SerialManager
from ..data_layer.grayscale import Grayscale
from .notice.base import NoticeBase


class Sensor(NoticeBase):
    def __init__(self):
        super().__init__()

        # 硬件管理单例
        self.__serials = SerialManager()  # 串口

        # 传感器
        self.__grayscale = Grayscale(serial_port=self.__serials.get_serial_usb())  # 灰度

    def clean_up(self):
        pass

    def get_grayscale(self):
        return self.__grayscale
