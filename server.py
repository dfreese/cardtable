#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Tavendo GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

# import sys
import json

# from twisted.internet import reactor
# from twisted.python import log
# from twisted.web.server import Site
# from twisted.web.static import File

from autobahn.twisted.websocket import (
    WebSocketServerFactory,
    WebSocketServerProtocol,
    listenWS)

import game

class BroadcastServerProtocol(WebSocketServerProtocol):

    def onOpen(self):
        self.id = -1
        self.factory.register(self)

    def onMessage(self, payload, isBinary):
        if not isBinary:
            msg = "{} from {}".format(payload.decode('utf8'), self.peer)
            parsed_json = json.loads(payload.decode('utf8'))
            if 'name' in parsed_json:
                self.factory.set_name(self, parsed_json['name'])
            if 'game' in parsed_json:
                self.factory.game.interp_cmds(parsed_json['game'], self.id)
                self.factory.broadcast_game_state()
            if 'command' in parsed_json:
                if parsed_json['command'] == 'refresh':
                    self.factory.broadcast_game_state()

    def connectionLost(self, reason):
        WebSocketServerProtocol.connectionLost(self, reason)
        self.factory.unregister(self)

class BroadcastServerFactory(WebSocketServerFactory):

    """
    Simple broadcast server broadcasting any message it receives to all
    currently connected clients.
    """

    def __init__(self, url):
        WebSocketServerFactory.__init__(self, url)
        self.game = game.Game()
        self.names = []
        self.clients = []

    def register(self, client):
        if client not in self.clients:
            print("registered client {}".format(client.peer))
            self.clients.append(client)
            self.names.append('Player %d' % len(self.clients))
            self.game.push_hand()
            client.id = self.clients.index(client)
        self.send_players()
        self.broadcast_game_state()

    def unregister(self, client):
        if client in self.clients:
            print("unregistered client {}".format(client.peer))
            client_idx = self.clients.index(client)
            self.names.pop(client_idx)
            self.clients.remove(client)
            hand_stack = self.game.pop_hand(client_idx)
            hand_stack.set_face_up(False)
            if len(hand_stack.cards) > 0:
                # Find the first empty stack, if any, and pop it, adding the
                # unregistered had as the last stack on the table.
                for stack in self.game.table.stacks:
                    if len(stack.cards) == 0:
                        self.game.table.stacks.pop(
                            self.game.table.stacks.index(stack)
                        )
                        break
                self.game.table.push_stack(hand_stack)
        self.send_players()
        self.broadcast_game_state()

    def broadcast(self, msg):
        for c in self.clients:
            c.sendMessage(msg.encode('utf8'))

    def broadcast_game_state(self):
        state_dict = {'game_state' : self.game.serialize()}
        self.broadcast(json.dumps(state_dict))

    def send_players(self):
        player_dict = {'players': [{'name': n} for n in self.names]}
        self.send_player_ids()
        self.broadcast(json.dumps(player_dict))

    def send_player_ids(self):
        for client in self.clients:
            id_dict = {'player_id' : self.clients.index(client)}
            msg = json.dumps(id_dict)
            client.sendMessage(msg.encode('utf8'))

    def set_name(self, client, name):
        print('changing name to %s for %s' % (name, client.peer))
        client_idx = self.clients.index(client)
        self.names[client_idx] = name
        self.send_players()

if __name__ == '__main__':
    factory = BroadcastServerFactory(u"ws://127.0.0.1:9000")
    factory.protocol = BroadcastServerProtocol
    listenWS(factory)

#     webdir = File(".")
#     web = Site(webdir)
#     reactor.listenTCP(8080, web)
#     reactor.run()
