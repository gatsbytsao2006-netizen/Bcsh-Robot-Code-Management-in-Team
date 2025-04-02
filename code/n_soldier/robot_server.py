import socket
import sys
import time

sys.path.append("..")
from uprobot_movement import Movement


def execute_command(command, movement):
    """执行机器人动作并返回状态"""
    actions = {
        'move_forward': '前进',
        'move_backward': '后退',
        'move_left': '左移',
        'move_right': '右移',
        'turn_left': '左转',
        'turn_right': '右转',
        'defense': '防守',
        'attack': '攻击'
    }
    arm = {
        'attack': [2048, 2048, 620, 2670, 600, 2150, 3300, 2200],
        'defense': [2150, 2200, 600, 2200, 2150, 2150, 3300, 2200]
    }

    action = actions.get(command, '未知指令')

    if command == 'move_forward':
        movement.move_forward(30, 500)
        time.sleep(2.0)

    elif command == 'move_backward':
        movement.move_backward(30, 500)
        time.sleep(2.0)

    elif command == 'move_left':
        movement.move_left(30, 500)
        time.sleep(2.0)

    elif command == 'move_right':
        movement.move_right(30, 500)
        time.sleep(2.0)

    elif command == 'turn_left':
        movement.turn_left(30, 500)
        time.sleep(2.0)

    elif command == 'turn_right':
        movement.turn_right(30, 500)
        time.sleep(2.0)

    elif command == 'defense':
        movement.call_servo_control(arm['defense'], 2)
        time.sleep(2.0)

    elif command == 'attack':
        movement.call_servo_control(arm['attack'], 2)
        time.sleep(2.0)

    return f"状态: {action} 完成"


def start_server(host='0.0.0.0', port=6000):

    movement = Movement()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"等待控制端连接在 {host}:{port}...")

        conn, addr = s.accept()
        with conn:
            print(f"控制端 {addr} 已连接")

            while True:
                data = conn.recv(1024).decode('utf-8').strip()

                if not data:
                    continue

                if data.lower() == 'exit':
                    print("程序退出")
                    conn.close()
                    break

                response = execute_command(data.lower(), movement)
                conn.sendall(response.encode('utf-8'))


if __name__ == "__main__":
    start_server()
