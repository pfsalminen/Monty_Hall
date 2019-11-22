#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os

AWS_KEY = 'AKIAIVFU5YZHIVROUFMA'
AWS_SECRET = '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'

if os.path.isfile(os.path.join(os.path.abspath('..'), 'data', 'config.json')):
    local = True
else:
    local = False
