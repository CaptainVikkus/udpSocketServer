import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json

clients_lock = threading.Lock()
connected = 0

clients = {}

def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024)
      print(str(data)[1:]);
      data = json.loads(str(data)[1:]);
      if addr in clients:
         if 'heartbeat' in data: #still connected
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['position']['X'] = data['X']
            clients[addr]['position']['Y'] = data['Y']
            clients[addr]['position']['Z'] = data['Z']
      else:
         if 'connect' in data:
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['position'] = {}
            ## send list of clients to the new client
            clientAddresses = {"cmd": 0, "player": []}
            for c in clients: #add all existing client id
                clientAddresses["player"].append({ 'id' : str(c)})
            m = json.dumps(clientAddresses)
            sock.sendto(bytes(m, 'utf8'), (addr[0], addr[1]))
            ## send new client to all clients
            message = {"cmd": 0,"player": {"id": str(addr)} }
            m = json.dumps(message)
            for c in clients:
                if c != addr:
                    sock.sendto(bytes(m,'utf8'), (c[0],c[1]))

def cleanClients(sock):
   while True:
      for c in list(clients.keys()):
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            print('Dropped Client: ', c)
            message = {"cmd": 2,"player":{"id": str(clients[c])}}
            m = json.dumps(message)
            for c2 in clients:
               sock.sendto(bytes(m,'utf8'), (c2[0],c2[1]))
            clients_lock.acquire()
            del clients[c]
            clients_lock.release()
      time.sleep(1)

def gameLoop(sock):
   while True:
      GameState = {"cmd": 1, "players": []}
      clients_lock.acquire()
      print (clients)
      for c in clients:
         player = {}
         #clients[c]['position'] = {"X": random.random(), "Y": random.random(), "Z": random.random()}
         player['id'] = str(c)
         player['position'] = clients[c]['position']
         GameState['players'].append(player)
      s=json.dumps(GameState)
      print(s)
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      clients_lock.release()
      time.sleep(1/10)

def main():
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,(s,))
   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()
