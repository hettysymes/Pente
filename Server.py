import socket
import threading

def client(username):
    host = socket.gethostname()
    port = 8080

    s = socket.socket()
    s.connect((host, port))

    s.send((username+"-").encode("utf-8"))
    data = s.recv(1024).decode('utf-8')
    print(data)

    print("Waiting for other player...")
    opp = s.recv(1024).decode('utf-8')
    print("Opponent: ", opp)

    if username<opp:
        data = s.recv(1024).decode('utf-8')
        print("Opponent move: ", data)

    while 1:
        move = input("Move: ")
        s.send((username+"-"+move).encode("utf-8"))
        data = s.recv(1024).decode('utf-8')
        print("Opponent move: ", data)

    s.close()

onlineUsers = {}

def server():
    host = socket.gethostname()
    port = 8080

    s = socket.socket()
    s.bind((host, port))

    while 1:
        s.listen(1)
        c, addr = s.accept()
        x = threading.Thread(target=handle_client, args=(c,))
        x.start()

def makeConnection():
    global onlineUsers
    notPlaying = []
    for username, status in onlineUsers.items():
        if status[1] == False: notPlaying.append(username)
    print(notPlaying)
    while len(notPlaying) > 1:
        u1 = notPlaying.pop()
        u2 = notPlaying.pop()
        onlineUsers[u1][1] = u2
        onlineUsers[u2][1] = u1
        onlineUsers[u1][0].send(u2.encode("utf-8"))
        onlineUsers[u2][0].send(u1.encode("utf-8"))

def handle_client(c):
    while True:
        data = c.recv(1024).decode("utf-8")
        if not data:
            break
        username, info = data.split("-")
        global onlineUsers
        if username not in onlineUsers:
            onlineUsers[username] = [c, False]
            msg = "Added as a current online user"
            c.send(msg.encode("utf-8"))
            makeConnection()
        elif onlineUsers[username][1] == False:
            del onlineUsers[username]
            msg = "Removed from current online users"
            c.send(msg.encode("utf-8"))
        else:
            opp = onlineUsers[username][1]
            onlineUsers[opp][0].send(info.encode("utf-8"))
        

inp = input("Client or server (c/s)? ")
if inp == "s":
    server()
else:
    username = input("Username: ")
    client(username)
