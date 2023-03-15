import os
import time
from _thread import *
import socket
from socket import *
import struct
from struct import *
import _thread


list_lock = _thread.allocate_lock()
user_list = {}
room_user_info = {}
port_list = {}
port_host = 2050


def join_procedure(conn_h, room, user_name):
    if room not in room_user_info:
        room_user_info[room] = [user_name]
        conn_h.send(b'\nYou have joined a Newly created Room')
    else:
        for member in room_user_info[room]:
            msg = '\nUser ' + user_name + ' joined room ' + room + '\n' + member + ': '
            send_msg(msg, member)
        room_user_info[room].append(user_name)
        conn_h.send(b'\nYou have joined an Existing Room')

    print(room_user_info)

def chat_procedure(room, user, message):
    msg = '\n' + user + ' - ' + room + ' says: ' + message
    room = room_user_info[room][:]
    room.remove(user)
    for member in room:
        send_msg(msg + '\n' + member + ': ', member)
    return


def list_procedure(conn_h, List):
    List = str(list(List))
    conn_h.send(pack('L', len(List)))
    conn_h.send(bytes(List, 'utf-8'))
    return


def send_msg(msg, member):
    m_socket = get_temp_socket(member, user_list[member])
    try:
        m_socket.send(bytes(msg, 'utf-8'))
    except ConnectionError:
        exception_handle(user_list[member])
    if msg.split(' ')[0] == 'secure-msg':
        return m_socket

    m_socket.close()
    return



def exit_procedure(room, user_name):
    room_user_info[room].remove(user_name)
    if len(room_user_info[room]) == 0:
        del room_user_info[room]
    else:
        for member in room_user_info[room]:
            msg = '\nUser ' + user_name + ' left room ' + room + '\n' + member + ': '
            send_msg(msg, member)
    return




def get_temp_socket(member, temp_port):
    sock = socket()
    try:
        sock.connect((gethostname(), temp_port))
    except ConnectionError:
        exception_handle(temp_port)
    return sock




def quit_procedure(conn_h, user_name):
    conn_h.close()
    time.sleep(2)
    del_list = []
    for room_members in room_user_info.values():
        if user_name in room_members:
            room_members.remove(user_name)
    if user_name in user_list:
        del user_list[user_name]
    for user in user_list.keys():
        msg = '\nUser ' + user_name + ' Left IRC Server\n' + user + ': '
        send_msg(msg, user)
    for room, member_list in room_user_info.items():
        if len(member_list) == 0:
            del_list.append(room)
    for room in del_list:
        del room_user_info[room]
    return





def exception_handle(port_message):
    del_list = []
    if port_message in port_list:
        user_name = port_list[port_message]
        del port_list[port_message]
    else:
        return
    for room_members in room_user_info.values():
        if user_name in room_members:
            room_members.remove(user_name)
    if user_name in user_list:
        del user_list[user_name]
    for user in user_list.keys():
        msg = '\nUser ' + user_name + ' Left the IRC Server\n' + user + ': '
        send_msg(msg, user)
    for room, member_list in room_user_info.items():
        if len(member_list) == 0:
            del_list.append(room)
    for room in del_list:
        del room_user_info[room]
    return


def c_handler(conn_h, port_message):
    user_name = port_list[port_message]
    while True:
        try:
            argument = conn_h.recv(128).decode('ascii')
            argument = argument.split(' ')
        except ConnectionError:
            exception_handle(port_message)
            _thread.exit()
        else:
            functionality = argument[0]

        if functionality == 'join-room':
            join_procedure(conn_h, argument[1], user_name)

        elif functionality == 'chat-room':
            try:
                message = conn_h.recv(448).decode('ascii')
            except ConnectionError:
                exception_handle(port_message)
                _thread.exit()
            else:
                chat_procedure(argument[1], user_name, message)

        elif functionality == 'pvt-msg':
            try:
                message = conn_h.recv(448).decode('ascii')
            except ConnectionError:
                exception_handle(port_message)
                _thread.exit()
            else:
                member = argument[1]
                if member not in user_list:
                    msg = '\nIRC_User_Error1: Username ' + member + ' not found\n' + user_name + ': '
                    send_msg(msg, user_name)
                else:
                    msg = '\n' + user_name + ' says: ' + message + '\n' + user_name + ':'
                    send_msg(msg, argument[1])


        elif functionality == 'list':
            if argument[1] == 'rooms':
                if len(room_user_info) == 0:
                    msg = '\nNo rooms to display\n'
                    send_msg(msg, user_name)
                list_procedure(conn_h, room_user_info.keys())
            elif argument[1] == 'users':
                list_procedure(conn_h, user_list.keys())
            elif argument[1] == 'members':
                if argument[2] not in room_user_info:
                    msg = '\nIrcArgumentError3: Room ' + argument[2] + ' not found\n' + argument[-1] + ': '
                    send_msg(msg, user_name)
                else:
                    list_procedure(conn_h, room_user_info[argument[2]])
                    
        elif functionality == 'broadcast-msg':
            msg = user_name + ' says: ' + conn_h.recv(448).decode('ascii')
            for user in user_list.keys():
                if user != user_name:
                    send_msg(msg + '\n' + user + ': ', user)

        elif functionality == 'exit-room':
            exit_procedure(argument[1], user_name)
                    
        elif functionality == 'quit-irc':
            send_msg('\n Quiting out of the IRC Server\nHope you had fun Enjoying our IRC services!', user_name)
            quit_procedure(conn_h, user_name)
            break
    return

def start(h_socket, port_host):
    conn_h, addr_h = h_socket.accept()
    conn_h.send(b'\nWelcome to The Internet Relay Chat BY: MOUNISHA, GANESH, HANESH')
    conn_h.send(b'\nENJOY THE IRC SERVICES')
    u_status = 'unregistered'
    global port_message
    while u_status == 'unregistered':
        try:
            reg_user = conn_h.recv(32).decode('ascii')
        except ConnectionError:
            _thread.exit()
        else:
            [user_stat, u_name] = reg_user.split(' ')
            if user_stat == 'register':
                list_lock.acquire()
                if u_name not in user_list:
                    user_list[u_name] = port_message
                    list_lock.release()
                    port_list[port_message] = u_name
                    u_status = 'registered'
                    conn_h.send(bytes(u_status, 'utf-8'))
                    conn_h.send(b'\nYou Have Been Enrolled successfully!!')
                else:
                    list_lock.release()
                    conn_h.send(bytes(u_status, 'utf-8'))
                    conn_h.send(b'\nRegistration_Error: This Username is Already in use.\nPlease Enter  a Different UserName')
            elif user_stat != 'register':
                conn_h.send(b'\n Please Enter an UserName to Continue')
        print(user_list)
        c_handler(conn_h, port_message)

s_socket = socket()#Creating a socket object
s_socket.bind((gethostname(), 1234)) #giving scoket specific network interface and portname
s_socket.listen() # making the socket to accept the connections
print('\nThe IRC Server is Active and Listening:..... ')
while True:
    conn, addr = s_socket.accept() #representing the connection and a tuple holding the address
    conn.send(pack('L', port_host))#L repesents Long Interger Type.
    port_message = port_host + 1 #port number for message handling
    h_socket = socket()
    h_socket.bind((gethostname(), port_host))
    h_socket.listen()
    start_new_thread(start, (h_socket, port_host,))
    port_host += 5
    
