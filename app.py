import socket
import threading

def recv():
    while True:
        msgFromServer, _ = UDPClientSocket.recvfrom(bufferSize)
        source, message = msgFromServer.decode("utf-8").split("|")
        if source=='set' and message =="inactive":
            break
        else:
            msg = "[{username}] : {message}".format(**eval(message))
            print("\r"+msg+f"\n[{username}] : ", end="")

t1 = threading.Thread(target = recv)

serverAddressPort   = ("127.0.0.1", 20001)
bufferSize          = 1024

username = input("Enter Username : ")
localPort = int(input("Enter Your Port : "))
destPort = int(input("Enter Destination Port : "))
destinationIP = ("127.0.0.1", destPort)


UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPClientSocket.bind(("127.0.0.1", localPort))
UDPClientSocket.sendto(str.encode("set|active"), serverAddressPort)
bytesAddressPair = UDPClientSocket.recvfrom(bufferSize)
data = bytesAddressPair[0].decode('utf-8')
address = bytesAddressPair[1]
destination,message = data.split("|")

if destination=="set" and message=="active":
    t1.start()
    try:
        while(True):   
            message = input(f'[{username}] : ')
            messageDict = {"username" : username,
                        "message" : message}
            messagewithIP = str(destinationIP)+"|"+str(messageDict)
            bytesToSend = str.encode(messagewithIP)
            UDPClientSocket.sendto(bytesToSend, serverAddressPort)

    except KeyboardInterrupt:
        UDPClientSocket.sendto(str.encode("set|inactive"), serverAddressPort)
        t1.join()
else:
    print('[ERROR] : Server Inactive')