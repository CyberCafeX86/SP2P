#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from random import randint
from time import sleep

import threading
import socket

GLOBAL_PORT = 50000
GLOBAL_INTERFACE = '0.0.0.0'

CLIENTS_PORT_RANGE = ((50001, 60000)) # Random number between those
clients = list()

class Client:
    def __init__(self, address, connection, global_port):
        self.address = address
        self.global_port = global_port
        self.connection = connection

def handle_client_connection(client):
    while True:
        data = client.connection.recv(1024).decode()

        if data:
            if data == 'PING':
                client.connection.send(b'OK')

                print(f'[C] {client.address} pinged')
            elif data == 'OK': # Kinda messy but works =)
                print(f'[:] {client.address[0]}:{client.global_port} is connected')
            elif '[MSG] ' in data:
                print(f'[MSG] {client.address}: {data.replace('[MSG] ', '')}')
            else:
                print(f'[ALL] {client.address}: {data}')
        else:
            print(f'[!] {client.address} disconnected')
            clients.remove(client)

            break

def send_client_connection(connection, message):
    connection.send(bytes(message, 'utf-8'))

def global_listen():
    global_sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    global_sockfd.bind((GLOBAL_INTERFACE, GLOBAL_PORT))

    print(f'[G] Global port listening: {GLOBAL_INTERFACE}:{GLOBAL_PORT}')
    print('[G] New peers are connectable to you now!')
    print('')

    while True:
        global_sockfd.listen()

        connection, address = global_sockfd.accept()

        with connection:
            print(f'\n[G] Contacting from new peer: {address}')
            
            client_data = connection.recv(16).decode() # Number -> This is the client global port, generated another port for him connect
                                                       # "DISCOVER" -> Organize all clients in a string and send it
                                                       # 192.168.1.1:50005;192.168.1.2:50010;...
                                                       # "PING" -> Answer with "OK"

            if client_data == 'DISCOVER':
                print('[G] Discovery information')

                clients_sent = 0
                response = str()

                for client in clients:
                    response += str(client.address[0])+':'+str(client.global_port)+';'
                    clients_sent += 1

                connection.send(bytes(response, 'utf-8'))

                print(f'[G] {clients_sent} clients sent')

                connection.close()
            elif client_data == 'PING':
                print(f'[G] {address} pinged')
                connection.send(b'OK')

                connection.close()
            else:
                try:
                    client_data = int(client_data)
                
                    stateful_port = randint(CLIENTS_PORT_RANGE[0], CLIENTS_PORT_RANGE[1])

                    stateful_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    stateful_sock.bind((GLOBAL_INTERFACE, stateful_port))

                    connection.send(bytes(str(stateful_port), 'utf-8'))

                    connection.close()

                    stateful_sock.listen()

                    new_connection, new_address = stateful_sock.accept()

                    if new_address[0] != address[0]:
                        new_connection.send(b'IP who made requisition and IP connecting to stateful port aren\'t the same')
                        new_connection.close()
                        continue

                    print(f'[G] New client connected: {new_address}')

                    clients.append(Client(new_address, new_connection, client_data))
                
                    threading.Thread(target=handle_client_connection,args=(clients[-1],)).start()
                except ValueError:
                    connection.send(b'Invalid data')
                    connection.close()

    global_sockfd.close()

def list_peers():
    print('address - port - global port')
    for client in clients:
        print(f'{client.address[0]} - {client.address[1]} - {client.global_port}')

def peer_connect(target, global_port):
    try:
        # Connecting to the global stateless port
        start_sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        start_sockfd.connect((target, global_port))

        start_sockfd.send(bytes(str(GLOBAL_PORT), 'utf-8'))

        server_port = int(start_sockfd.recv(8).decode())

        start_sockfd.close()

        # Connecting to stateful connection
        sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        sleep(0.5) # Wait to open the door

        sockfd.connect((target, server_port))

        clients.append(Client((target, server_port), sockfd, global_port))

        threading.Thread(target=handle_client_connection, args=(clients[-1],)).start()

        print(f'[>] Peer connected sucessfully: {target}:{server_port}')
    except ConnectionRefusedError:
        print(f'[E] Connection refused: {target}')

