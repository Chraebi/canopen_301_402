#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from canopen_301_402.constants import *
from canopen_301_402.canopen_msgs.msgs import *
from canopen_301_402.canopen_301.obj import CanOpenObject
from canopen_301_402.signal import Signal

from canopen_301_402.operations import Operations


class SetTargetPosition(Operations):
    def __init__(self, node, value, relative=False, immediatly=False):
        self.node = node
        self.canopen = node.canopen

        self.value = value
        self.relative = relative
        self.immediatly = immediatly

        super(SetTargetPosition, self).__init__()

    def step1(self):
        print "step1"
        self.node.sdo.signal_write_complete[Can402Objects.target_position].register_once(self.next_operation)

        # set target position value
        data = self.node.can402.target_position.datatype.encode(self.value)
        msg = CanOpenMessageSdoWriteRequest(
            self.canopen, 
            self.node.node_id, 
            Can402Objects.target_position[0], 
            Can402Objects.target_position[1], 
            data)
        self.canopen.send_msg(msg)

    def step2(self):
        print "step2"
        self.node.sdo.signal_write_complete[Can402Objects.controlword].register_once(self.next_operation)

        # notify device of new target by setting controlword
        state = self.node.can402.controlword.value

        if self.relative:
            state |= (1 << Can402ControlwordBits.abs_rel.value)
        else:
            state &= ~(1 << Can402ControlwordBits.abs_rel.value)

        state |= (1 << Can402ControlwordBits.new_set_point.value)
        
        if self.immediatly:
            state |= (1 << Can402ControlwordBits.change_set_immediately.value)
        else:
            state &= ~(1 << Can402ControlwordBits.change_set_immediately.value)

        data = [state & 0xFF, (state >> 8) & 0xFF]

        msg = CanOpenMessageSdoWriteRequest(
            self.canopen, 
            self.node.node_id, 
            Can402Objects.controlword[0], 
            Can402Objects.controlword[1], 
            data)

        self.canopen.send_msg(msg)

        # antwort 
          # can0  181   [2]  37 10
          # can0  281   [6]  37 10 05 2F 01 00
          # can0  381   [6]  37 10 02 00 00 00


    def step3(self):
        print "step3"
        self.node.sdo.signal_write_complete[Can402Objects.controlword].register_once(self.next_operation)

        # reset new target bit in controlword (dont really know why, but this is mandatory)
        state = self.node.can402.controlword.value
        state ^= (1 << Can402ControlwordBits.new_set_point.value)

        data = [state & 0xFF, (state >> 8) & 0xFF]

        msg = CanOpenMessageSdoWriteRequest(
            self.canopen, 
            self.node.node_id, 
            Can402Objects.controlword[0], 
            Can402Objects.controlword[1], 
            data)

        self.canopen.send_msg(msg)


