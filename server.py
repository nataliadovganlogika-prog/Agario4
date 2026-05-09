import socket
from threading import Thread, Lock
from math import hypot

HOST = "localhost"
PORT = 8080

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = {}
players = {}
player_id = 1
lock = Lock()

def serialize():
    with lock:
        return "|".join([
            f"{pid}, {p['x']}, {p['y']}, {p['r']}, {p['name']}"
            for pid, p in players.items()
        ])

def handle_client(conn, pid):
    try:
        name = conn.recv(1024).decode().strip()
        if not name:
            name = f"Player{pid}"

        with lock:
            players[pid]['name'] = name

        conn.send(f"{pid},0,0,20\n".encode())

        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break

            try:

                _, x, y, r = map(int, data.split(','))

                with lock:
                    if pid in players:
                        players[pid]['x'] = x
                        players[pid]['y'] = y
                        players[pid]['r'] = r

                check_collisions()
            except:
                pass
    finally:
        with lock:
            players.pop(pid, None)
            clients.pop(pid, None)
        conn.close()

def check_collisions():
    remove = []

    with lock:
        ids = list(players.keys())

        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):

               p1 = players[ids[i]]
               p2 = players[ids[j]]

               dist = hypot(p1['x'] - p2['x'], p1['y'] - p2['y'])

               if dist <= p1['r'] + p2['r']:
                   if p1['r'] > p2['r'] * 1.1:
                       p1['r'] += int(p2['r'] * 0.5)
                       clients[ids[j]].send("LOSE\n".encode())
                       remove.append(ids[j])

                   elif p2['r'] > p1['r'] * 1.1:
                       p2['r'] += int(p1['r'] * 0.5)
                       clients[ids[i]].send("LOSE\n".encode())
                       remove.append(ids[i])

        for pid in remove:
            players.pop(pid, None)
            if pid in clients:
                clients[pid].close()
                clients.pop(pid, None)

def broadcast():
    while True:
        data = serialize()
        with lock:
            for c in list(clients.values()):
                try:
                    c.send((data + "\n").encode())
                except:
                    pass

def accept():
    global player_id

    while True:
        conn, _ = server.accept()

        with lock:
            pid = player_id
            player_id += 1

            players[pid] = {'x': 0, 'y': 0, 'r': 20, 'name': f"Player{pid}"}
            clients[pid] = conn

        Thread(target=handle_client, args=(conn, pid), daemon=True).start()

print("Server started...")
Thread(target=broadcast, daemon=True).start()
accept()