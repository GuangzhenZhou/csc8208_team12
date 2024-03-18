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
# 如果使用命令行启动，取消下方代码的注释；If starting from the command line, uncomment the code below
# args_dict = vars(args.parse_args())
# 如果喜欢使用PyCharm等IDE进行启动，取消下方代码的注释；If you prefer to start using an IDE such as PyCharm, uncomment the code below
args_dict = {"addr": '127.0.0.1', "port": 3000}


class Server:

    def __init__(self):
        self.clients = []

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((args_dict["addr"], args_dict["port"]))
        self.sock.listen(100)

        # 处理高频消息的部分
        self.last_message_time = {}  # Records the last time each client sent a message
        self.message_count = {}  # Records the number of messages sent by each client within a specified time period
        self.suspicious_users = set()  # Log suspicious users
        self.silenced_users = {} # The key is conn and the value is the timestamp when the ban started.

    def update_user_activity(self, conn, addr):
        current_time = time.time()
        time_threshold = 60  # Behavior analysis within 60 seconds
        message_limit = 10  # Maximum number of messages allowed in 60 seconds

        # If the message is sent for the first time, initialize the record
        if conn not in self.last_message_time:
            self.last_message_time[conn] = current_time
            self.message_count[conn] = 1
        else:
            # Check time difference
            if current_time - self.last_message_time[conn] < time_threshold:
                self.message_count[conn] += 1
                if self.message_count[conn] > message_limit:
                    # Flag user as suspicious and possible action
                    print(f"[Warning] {addr} might be a bot. Silencing for 1 minute.")
                    self.suspicious_users.add(conn)
                    self.silenced_users[conn] = current_time  # Record the time when the ban started
            else:
                # Reset counters and timestamps
                self.message_count[conn] = 1
                self.last_message_time[conn] = current_time

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
        # Send connection confirmation message
        conn.send("Connection established\n".encode('utf-8'))

        while True:
            try:
                msg = conn.recv(4096)
                if msg:
                    current_time = time.time()
                    # Check if user is banned
                    if conn in self.silenced_users and current_time - self.silenced_users[conn] < 60:
                        # The user is in a muted state, send a muting reminder message.
                        conn.send("YOU ARE CURRENTLY BANNED。\n".encode('utf-8'))
                        continue  # Skip broadcasting the message
                    else:
                        # Unlock the mute status if the mute time has expired
                        if conn in self.silenced_users:
                            del self.silenced_users[conn]

                        decoded_msg = msg.decode('utf-8').rstrip('\n')
                        print(f"<{addr[0]}> {decoded_msg}")

                        # Update user activity record
                        self.update_user_activity(conn, addr)

                        # Broadcast messages to other clients
                        self.broadcast(conn, addr, decoded_msg)
                else:
                    # If no message is received, the client may have disconnected
                    if conn in self.clients:
                        self.clients.remove(conn)
                    conn.close()
                    break  # Exit loop

            except Exception as e:
                print(f"Error handling message from {addr}: {e}")
                if conn in self.clients:
                    self.clients.remove(conn)
                conn.close()
                break  # Exit loop

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
    # Close all client connections
    for client in ser.clients:
        try:
            client.close()
        except Exception as e:
            print(f"Error closing client socket: {e}")
    # Close listening socket
    try:
        ser.sock.close()
    except Exception as e:
        print(f"Error closing server socket: {e}")
    print("Server shut down successfully.")
    sys.exit(0)


if __name__ == "__main__":
    ser = Server()
    # Register signal handling function
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    ser.execute()
