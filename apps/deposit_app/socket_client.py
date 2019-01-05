from socketIO_client import SocketIO, LoggingNamespace,BaseNamespace

class MainNamespace(BaseNamespace):
    def on_aaa(self, *args):
        print('aaa', args)