class CanOpen402(object):
    """docstring for CanOpen402"""
    def __init__(self, node):
        super(CanOpen402, self).__init__()
        self.node = node
        self.canopen = node.canopen
        
        self.controlword = None
        self.statusword = None
        self.modes_of_operation_set = None
        self.modes_of_operation_get = None
        self.target_position = None
        self.populate_with_defaults()

        self.state = Can402State.switch_on_disabled

        self.statusword.signal_value_updated.register(self._on_statusword_update)

        self.signal_enter_state = dict()
        for state in Can402State:
            self.signal_enter_state[state] = Signal()


    def populate_with_defaults(self):
        # init controlword and statusword
        self.node.obj_dict.objects[Can402Objects.controlword] = CanOpenObject(self.node, *Can402Objects.controlword)
        self.node.obj_dict.objects[Can402Objects.statusword] = CanOpenObject(self.node, *Can402Objects.statusword)
        self.node.obj_dict.objects[Can402Objects.modes_of_operation_set] = CanOpenObject(self.node, *Can402Objects.modes_of_operation_set)
        self.node.obj_dict.objects[Can402Objects.modes_of_operation_get] = CanOpenObject(self.node, *Can402Objects.modes_of_operation_get)
        self.node.obj_dict.objects[Can402Objects.target_position] = CanOpenObject(self.node, *Can402Objects.target_position)

        self.controlword = self.node.obj_dict.objects[Can402Objects.controlword]
        self.statusword = self.node.obj_dict.objects[Can402Objects.statusword]
        self.modes_of_operation_set = self.node.obj_dict.objects[Can402Objects.modes_of_operation_set]
        self.modes_of_operation_get = self.node.obj_dict.objects[Can402Objects.modes_of_operation_get]
        self.target_position = self.node.obj_dict.objects[Can402Objects.target_position]

        print self.controlword.eds_obj

        # set datatypes
        self.node.obj_dict.objects[Can402Objects.controlword].datatype_id = CanOpenBasicDatatypes.uint16
        self.node.obj_dict.objects[Can402Objects.statusword].datatype_id = CanOpenBasicDatatypes.uint16
        self.node.obj_dict.objects[Can402Objects.modes_of_operation_set].datatype_id = CanOpenBasicDatatypes.uint8
        self.node.obj_dict.objects[Can402Objects.modes_of_operation_get].datatype_id = CanOpenBasicDatatypes.uint8
        self.node.obj_dict.objects[Can402Objects.target_position].datatype_id = CanOpenBasicDatatypes.int32


    def _on_statusword_update(self):
        # todo: change state
        for state,bits in Can402StatuswordStateBits.iteritems():
            mask = Can402StatuswordStateMasks[state]
            if (self.statusword.value & mask) == bits:
                self.state = state
                self.signal_enter_state[state].dispatch()
                break

    def set_mode(self, mode, callback_complete=None):
        '''
        @summary: 
        @param mode: Can402ModesOfOperation
        @result: 
        '''

        if callable(callback_complete):
            self.node.obj_dict.objects[Can402Objects.modes_of_operation_set].signal_value_updated.register_once(callback_complete)

        data = [Can402ModesOfOperationBits[mode]]
        
        msg = CanOpenMessageSdoWriteRequest(
            self.canopen, 
            self.node.node_id, 
            Can402Objects.modes_of_operation_set[0], 
            Can402Objects.modes_of_operation_set[1], 
            data)

        self.canopen.send_msg(msg)


    def change_state(self, command, callback_complete=None):
        '''
        @param command: Can402StateCommand
        '''

        if self.state not in Can402StateTransitions: raise Exception()
        if command not in Can402StateTransitions[self.state]: raise ValueError()
        new_state = Can402StateTransitions[self.state][command]

        state = self.controlword.value
        datatype = self.controlword.datatype

        assert datatype.identifier() == CanOpenBasicDatatypes.uint16


        bits = Can402StateCommandBits[command] # value of bits to be replaced
        mask = Can402StateCommandMask[command] # which bits shall be replaced
        # set all bits to zero that will be replaced 
        state = state & (~mask & 0xFFFF)
        # replace bits
        state = state | (mask & bits & 0xFFFF)
        data = [state & 0xFF, (state >> 8) & 0xFF]


        def value_updated(*args):
            self.state = new_state
            if callable(callback_complete):
                callback_complete()

        self.node.sdo.signal_write_complete[Can402Objects.controlword].register_once(value_updated)

        msg = CanOpenMessageSdoWriteRequest(
            self.canopen, 
            self.node.node_id, 
            Can402Objects.controlword[0], 
            Can402Objects.controlword[1], 
            data)

        self.canopen.send_msg(msg)

    def start_homing(self):
        state = self.controlword.value
        state |= (1 << Can402ControlwordBits.new_set_point.value)
        data = [state & 0xFF, (state >> 8) & 0xFF]
        msg = CanOpenMessageSdoWriteRequest(
            self.canopen, 
            self.node.node_id, 
            Can402Objects.controlword[0], 
            Can402Objects.controlword[1], 
            data)

        self.canopen.send_msg(msg)

    def set_target_position(self, value, relative=False, immediatly=False):
        '''
        @summary: set new target position in 
        @param value:
        @param relative:
        @param immediatly:
        @result: 
        '''

        # todo check Voraussetzung: NMT-Zustand „Operational“, Antriebszustand „Operation Enabled“ und Modes of
        # Operation (0x6060) auf Profile Position Mode (1) gesetzt.

        op = SetTargetPosition(self.node, value, relative, immediatly)
        op.start()



    def current_status(self):
        value = self.statusword.value
        if value is None: return None

        result = dict()
        for item in Can402StatuswordBits:
            result[item.name] = ((value & (1 << item.value)) == (1 << item.value))
        return result
