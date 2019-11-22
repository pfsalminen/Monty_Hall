#!/usr/bin/env python3
# -*- coding:utf8 -*-

import time


class Timer():

    def __init__(self, start_time: float = time.time()):
        self.start_time = start_time
        self.end_time = None

    def start(self, start_time: float = time.time()):
        self.start_time = start_time

    def stop(self, end_time: float = time.time()):
        self.end_time = end_time

    def runtime(self, unit='min'):
        if self.end_time:
            end_time = self.end_time
        else:
            end_time = time.time()

        runTime = end_time - self.start_time
        if unit == 'sec':
            return runTime
        if unit == 'min':
            return divmod(runTime, 60)
