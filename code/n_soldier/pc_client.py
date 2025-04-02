import socket


def show_menu():
    print("\n===== 机器人控制指令 =====")
    print("1: 前进     2: 后退")
    print("3: 左移     4: 右移")
    print("5: 左转     6: 右转")
    print("7: 防守     8: 攻击")
    print("0: 退出")


def send_command(host='192.168.2.33', port=6000):  # 替换为机器人IP
    print("连接设备中...")

    commands = {
        '0': 'exit',
        '1': 'move_forward',
        '2': 'move_backward',
        '3': 'move_left',
        '4': 'move_right',
        '5': 'turn_left',
        '6': 'turn_right',
        '7': 'defense',
        '8': 'attack'
    }

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        print("设备连接成功！")

        while True:
            show_menu()
            choice = input("请输入指令编号: ")

            command = commands.get(choice, 'invalid')

            if command == 'invalid':
                print("无效指令！")
                continue

            s.sendall(command.encode('utf-8'))

            if command == 'exit':
                break

            response = s.recv(1024).decode('utf-8')
            print(f"机器人反馈: {response}")


if __name__ == "__main__":
    send_command()