def peer_discover(target, global_port):
    try:
        sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        sockfd.connect((target, global_port))

        sockfd.send(b'DISCOVER')

        clients = sockfd.recv(1024).decode() # <peer_ip>:<peer_global>;<peer_ip2>:<peer_global2>;...

        sockfd.close()

        clients = clients.split(';')

        print(f'[!] {len(clients)} new nodes discovered to connect...')

        peer_connect(target, global_port)

        for client in clients:
            if client == '':
                break

            client_ip = client.split(':')[0]
            client_port = client.split(':')[1]

            peer_connect(client_ip, int(client_port))
    except ConnectionRefusedError:
        print(f'[E] Connection refused: {target}')

def disconnect_all():
    for client in clients:
        print(f'[!] {client.address} closed connection')
        client.connection.close()
    
def send_all(message):
    for client in clients:
        client.connection.send(bytes(message, 'utf-8'))

def send_msg(target_client, message):
    found = False

    for client in clients:
        if target_client == client.address[0]:
            client.connection.send(bytes(message, 'utf-8'))

            found = True

            break

    if not found:
        print('[E] client not found')

def ping_all():
    # Global test #
    for client in clients:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((client.address[0], client.global_port))
            s.send(b'PING')
            data = s.recv(8).decode()
            s.close()
        
            if data == 'OK':
                print(f'[:] {client.address[0]}:{client.global_port} is avaliable for connection')
        except ConnectionRefusedError:
            pass

    # Connection test #
    for client in clients:
        try:
            client.connection.send(b'PING')
        
            # Appear on the terminal is handled on handle_client_connection
        except Exception as e:
            print(f'[E] {client.address[0]}: {e}')

            if client in clients:
                clients.remove(client)

def cmd_help():
    print('help           - shows this help')
    print('dev_msg        - dev message')
    print('peers          - shows peer connected list')
    print('connect        - connect to a P2P network')
    print('connect_single - connect to only one P2P peer')
    print('disconnect     - disconnects all peers')
    print('all            - sends a message for everyone you\'re connected to')
    print('msg            - sends a message for a specific peer')

def dev_msg():
    print('Hello from dev of this script')
    print('This code is mostly written for fun purposes')
    print('Many things still missing, some ideas if I want to upgrade it on future:')
    print('- Better terminal (colors, organized input/outputs)')
    print('- Switch to JSon on communications')
    print('- Rewrite some things to be more legible')
    print('- Maybe implement argparse')
    print('- Maybe *very maybe* add some cryptography')
    print('- Maybe some web panel like i2pd')
    print('')
    print('Thanks for using it! Don\'t forget to star on Github!')

def main():
    threading.Thread(target=global_listen, daemon=True).start()

    sleep(0.5)

    print('[!] Use "help" command to check available commmands')

    while True:
        inp = str(input('SP2P > '))

        command = inp.split(' ')[0]
        args = inp.split(' ')[1:]
        strargs = inp.lstrip(command + ' ').strip()

        match command:
            case 'help': cmd_help()
            case 'dev_msg': dev_msg()
            case 'all': send_all(strargs)
            case 'peers': list_peers()
            case 'ping': ping_all()
            case 'disconnect': disconnect_all()
            case 'connect':
                if len(args) < 2:
                    print('connect <target ip> <target global port>')

                    continue

                peer_discover(args[0], int(args[1]))
            case 'connect_single':
                if len(args) < 2:
                    print('connect_single <target ip> <target global port>')

                    continue

                peer_connect(args[0], int(args[1]))
            case 'msg':
                if len(args) < 2:
                    print('msg <target ip> <message>')

                    continue

                message_to_send = strargs.replace(args[0], '[MSG]')
                target = args[0]

                send_msg(target, message_to_send)
            case _:
                pass

        print('')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        disconnect_all()
    except EOFError:
        disconnect_all()
    except Exception as e:
        print('[!] An error ocurried!')
        print(f'[!] {e}')
    finally:
        print('\n\n[♥] Thanks for using SP2P. Give a star on github!')

