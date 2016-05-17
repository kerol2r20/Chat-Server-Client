import socket
import argparse
import queue
import re
import sqlite3
from threading import Thread

online={}
sendfileSignal={}
filebuffer={}

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
        global sendfileSignal
        global filebuffer
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
                message += "<{}  {}> {}\n".format(msg[1], msg[4], msg[3])
            message += "*************************************\n"
            sock.sendall(message.encode('ascii')) 
            db.execute('DELETE FROM offmsg where receiver="{}"'.format(self.user))
            con.commit()
        while True:
            message = sock.recv(1024)
            message = message.decode('ascii')
            send = re.match('send\s+(.*)\s+(.*)', message)
            if send:
                if send.group(1) in online:
                    message = '<%s> %s' % (self.user, send.group(2))
                    online[send.group(1)].sendall(message.encode('ascii'))
                    sock.sendall(message.encode('ascii'))
                else:
                    db.execute('INSERT INTO offmsg (sender, receiver,content) VALUES ("{}","{}","{}")'.format(self.user, send.group(1), send.group(2)))
                    con.commit()
            logout = re.match('logout', message)
            if logout:
                online.pop(self.user)
                sock.sendall(b'logout')
                sock.close()
                return
            sendfile = re.match('sendfile\s+(.*)\s+(.*)\s(.*)', message)
            if sendfile:
                target = sendfile.group(1)
                filename = sendfile.group(2)
                filesize = sendfile.group(3)
                message = "sendfile {},{},{}".format(self.user,filename,filesize)
                online[target].sendall(message.encode('ascii'))
                while True:
                    if self.user in sendfileSignal:
                        if sendfileSignal[self.user]=='Accept':
                            sendfileSignal.pop(self.user)
                            message = "SendfileACK Accept"
                            sock.sendall(message.encode('ascii'))
                            filebuffer[target]=sock.recv(int(filesize))
                            break
                        else:
                            sendfileSignal.pop(self.user)
                            message = "SendfileACK Reject"
                            sock.sendall(message.encode('ascii'))
                            break

            sendAccept = re.match('sendfileAccept (.*) (.*)', message)
            if sendAccept:               
                sendfileSignal[sendAccept.group(1)]='Accept'
                filesize=sendAccept.group(2)
                while True:
                    if self.user in filebuffer:
                        sock.sendall(filebuffer[self.user])
                        filebuffer.pop(self.user)
                        break
            sendReject = re.match('sendfileReject (.*) (.*)', message)
            if sendReject:
                sendfileSignal[sendReject.group(1)]='Reject'
            if message=='friendlist':
                message = "******   Your Friend List   ******\n"
                query = db.execute('SELECT * FROM friend WHERE user="{}"'.format(self.user))
                rows = query.fetchall()
                if len(rows)!=0:
                    for row in rows:
                        if row[2] in online:
                            message+="{} online\n".format(row[2])
                        else:
                            message+="{} offline\n".format(row[2])
                message+="**********************************\n"
                sock.sendall(message.encode('ascii'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A chat server")
    parser.add_argument('host', help="IP or hostname")
    parser.add_argument('-p', metavar='port', type=int, default=5000, help="TCP bind port (default 5000)")
    args = parser.parse_args()
    address = (args.host, args.p)
    server(args.p)

