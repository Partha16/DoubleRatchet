import socket
import threading
from DoubleRatchet import DRatch
import pickle
import os
import time
import sys

init = sys.argv[1]=="1"
serverAddressPort   = ("127.0.0.1", 20001)
bufferSize          = 16384

username = input("Enter Username : ")
localPort = int(input("Enter Your Port : "))
destPort = int(input("Enter Destination Port : "))
destinationIP = ("127.0.0.1", destPort)

UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPClientSocket.bind(("127.0.0.1", localPort))
last_message = None

if os.path.exists(f"./certificates/{username}.pickle"):
    with open(f"./certificates/{username}.pickle") as f:
        user = pickle.load(f)
else:
    user = DRatch(init,username)
    user_keys = user.exportPublicKeys()
    UDPClientSocket.sendto(str.encode(f"keys|{str(user_keys)}"), serverAddressPort)
    UDPClientSocket.sendto(str.encode(f"reqkeys|{str(destinationIP)}"), serverAddressPort)
    dataKey = eval(UDPClientSocket.recvfrom(bufferSize)[0])
    while dataKey is None:
        UDPClientSocket.sendto(str.encode(f"reqkeys|{str(destinationIP)}"), serverAddressPort)
        dataKey = eval(UDPClientSocket.recvfrom(bufferSize)[0])
        time.sleep(1)
    user.x3dh(dataKey)
    user.init_ratchets()
    if not init:
        user.dh_ratchet(dataKey['PublicKey'])
        # messageDict = {"username" : username,
        #                "message" : "?:::? Message Recieved ?:::?"}
        # encrypted = str(user.send(str.encode(str(messageDict))))
        # messagewithIP = str(destinationIP)+"|"+str(encrypted)
        # UDPClientSocket.sendto(str.encode(messagewithIP), serverAddressPort)

    # with open(f"./certificates/{username}.pickle","wb") as fp:
    #     pickle.dump(user,fp)
    

def recv():
    global last_message
    while True:
        msgFromServer, _ = UDPClientSocket.recvfrom(bufferSize)
        data  = msgFromServer.decode("utf-8")
        i = data.find("|")
        source = data [:i]
        message = data [i+1:]
        if source=='set' and  message =="inactive":
            break
        if source=='request-dummy':
            messageDict = {"username" : username,
                        "message" : "?:::? Resend Message ?:::?"}
            encrypted = str(user.send(str.encode(str(messageDict))))
            messagewithIP = str(message)+"|"+encrypted
            UDPClientSocket.sendto(str.encode(messagewithIP), serverAddressPort)

        else:
            cipher, key = eval(message)
            decrypted = eval(user.recieve(cipher,key).decode("utf-8"))
            if decrypted['message'] != "?:::? Message Recieved ?:::?":
                msg = f"[{decrypted['username']}] : {decrypted['message']}"
                print("\r"+msg+f"\n[{username}] : ", end="")

            if decrypted['message'] == "?:::? Resend Message ?:::?":
                messageDict = {"username" : username,
                               "message" : last_message}
                encrypted = str(user.send(str.encode(str(messageDict))))
                messagewithIP = str(destinationIP)+"|"+str(encrypted)
                UDPClientSocket.sendto(str.encode(messagewithIP), serverAddressPort)
                


t1 = threading.Thread(target = recv)


UDPClientSocket.sendto(str.encode("set|active"), serverAddressPort)
bytesAddressPair = UDPClientSocket.recvfrom(bufferSize)
data = bytesAddressPair[0].decode('utf-8')
address = bytesAddressPair[1]
i = data.find("|")
destination = data [:i]
message = data [i+1:]

if destination=="set" and message=="active":
    t1.start()
    try:
        while(True):   
            message = input(f'[{username}] : ')
            last_message=message
            messageDict = {"username" : username,
                        "message" : message}
            encrypted = str(user.send(str.encode(str(messageDict))))
            messagewithIP = str(destinationIP)+"|"+str(encrypted)
            UDPClientSocket.sendto(str.encode(messagewithIP), serverAddressPort)

    except KeyboardInterrupt:
        UDPClientSocket.sendto(str.encode("set|inactive"), serverAddressPort)
        t1.join()
else:
    print('[ERROR] : Server Inactive')