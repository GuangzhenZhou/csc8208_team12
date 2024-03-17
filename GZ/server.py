#!/usr/bin/env python3
import base64
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

    def broadcast(self, conn, addr, msg):
        encoded_msg = f"<{addr[0]}> {msg}".encode('utf-8')
        for client in self.clients:
            if client != conn:
                try:
                    client.send(encoded_msg)
                except:
                    client.close()
                    self.clients.remove(client)

    def client_handler(self, conn, addr):
        conn.send("Connection established".encode('utf-8'))
        while True:
            try:
                msg = conn.recv(4096)
                if msg:
                    decoded_msg = msg.decode('utf-8')
                    print(f"<{addr[0]}> {decoded_msg}")
                    self.broadcast(conn,addr, decoded_msg)
                else:
                    self.clients.remove(conn)
            except Exception as e:
                print(f"Error handling message from {addr}: {e}")
                if conn in self.clients:
                    self.clients.remove(conn)
                conn.close()

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
