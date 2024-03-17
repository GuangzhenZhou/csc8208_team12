#!/usr/bin/env python3

import socket
import select
import sys
import argparse

args = argparse.ArgumentParser(description="server")
args.add_argument("addr", action="store", help="ip address")
args.add_argument("port", type=int, action="store", help="port")
# 如果使用命令行启动，取消下方代码的注释；If starting from the command line, uncomment the code below
# args_dict = vars(args.parse_args())
# 如果喜欢使用PyCharm等IDE进行启动，取消下方代码的注释；If you prefer to start using an IDE such as PyCharm, uncomment the code below
args_dict = {"addr": '127.0.0.1', "port": 3000}


class Client:

    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((args_dict["addr"], args_dict["port"]))

    def execute(self):
        while True:
            read_sock, write_sock, err_sock = select.select(
                [sys.stdin, self.server], [], [])
            for sock in read_sock:
                if sock == self.server:
                    msg = sock.recv(4096).decode("utf-8").rstrip('\n')
                    print(msg)
                else:
                    msg = sys.stdin.readline().strip()
                    self.server.send((msg + '\n').encode('utf-8'))
                    sys.stdout.write(f"<You> {msg}\n")
                    sys.stdout.flush()


if __name__ == "__main__":
    client = Client()
    client.execute()
