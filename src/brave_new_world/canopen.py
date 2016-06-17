#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import can

from brave_new_world.utils import *
from brave_new_world.connection_set import ConnectionSet
from brave_new_world.canopen_msgs.msg import CanOpenMessage
from brave_new_world.canopen_msgs.msgs import *

import Queue

from collections import defaultdict

class CanOpen(can.Listener):
    """docstring for CanOpen"""
    def __init__(self, bus):
        super(CanOpen, self).__init__()
        self.bus = bus
        self.notifier = can.Notifier(self.bus,[self])

        self.connection_set = ConnectionSet()

        self.msgs = CanOpenMessages(self)

        self.msg_queues = defaultdict(Queue.Queue)

        self.msg_history = list()
        self.enable_history = True

    def send(self, msg):
        print type(msg), msg
        # send can msg
        if isinstance(msg, CanOpenMessage):
            self.bus.send(msg.to_can_msg())
        elif type(msg) == can.Message:
            self.bus.send(msg)
        elif type(msg) == str:
            self.bus.send(str_to_can_msg(msg))

        else:
            raise ValueError()


    def on_message_received(self, msg):

        # convert message to canopen message
        if type(msg) == can.Message:
            msg = CanOpenMessage.from_can_msg(msg, self)

        # parse message into higher level canopen message types
        if type(msg) == CanOpenMessage:
            msg = self.msgs.try_to_upgrage_canopen_message(msg)

        # history
        if self.enable_history:
            self.msg_history.append(msg)

        # enqueue CanOpenMessage
        self.msg_queues[msg.node_id].put(msg)
