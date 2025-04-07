from .application_layer.sensor import Sensor


class UpAPI:
    _instance = None
    __grayscale_record = [False] * 7  # 灰度数据缓存

    def __new__(cls, grayscale_threshold=3060):
        if cls._instance is None:
            cls._instance = super(UpAPI, cls).__new__(cls)

            # 子系统
            cls._instance.__sensor = Sensor()

            # 参数
            cls._instance.__grayscale_threshold = grayscale_threshold  # 灰度阈值

        return cls._instance

    def __adc_grayscale_data(self, data_list):
        """
        灰度阵列模拟量转为数字量

        :param data_list: 模拟量数据
        :return: 数字量数据
        """
        adc_data_list = [data >= self.__grayscale_threshold for data in data_list]
        return adc_data_list

    # ------------------------------ 传感器数据 ------------------------------

    def get_grayscale_data(self):
        """
        获取灰度阵列数字量数据

        :return: 数字量数据
        """
        grayscale = self.__sensor.get_grayscale()
        analog_data = grayscale.get_grayscale_data()

        print(f"灰度传感器模拟量数据: {analog_data}")

        if analog_data is not None:
            digital_data = self.__adc_grayscale_data(analog_data)
            self.__grayscale_record = digital_data
            return digital_data
        else:
            return self.__grayscale_record
