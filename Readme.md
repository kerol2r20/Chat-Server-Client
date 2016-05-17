# Chat Server/Client  
This is a simple implement of chat server and client with python 3.

===
### Server usage
Start the server binding wild and port 5000.
```bash
python3 server.py ''
```

### Client usage
Start the client program
```bash
python3 client.py
```
If you want to create a new acount add prefix "new" to your username  
such as
```sh
new Gugug
```
And then enter your password to login

### Client Command
1. friend list  
List all your friend with there state  
2. friend add/remove [message]  
Add/Remove friend  
3. send [username] [message]  
Send someone message (if the user is not online will leave a offline message to him)  
4. talk [username]  
Invite someone to chat with you  
5. sendfile [username] [filename]  
Send file to someone
