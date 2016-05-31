#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from enum import Enum


class CanFunctionCode(Enum): # todo better name, Kommunikation_DE_7000_00030.PDF pg. 69
    nmt  = b0000 # node_id must be 0
    sync = b0001 # node_id must be 0
    emergency = b0001
    pdo1_tx = b0011
    pdo1_rx = b0100
    pdo2_tx = b0101
    pdo2_rx = b0110
    pdo3_tx = b0111
    pdo3_rx = b1000
    sdo_tx = b1011
    sdo_rx = b1100
    nmt_error_control = b1110   

class CanData(Enum): # todo better name
    sdo_upload_request = 0x40        # 0b 0100 0000
    sdo_upload_response = 0x43       # 0b 0100 0011
    sdo_download_request_bits = 0x23 # 0b 0010 0011 
    sdo_download_response = 0x60     # 0b 0110 0000 
    sdo_error = 0x80


class Can301StateCommand(Enum):
    start_remote_node = 0x01
    enter_pre_operational = 0x80
    stop_remote_node = 0x02
    reset_node = 0x81
    reset_communication = 0x82

# Kommunikation DE_7000_00030.PDF pg. 64
CanErrors = dict({
        0x05030000: "toggle bit not changed",
        0x05040001: "SDO command specifier not valid",
        0x06010000: "access to this object not supported",
        0x06010002: "try to write to read-only property",
        0x06020000: "object not existing in object dictionary",
        0x06040041: "object can not be mapped in PDO",
        0x06040042: "number and/or length of mapped objects would exceed PDO length",
        0x06040043: "general parameter incompatibility",
        0x06040047: "general internal device error",
        0x06060000: "access aborted due to hardware error",
        0x06070010: "data type or parameter length does not match or not known",
        0x06070012: "data type does not match: parameter length to high",
        0x06070013: "data type does not match: parameter length to low",
        0x06090011: "subindex not existing",
        0x06090030: "general domain error",
        0x06090031: "domain error: parameter value to big",
        0x06090032: "domain error: parameter value to small",
        0x060A0023: "resource not available",
        0x08000021: "access not available due to local application",
        0x08000022: "access not available due to current device state"
    })

CanErrors.unknown = "Unknown error code: %s"
