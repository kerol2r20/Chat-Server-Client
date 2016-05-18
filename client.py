import socket
import threading
import queue
import re
import os
from getpass import getpass

queueinput = queue.Queue()
prefix = ""
sendfileRequest = {}

def helpinfo():
	print("************   Help   ************")
	print("1. send <msg> <username>: Send message to target. If taget is not online now, the message will save to offline buffer.")
	print("2. chat <username>: Invite someone chat with you.")
	print("3. leave: Leave chatroom.")
	print("4. friend list: List all your friend and show you their status.")
	print("5. friend <add/remove> <username>: Add/remove someone from your friend list.")
	print("6. sendfile <user> <filename>: Send someone file.")
	print("7. logout: Log out from chat server.")
	print("**********************************")

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
            helpinfo()
            threading.Thread(target=RecvMsg,args=(sock,)).start()
            while True:
                while not queueinput.empty():
                    message = queueinput.get()
                    if message == "help":
                    	helpinfo()
                    	continue
                    file = re.match('sendfile\s+(.*)\s(.*)', message)
                    if file:
                        if os.path.isfile(file.group(2)):
                            size = os.stat(file.group(2)).st_size
                            # binary = open(file.group(2),'rb')
                            message = "sendfile {} {} {}".format(file.group(1),file.group(2),str(size))
                            sock.sendall(message.encode('ascii'))
                            while 'Ack' not in sendfileRequest:
                                pass
                            if sendfileRequest['Ack']=='Accept':
                                print("We can start transfer file")
                                sendfileRequest.pop('Ack')
                                binary = open(file.group(2),'rb')
                                print("Load file to buffer...")
                                buff = binary.read()
                                sock.sendall(buff)
                                print("Upload complete")
                            else:
                                print("We can't send file  QQ")
                                sendfileRequest.pop('Ack')
                        else:
                            print("File is not exist")
                    else:
                        # Accept send file
                        global prefix
                        sendfileACK = re.match("sendfileACK (.*) (.*)",prefix)
                        if sendfileACK:
                            if message=='y':
                                message = "sendfileAccept {} {}".format(sendfileACK.group(1),sendfileACK.group(2))
                            else:
                                message = "sendfileReject {} {}".format(sendfileACK.group(1),sendfileACK.group(2))
                            prefix = ""
                        chatRequest = re.match("chatRequest (.*)",prefix)
                        if chatRequest:
                        	if message=='y':
                        		message = "chatAccept {}".format(chatRequest.group(1))
                        	else:
                        		message = "chatReject {}".format(chatRequest.group(1))
                        	prefix = ""
                        message = message.encode('ascii')
                        sock.sendall(message)
        else:
            print("Login error Please try again")
            sock.close()

def RecvMsg(sock):
    global sendfileRequest
    global prefix
    while True:
        reply = sock.recv(1024)
        reply = reply.decode('ascii')
        sendfile = re.match("sendfile (.*),(.*),(.*)",reply)
        if sendfile:
            print("{} will send you {} with {} byte. Would you want it (y/n)?".format(sendfile.group(1),sendfile.group(2),sendfile.group(3)))
            prefix="sendfileACK {} {}".format(sendfile.group(1),sendfile.group(3))
            buff = sock.recv(int(sendfile.group(3)))
            f = open(sendfile.group(2),'wb')
            f.write(buff)
            f.close()
        if reply=='logout':
            print('Disconnect to chat server. Socket close...')
            sock.close()
            return
        if reply=='SendfileACK Accept':
            sendfileRequest['Ack']='Accept'
        if reply=='SendfileACK Reject':
            sendfileRequest['Ack']='Reject'  
        chatRequest = re.match("chatRequest (.+)",reply)
        if chatRequest:
        	target = chatRequest.group(1)
        	print("{} want to chat with you. World you want to (y/n)?".format(target))
        	prefix="chatRequest {}".format(target)
        else:
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
