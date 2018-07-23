#!/usr/bin/env python

from alexalover import *

debug = False
if len(sys.argv) > 1 and sys.argv[1] == '-d':
    debug = True

al = alexalover(debug)
