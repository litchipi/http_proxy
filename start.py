#!/usr/bin/env python3

from tcp_proxy import HttpProxy, Arguments

class Handler:
    def handle_response(self, header, payload):
        return header, payload

    def handle_request(self, header, payload):
        return header, payload

# TODO  Set up for a specific website only

if __name__ == '__main__':
    args = Arguments().get_args()
    proxy = HttpProxy(Handler(), args.port)
    proxy.loop()
