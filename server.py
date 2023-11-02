import socket
import threading
import time

msgQueues = {}
sendLoops = {}
activeUsers = {}

localIP     = "127.0.0.1"
localPort   = 20001
bufferSize  = 1024



UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPServerSocket.bind((localIP, localPort))

print(f"UDP to {localIP} server up and listening")


def send(source, destination):
    while len(msgQueues[(source,destination)]) != 0:   
        message = msgQueues[(source,destination)].pop()
        bytesToSend = str.encode(str(source) +"|"+message)
        while not activeUsers[destination]:
            time.sleep(1)
        UDPServerSocket.sendto(bytesToSend, destination)
        print(f"[SERVER] SOURCE : {source}, DESTINATION : {destination}, MSG : {message}")
        
       

def activateSenderLoop(address, destination):
    if (address,destination) not in sendLoops.keys():
        t1 = threading.Thread(target=send, args=(address, destination)) 
        sendLoops[(address,destination)] = t1
        t1.start()
    else:
        if not sendLoops[(address,destination)].is_alive():
            t1 = threading.Thread(target=send, args=(address, destination)) 
            sendLoops[(address,destination)] = t1
            t1.start()
        

try:
    while(True):
            bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
            data = bytesAddressPair[0].decode('utf-8')
            address = bytesAddressPair[1]
            destination,message = data.split("|")
            if destination=="set":
                activeUsers[address] = message=="active"
                UDPServerSocket.sendto(*bytesAddressPair)
                print(f"[SERVER] : {address} {message}")
            else:
                destination = eval(destination)
                if destination not in activeUsers.keys():
                    activeUsers[destination] = False
                if (address,destination) in msgQueues.keys():
                    msgQueues[(address,destination)].append(message)
                else:
                    msgQueues[(address,destination)] = [message]
                activateSenderLoop(address,destination)

except KeyboardInterrupt:
    for t in sendLoops.values():
        t.join()


