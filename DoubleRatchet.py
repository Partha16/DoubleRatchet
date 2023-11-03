from utils import *

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from Crypto.Cipher import AES

class DRatch(object):
    #snip
    def __init__(self, init : bool, name : str):
        # generate keys
        self.name = name
        self.init = init
        self.IdentityKey = X25519PrivateKey.generate()
        
        if init:
            self.DHratchet = X25519PrivateKey.generate()
            self.SignedPreKey = X25519PrivateKey.generate()
            self.OnetimePreKey = X25519PrivateKey.generate()
        else:
            self.EphemeralKey = X25519PrivateKey.generate()
            self.DHratchet = None

    
    def x3dh(self, obj):
        if self.init:
            self._x3dh_init(obj)
        else:
            self._x3dh_resp(obj)
    
    def exportPublicKeys(self):
        keys = {}
        keys['IdentityKey'] = self.IdentityKey.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        if self.init:
            keys['SignedPreKey'] = self.SignedPreKey.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
            keys['OnetimePreKey'] = self.OnetimePreKey.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
            keys['PublicKey'] = self.DHratchet.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        else:
            keys['EphemeralKey'] = self.EphemeralKey.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        return keys
    
    def _x3dh_init(self, recv : dict):
        # perform the 4 Diffie Hellman exchanges (X3DH)
        dh1 = self.SignedPreKey.exchange(X25519PublicKey.from_public_bytes(recv['IdentityKey']))
        dh2 = self.IdentityKey.exchange(X25519PublicKey.from_public_bytes(recv['EphemeralKey']))
        dh3 = self.SignedPreKey.exchange(X25519PublicKey.from_public_bytes(recv['EphemeralKey']))
        dh4 = self.OnetimePreKey.exchange(X25519PublicKey.from_public_bytes(recv['EphemeralKey']))
        # the shared key is KDF(DH1||DH2||DH3||DH4)
        self.SharedKey = hkdf(dh1 + dh2 + dh3 + dh4, 32)
        print(f'[{self.name}] : \tShared key:', b64(self.SharedKey))
    
    def _x3dh_resp(self, sendr):
        # perform the 4 Diffie Hellman exchanges (X3DH)
        dh1 = self.IdentityKey.exchange(X25519PublicKey.from_public_bytes(sendr['SignedPreKey']))
        dh2 = self.EphemeralKey.exchange(X25519PublicKey.from_public_bytes(sendr['IdentityKey']))
        dh3 = self.EphemeralKey.exchange(X25519PublicKey.from_public_bytes(sendr['SignedPreKey']))
        dh4 = self.EphemeralKey.exchange(X25519PublicKey.from_public_bytes(sendr['OnetimePreKey']))
        # the shared key is KDF(DH1||DH2||DH3||DH4)
        self.SharedKey = hkdf(dh1 + dh2 + dh3 + dh4, 32)
        print(f'[{self.name}] : \tShared key:', b64(self.SharedKey))
  
    def init_ratchets(self):
        # initialise the root chain with the shared key
        self.root_ratchet = SymmRatchet(self.SharedKey)
        # initialise the sending and recving chains
        self.recv_ratchet = SymmRatchet(self.root_ratchet.next()[0])
        self.send_ratchet = SymmRatchet(self.root_ratchet.next()[0])

    def send(self, msg):
        key, iv = self.send_ratchet.next()
        cipher = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(msg))
        #print(f'[{self.name}]\tSending ciphertext:', b64(cipher))
        # send ciphertext and current DH public key
        #recv.recieve(cipher, self.DHratchet.public_key())
        return (cipher,self.DHratchet.public_key().public_bytes(encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw
        ))

    def recieve(self, cipher, recv_public_key):
        # receive Alice's new public key and use it to perform a DH
        self.dh_ratchet(recv_public_key)
        key, iv = self.recv_ratchet.next()
        # decrypt the message using the new recv ratchet
        msg = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(cipher))
        #print(f'[{self.name}]\tDecrypted message:', msg)
        return msg

    def dh_ratchet(self, recv_public):
        recv_public = X25519PublicKey.from_public_bytes(recv_public)
        # perform a DH ratchet rotation using Alice's public key
        if self.DHratchet is not None:
            dh_recv = self.DHratchet.exchange(recv_public)
            shared_recv = self.root_ratchet.next(dh_recv)[0]
            # use Alice's public and our old private key
            # to get a new recv ratchet
            self.recv_ratchet = SymmRatchet(shared_recv)
            #print(f'[{self.name}]\tRecv ratchet seed:', b64(shared_recv))
        # generate a new key pair and send ratchet
        # our new public key will be sent with the next message to Alice
        self.DHratchet = X25519PrivateKey.generate()
        dh_send = self.DHratchet.exchange(recv_public)
        shared_send = self.root_ratchet.next(dh_send)[0]
        self.send_ratchet = SymmRatchet(shared_send)
        #print(f'[{self.name}]\tSend ratchet seed:', b64(shared_send))