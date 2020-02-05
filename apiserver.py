from flask import Flask,request
import socket
app = Flask(__name__)
ip = input("Enter Node IP:")
serversockin = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serversockin.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

@app.route("/gateway",methods=['POST'])
def pebblegateway():
    serversockin.sendto(request.data,(ip,2020))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")