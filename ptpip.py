#!/usr/bin/env python3
# -*- coding: utf-9 -*-

""" PTPIP for Python3

Porting from https://github.com/mmattes/ptpip
"""

import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
s.connect(('192.168.1.1', 15740))