from ..utils import convert_util as tools
from ..hardware_layer.communicator.grayscale_communicator import GrayscaleCommunicator
from .communication.grayscale_data import GrayscaleReadCommand


class Grayscale:
    __addresses = {
        'get_grayscale_data': 0x14,
    }

    def __init__(self, serial_port, threshold=3000):
        self.communicator = GrayscaleCommunicator(serial_port)
        self.threshold = threshold

    def get_grayscale_data(self):
        # 封装灰度传感器读指令
        command = GrayscaleReadCommand(address=self.__addresses['get_grayscale_data'], parameters=[0x0E])

        # 封装灰度传感器读指令
        frame = command.to_bytes()

        # 发送数据帧，并接收响应数据
        data = self.communicator.get_response_data(frame)

        # 解析响应数据
        if data:
            # 分离每一个通道的 16 进制小端数据，并组合成为数组
            data_list = self.__separate_data(data)
            # 将分离后的数组从 16 进制小端，专函成为 10 进制
            data_list = [tools.little_endian_list_convert_to_decimal(data) for data in data_list]
            return data_list
        else:
            return None

    def __separate_data(self, data, byte_count=2):
        """
        将 bytearray 数据分离成 10 进制数组
        :param data: 待分离 bytearray 数据
        :param byte_count: bytearray 数据分割步长
        :return: 10 进制数组
        """
        data_length = len(data)
        if data_length % byte_count != 0:
            raise ValueError("Divisible Error \n data_length: {data_length}, byte_count: {byte_count]}")

        separated_data = [data[i:i + 2] for i in range(0, data_length, byte_count)]
        return separated_data
