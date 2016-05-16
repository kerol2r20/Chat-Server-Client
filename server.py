import socket
import argparse
import queue
import re
import sqlite3
from threading import Thread

online={}
offlineMsg={}

def server(port):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(('',port))
    listener.listen(100)
    print('Listening at',listener.getsockname())
    connection = queue.Queue(maxsize=100)
    while True:
        connection.put(Accept(listener).start())

class Accept(Thread):
    def __init__(self, listener):
        super(Accept, self).__init__()
        self.listener = listener

    def run(self):
        con = sqlite3.connect('user.db')
        db = con.cursor()
        global online
        global offlineMsg
        sock, address = self.listener.accept()
        message = sock.recv(1024).decode('ascii')
        new = re.match('new (.*),(.*)',message)
        if new:
            query = db.execute('SELECT * FROM user WHERE name="{}"'.format(new.group(1)))
            if len(query.fetchall())==0:
                db.execute('INSERT INTO user (name,password) VALUES ("{}","{}")'.format(new.group(1),new.group(2)))
                con.commit()
                print("A new account registe: {}".format(new.group(1)))
                self.user = new.group(1)
                sock.sendall(b'succ')
            else:
                sock.close()
                return
        else:
            new = re.match('(.*),(.*)',message)
            query = db.execute('SELECT * FROM user WHERE name="{}" AND password="{}"'.format(new.group(1),new.group(2)))
            if len(query.fetchall())==1:
                print("{} login".format(new.group(1)))
                self.user = new.group(1)
                online[self.user]=sock
                sock.sendall(b'succ')
            else:
                sock.close()
                return
        query = db.execute('SELECT * FROM offmsg where receiver="{}"'.format(self.user))
        # query = db.execute('SELECT * FROM offmsg where receiver="Mary"')
        msgs = query.fetchall()
        if len(msgs)!=0:
            message = "********   Offline Message   ********\n"
            for msg in msgs:
                message += "<{}  {}> {}\n".format(msg[2], msg[4], msg[3])
            message += "*************************************\n"
            sock.sendall(message.encode('ascii')) 
            db.execute('DELETE FROM offmsg where receiver="{}"'.format(self.user))
            con.commit()
        while True:
            message = sock.recv(1024)
            message = message.decode('ascii')
            send = re.match('send\s+(.*)\s+(.*)',message)
            if send and send.group(1) in online:
                message = '<%s> %s' % (self.user, send.group(2))
                online[send.group(1)].sendall(message.encode('ascii'))
                sock.sendall(message.encode('ascii'))
            else:
                db.execute('INSERT INTO offmsg (sender, receiver,content) VALUES ("{}","{}","{}")'.format(self.user, send.group(1), send.group(2)))
                con.commit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A chat server")
    parser.add_argument('host', help="IP or hostname")
    parser.add_argument('-p', metavar='port', type=int, default=5000, help="TCP bind port (default 5000)")
    args = parser.parse_args()
    address = (args.host, args.p)
    server(args.p)

