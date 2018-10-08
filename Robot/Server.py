from socketserver import ThreadingTCPServer, BaseRequestHandler
from rasa_nlu.model import Interpreter
from scripts.rasa_robot import Robot
from warnings import filterwarnings
from time import sleep

filterwarnings('ignore')
HOST, PORT = "localhost", 8877
MODEL_ADDR = './data/models/current/nlu'
INTERPRETER = Interpreter.load(MODEL_ADDR)

class MyTCPHandler(BaseRequestHandler):
    def handle(self):
        robot = Robot(self.request, INTERPRETER)
        while True:
            self.request.sendall(b'SESSIONSTOP')
            try:
                if not robot.session():
                    self.request.sendall(b'STOPRUNNING')
                    break
            except:
                self.request.sendall(b'There is something mistakes happended.')

if __name__ == "__main__":
    server = ThreadingTCPServer((HOST, PORT), MyTCPHandler)
    print('I am starting to offer service!')
    server.serve_forever()
