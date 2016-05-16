import socket
import threading
import queue
import re
from getpass import getpass

queueinput = queue.Queue()

class ServerReply(threading.Thread):
    def __init__(self,user,pw):
        super(ServerReply, self).__init__()
        self.user = user
        self.pw = pw

    def run(self):
        global queueinput
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 5000))
        message = '{},{}'.format(self.user,self.pw)
        sock.sendall(message.encode('ascii'))
        message = sock.recv(1024).decode('ascii')
        if(message=="succ"):
            print("Login Success")
            threading.Thread(target=sendMsg,args=(sock,)).start()
            while True:
                while not queueinput.empty():
                    message = queueinput.get()
                    message = message.encode('ascii')
                    sock.sendall(message)
                    # reply = sock.recv(1024).decode('ascii')
                    # print(reply)
        else:
            print("Login Error")
            sock.close()

def sendMsg(sock):
    while True:
        reply = sock.recv(1024)
        reply = reply.decode('ascii')
        print(reply)

class inputMes(threading.Thread):
    def __init__(self):
        super(inputMes, self).__init__()

    def run(self):
        global queueinput
        while True:
            Mes = input()
            queueinput.put(Mes)

if __name__ == '__main__':
    user = input("username(Registe add prefix 'new'):")
    pw = getpass("password:")
    server = ServerReply(user,pw)
    server.start()
    inputM = inputMes()
    inputM.start()
    server.join()
    inputM.join()

