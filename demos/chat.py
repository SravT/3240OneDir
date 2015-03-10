#!/usr/bin/env python

from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor

class SendContent(Protocol):
    def connectionMade(self):
        self.transport.write(self.factory.text)
        self.transport.loseConnection()

class SendContentFactory(Factory):
    protocol = SendContent
    def __init__(self, text=None):
        if text is None:
            text = """Hello, how are you my friend? Feeling fine? Good!"""
        self.text = text

reactor.listenTCP(50000, SendContentFactory())
reactor.run()
