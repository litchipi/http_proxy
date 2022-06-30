
import argparse

class Arguments:
    def __init__(self):
        self.parser = argparse.ArgumentParser()

        self.add_arguments("port", type=int, help="Port on which the proxy is listening")

    def add_arguments(self, *args, **kwargs):
        self.parser.add_argument(*args, **kwargs)

    def get_args(self):
        return self.parser.parse_args()
