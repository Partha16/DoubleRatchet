import socket
import threading
import time

msgQueues = {}
sendLoops = {}
activeUsers = {}
keys = {}
localIP     = "127.0.0.1"
localPort   = 20001
bufferSize  = 16384
current_sender = None


UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPServerSocket.bind((localIP, localPort))

print(f"[Server] : UDP server up and listening")


def send(source, destination):
    global current_sender
    requested = False
    while len(msgQueues[(source,destination)]) != 0:   
        message = msgQueues[(source,destination)].pop()
        bytesToSend = str.encode(str(source) +"|"+message)
        while not activeUsers[destination]:
            time.sleep(1)
        if current_sender != source and not requested:
            #request dummy
            UDPServerSocket.sendto(str.encode(f"request-dummy|{source}"),current_sender)
            requested = True
        else:
            UDPServerSocket.sendto(bytesToSend, destination)
            msgQueues[(source,destination)]
            current_sender = destination
            requested = False
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
            i = data.find("|")
            destination = data [:i]
            message = data [i+1:]
            if destination=="set":
                activeUsers[address] = message=="active"
                UDPServerSocket.sendto(*bytesAddressPair)
                print(f"[SERVER] : {address} {message}")
            elif destination=="keys":
                keysdata = eval(message)
                keys[address] = keysdata
                if "EphemeralKey" in keysdata.keys():
                    current_sender = address
                print(f"[SERVER] : ({address} , {keysdata})")
            elif destination=="reqkeys":
                reqaddr = eval(message)
                if reqaddr in keys.keys():
                    UDPServerSocket.sendto(str.encode(str(keys[reqaddr])),address)
                    print(f"[SERVER] ({reqaddr} , {keys[reqaddr]})")
                else:
                    UDPServerSocket.sendto(str.encode('None'),address)

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


