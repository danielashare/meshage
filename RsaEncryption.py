from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.Cipher import PKCS1_OAEP
import sqlite3


class RsaEncryption:
    def __init__(self, **kwargs):
        generate = kwargs.get('generate')
        length = kwargs.get('length')
        if generate or generate is None:
            random_generator = Random.new().read
            new_key = RSA.generate(length, random_generator)
            self.public_key = new_key.publickey().exportKey("PEM", pkcs=1)
            self.private_key = new_key.exportKey("PEM", pkcs=1)
            conn = sqlite3.connect('meshage.db')
            conn.execute('UPDATE users SET publicKey = "' + self.public_key + '" WHERE userID = 0')
            conn.execute('UPDATE users SET privateKey = "' + self.private_key + '" WHERE userID = 0')
            conn.commit()
            conn.close()
        else:
            conn = sqlite3.connect('meshage.db')
            cur = conn.cursor()
            cur.execute('SELECT publicKey, privateKey FROM users WHERE userID = 0')
            data = cur.fetchone()
            self.public_key = data[0]
            self.private_key = data[1]
            conn.close()

    @staticmethod
    def encrypt(public_key, message):
        public_key = RSA.importKey(public_key)
        cipher = PKCS1_OAEP.new(public_key)
        cipher_text = cipher.encrypt(message)
        return cipher_text

    def decrypt(self, cipher_text):
        private_key = RSA.importKey(self.private_key)
        cipher = PKCS1_OAEP.new(private_key)
        message_decrypted = cipher.decrypt(cipher_text)
        return message_decrypted
