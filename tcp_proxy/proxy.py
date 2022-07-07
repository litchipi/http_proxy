#!/usr/bin/env python3

import sys
import socket
import threading

from scapy.all import IP, TCP

class HttpProxy:
    def __init__(self, handler, local_port, remote_port=80):
        self.handler = handler

        self.local_port = local_port
        # TODO  Allow to add custom port to remote port
        self.remote_port = remote_port

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server.bind(("localhost", local_port))
        except Exception as e:
            print(f"Error while creating proxy: {e}")
            sys.exit(1)

    def create_request(self, header, payload, ignored_keys=[]):
        IGNORED_HEADER_KEYS = ["method", "path", "protocol"] + ignored_keys
        return "{} {} {}".format(header["method"], header["path"], header["protocol"]).encode() + \
            b'\r\n'.join([b''] + ["{}: {}".format(key, val).encode()
                for key, val in header.items() if key not in IGNORED_HEADER_KEYS]) + \
            b'\r\n\r\n' + payload

    def create_response(self, user_header, payload, ignored_keys=[]):
        header = {"code": 200, "message":"OK", "protocol":"HTTP1/1"}
        header.update(user_header)
        IGNORED_HEADER_KEYS = ["code", "message", "protocol"] + ignored_keys
        return "{} {} {}".format(header["protocol"], header["code"], header["message"]).encode() + \
            b'\r\n'.join([b''] + ["{}: {}".format(key, val).encode()
                for key, val in header.items() if key not in IGNORED_HEADER_KEYS]) + \
            b'\r\n\r\n' + payload

    def get_header(self, buffer, req=True):
        try:
            header_raw = buffer.split(b'\r\n\r\n')[0].decode()
            payload = b'\r\n\r\n'.join(buffer.split(b'\r\n\r\n')[1:])
        except:
            print("Error while getting the header")
            print(buffer)
            sys.exit(1)
        header = dict()
        first = True
        for line in header_raw.split("\r\n"):
            if first:
                if req:
                    header["method"] = line.split(" ")[0]
                    header["path"] = line.split(" ")[1]
                    header["protocol"] = line.split(" ")[2]
                    first = False
                else:
                    try:
                        header["protocol"] = line.split(" ")[0]
                        header["code"] = line.split(" ")[1]
                        header["message"] = line.split(" ")[2]
                    except:
                        print(line)
                    first = False
            elif ": " in line:
                header[line.split(": ")[0]] = line.split(": ")[1]
            else:
                raise Exception("Unexpected error while getting header from HTTP packet")
        return (header, payload)

    # Unused
    def load_req(self, buffer, local):
        hostname = self.get_header(buffer)[0]["Host"]
        port = None
        if ":" in hostname:
            (hostname, port) = (hostname.split(":")[0], int(hostname.split(":")[1]))
        if not port:
            port = self.remote_port
        try:
            dst_ip = socket.gethostbyname(hostname)
        except:
            print("Error while getting IP of host", hostname)
            return None
        return IP(src=local[0], dst=dst_ip)/TCP(sport=local[1], dport=port)/buffer

    def proxy_handler(self, client_socket):
        snb = client_socket.fileno()
        local_buffer = receive_from(client_socket)

        if not len(local_buffer):
            client_socket.close()
            return

        hostname = self.get_header(local_buffer)[0]["Host"]
        port = None
        if ":" in hostname:
            (hostname, port) = (hostname.split(":")[0], int(hostname.split(":")[1]))
        if not port:
            port = self.remote_port

        try:
            dst_ip = socket.gethostbyname(hostname)
        except:
            print("Error while getting IP of host", hostname)
            return

        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            remote_socket.connect((dst_ip, port))
        except ConnectionRefusedError:
            print(f"{snb} [!] Connection refused")
            return

        while True:
            if len(local_buffer):
                (header, payload) = self.get_header(local_buffer)
                (header, payload) = self.handler.handle_request(header, payload)
                header["Content-Length"] = len(payload)
                remote_socket.sendall(self.create_request(header, payload))

            remote_buffer = receive_from(remote_socket)
            if len(remote_buffer):
                (header, payload) = self.get_header(remote_buffer, req=False)
                (header, payload) = self.handler.handle_response(header, payload)
                client_socket.sendall(self.create_response(header, payload))

            if not len(local_buffer) or not len(remote_buffer):
                client_socket.close()
                remote_socket.close()
                break

            local_buffer = receive_from(client_socket)

    def loop(self):
        print("[*] Listening on localhost:%d" % self.local_port)
        self.server.listen(64)
        while True:
            client_socket, addr = self.server.accept()
            proxy_thread = threading.Thread(
                target=self.proxy_handler,
                args=(client_socket,)
            )
            proxy_thread.start()

def receive_from(connection, buffer_size=(1024 * 2), timeout=1):
    buffer = b""
    connection.settimeout(timeout)
    try:
        while True:
            data = connection.recv(buffer_size)
            if not data:
                break
            buffer += data
    except Exception as e:
        pass
    return buffer
