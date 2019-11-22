#!/usr/bin/env python3
# -*- coding:utf-8 -*-

'''net_sync.py  psalminen@verisk.com    Service Software Inc. 2018
Parent program for the net_sync integration client.
Cmd fire app that triggers all aspects of the client.
Functions:
    run         - Runs active scripts, creates XMLs and sends via FTP or to S3
    edit        - Opens gui to edit scripts and add new ones
'''

import fire
import local_gui
import scripter

def run():
    scripter.run()


def edit():
    local_gui.run()


if __name__=='__main__':
    fire.Fire()
