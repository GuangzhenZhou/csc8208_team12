#!/usr/bin/env python3
import time
import socket
import argparse
import concurrent.futures
import signal
import sys

args = argparse.ArgumentParser(description="server")
args.add_argument("addr", action="store", help="ip address")
args.add_argument("port", type=int, action="store", help="port")
# args_dict = vars(args.parse_args())
args_dict = {"addr": '127.0.0.1', "port": 3000}


class Server:

    def __init__(self):
        self.clients = []

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((args_dict["addr"], args_dict["port"]))
        self.sock.listen(100)

        self.last_message_time = {}  # 记录每个客户端最后一次发送消息的时间
        self.message_count = {}  # 记录每个客户端在规定时间内发送的消息数量
        self.suspicious_users = set()  # 记录可疑用户

    def update_user_activity(self, conn, addr):
        current_time = time.time()
        time_threshold = 60  # 60秒内的行为进行分析
        message_limit = 3  # 在60秒内允许的最大消息数

        # 如果是首次发送消息，初始化记录
        if conn not in self.last_message_time:
            self.last_message_time[conn] = current_time
            self.message_count[conn] = 1
        else:
            # 检查时间差
            if current_time - self.last_message_time[conn] < time_threshold:
                self.message_count[conn] += 1
                if self.message_count[conn] > message_limit:
                    # 标记为可疑用户并可能采取行动
                    print(f"[Warning] {addr} might be a bot.")
                    self.suspicious_users.add(conn)
            else:
                # 重置计数器和时间戳
                self.message_count[conn] = 1
                self.last_message_time[conn] = current_time

    def broadcast(self, conn, addr, msg):
        encoded_msg = f"<{addr[0]}> {msg}\n".encode('utf-8')
        for client in self.clients:
            if client != conn:
                try:
                    client.send(encoded_msg)
                except:
                    client.close()
                    self.clients.remove(client)

    def client_handler(self, conn, addr):
        # 发送连接确认消息
        conn.send("Connection established".encode('utf-8'))

        while True:
            try:
                msg = conn.recv(4096)
                if msg:
                    decoded_msg = msg.decode('utf-8')
                    print(f"<{addr[0]}> {decoded_msg}")

                    # 更新用户活动记录
                    self.update_user_activity(conn, addr)

                    # 广播消息给其他客户端
                    self.broadcast(conn, addr, decoded_msg)
                else:
                    # 如果没有接收到消息，可能是客户端已断开连接
                    if conn in self.clients:
                        self.clients.remove(conn)
                    conn.close()
                    break  # 退出循环

            except Exception as e:
                print(f"Error handling message from {addr}: {e}")
                if conn in self.clients:
                    self.clients.remove(conn)
                conn.close()
                break  # 退出循环

    def execute(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            while True:
                conn, addr = self.sock.accept()
                self.clients.append(conn)
                print(f"{addr[0]} connected")
                futures.append(
                    executor.submit(self.client_handler, conn=conn, addr=addr))

def signal_handler(sig, frame):
    print('Shutting down server...')
    # 关闭所有客户端连接
    for client in ser.clients:
        try:
            client.close()
        except Exception as e:
            print(f"Error closing client socket: {e}")
    # 关闭监听socket
    try:
        ser.sock.close()
    except Exception as e:
        print(f"Error closing server socket: {e}")
    print("Server shut down successfully.")
    sys.exit(0)


if __name__ == "__main__":
    ser = Server()
    # 注册信号处理函数
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    ser.execute()
