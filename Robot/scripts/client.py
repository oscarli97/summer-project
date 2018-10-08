# coding: utf-8
from socket import socket, AF_INET, SOCK_STREAM
from random import randint
from threading import Thread

HOST, PORT = "localhost", 8877
ID = str(randint(1000,9999))

class base_client(Thread):
    def __init__(self, **kward):
        Thread.__init__(self)
        self._HOST = kward.get('HOST', 'localhost')
        self._PORT = kward.get('PORT', 8879)
        self._ID = kward.get('ID', str(randint(1000, 9999)))
        self._conn = socket(AF_INET, SOCK_STREAM)
        self._conn.connect((self._HOST, self._PORT))
        self._running = True

    def run(self):
        GET_INFO = self.listen()
        try:
            while self._running:
                if GET_INFO:
                    self.say()
                GET_INFO = self.listen()
                
        except Exception as e:
            print('Something wrong as %s' % e)
            
        finally:
            self._conn.close()
                
    def say(self):
        data = self.call()
        self._conn.sendall(bytes(data, encoding = 'utf-8'))

    def listen(self):
        receive = str(self._conn.recv(1024).strip())
        if 'STOPRUNNING' in receive:
            self._running = False
            return
            
        elif 'SESSIONSTOP' in receive:
            receive.replace('SESSIONSTOP', '')
            print('')
            return True
            
        elif 'INPUT' in receive:
            receive.replace('INPUT', '')
            #receive = str(receive)
            self.callback(receive)
            return True
            
        #receive = str(receive)
        self.callback(receive)
        return False

    def callback(self, receive):
        '''Rewrite this function for different API
        '''
        #receive = str(receive)
        print(receive)

    def call(self):
        '''Rewrite this function for different API
        '''
        return input('YOU: ')

if __name__ == '__main__':
    user = base_client(HOST=HOST, PORT=PORT)
    user.start()
    user.join()
