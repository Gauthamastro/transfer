import socket
s= socket.socket()
port = 10000
s.connect((server_ip,port))
s.send(tx_bytes)
