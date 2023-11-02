from DoubleRatchet import DRatch

alice = DRatch(False, 'Alice')
bob = DRatch(True, 'Bob')

bob_keys = bob.exportPublicKeys()
alice_keys = alice.exportPublicKeys()
# Alice performs an X3DH while Bob is offline, using his uploaded keys
alice.x3dh(bob_keys)

# Bob comes online and performs an X3DH using Alice's public keys
bob.x3dh(alice_keys)

# Initialize their symmetric ratchets
alice.init_ratchets()
bob.init_ratchets()

# Initialise Alice's sending ratchet with Bob's public key
alice.dh_ratchet(bob.DHratchet.public_key())

# Alice sends Bob a message and her new DH ratchet public key
alice.send(bob, b'Hello Bob!')

# Bob uses that information to sync with Alice and send her a message
bob.send(alice, b'Hello to you too, Alice!')