import base64
import typing
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

class CrypotgraphyController:
    def __init__(self) -> None:
        self.__tls_private_key : rsa.RSAPrivateKey = None
        self.__tls_public_key  : rsa.RSAPublicKey = None

    def __generate_tls_keys(self) -> None:
        """Generates public and private keys for websocket TLS encryption."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        public_key = private_key.public_key()

        self.__tls_private_key = private_key
        self.__tls_public_key = public_key

    def serialize_tls_public_key(self) -> str:
        """Returns the server's public key for websocket TLS encryption."""
        key: bytes = self.__tls_public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return base64.b64encode(key).decode("ascii")

    def deserialize_client_tls_public_key(self, public_key: str) -> rsa.RSAPublicKey:
        """Loads a client's public key for the websocket TLS encryption."""
        public_key = base64.b64decode(public_key.encode("ascii"))
        return serialization.load_der_public_key(public_key)

    def generate_server_tls_keys(self) -> None:
        self.__generate_tls_keys()

    def get_server_tls_public_key(self) -> str:
        return self.serialize_tls_public_key()
    

    def encrypt_tls(self, plaintext: str, client_public_key: str) -> str:
        """Encrypts data with client's public key."""
        ciphertext = ""
        chunk_size = 190  # split data into chunks of 190 characters

        for i in range(0, len(plaintext), chunk_size):
            chunk = plaintext[i:i+chunk_size]
            encrypted_chunk = self.encrypt_tls_chunk(chunk, client_public_key)
            ciphertext += base64.b64encode(encrypted_chunk).decode("ascii")

        return ciphertext

    def encrypt_tls_chunk(self, plaintext: str, client_public_key: str) -> str:
        """Encrypts data with client's public key."""
        public_key = self.deserialize_client_tls_public_key(client_public_key)

        ciphertext = public_key.encrypt(
            plaintext.encode("utf-8"),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return ciphertext
    
    def decrypt_tls(self, ciphertext: str) -> str:
        """Decrypts data with server's private key."""
        plaintext = ""
        chunks : typing.List[str] = [chunk+"==" for chunk in ciphertext.split("==") if chunk]
        for chunk in chunks:
            decrypted_chunk = self.decrypt_tls_chunk(chunk)
            plaintext += decrypted_chunk
        return plaintext

    def decrypt_tls_chunk(self, chunk: str) -> str:
        """Decrypts a chunk of data with server's private key."""
        plaintext = self.__tls_private_key.decrypt(
            base64.b64decode(chunk),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plaintext.decode("utf-8")