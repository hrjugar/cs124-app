import socket
from otp import *
from constants import *
from smtplib import *


if __name__ == "__main__":
    secret = None
    s = socket.socket()
    s.bind((socket.gethostname(), PORT))
    s.listen(5)

    while True:
        client_socket, address = s.accept()
        data = client_socket.recv(1024).decode().split("\n")
        instruction = data[0]

        if instruction == Instruction.GET_SECRET:
            secret = data[1]
        elif instruction == Instruction.VERIFY:
            input_code = data[1]
            verified = TOTP(secret).verify(input_code)
            client_socket.send(b'1' if verified else b'')

        client_socket.close()