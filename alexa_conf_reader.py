#!/usr/bin/env python
# -*- coding: utf-8 -*-

# AlexaLove - Communicate shell scripts with Amazon Alexa
# Copyright (C) 2018  Rodolfo Garcè´øa Peè´–as (kix) <kix@kix.es>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# alexa_conf_reader.py
# Get the configuration for AlexaLover from the config file
# We need: filename, char used as delimiter and char used for comments
# Usage:
# a = alexa_conf_reader("alexalover.conf", ";", "#")
# devs = a.get_devices()
# for n in devs:
#     print "%s %s %s" % (n[0], n[1], n[2])

import os

class alexa_conf_reader:
    devices = []

    def __init__(self, conffile, delimiter, comment):
        self.conffile = conffile
        self.delimiter = delimiter
        self.comment = comment

    def get_devices(self):
        with open(self.conffile, "r") as ins:
            for line in ins:
                if not line.startswith(self.comment):
                    sl = line.rstrip('\r\n')
                    sl = sl.split(self.delimiter)
                    if len(sl) == 4:
                        if self.which(sl[1]) == sl[1] and self.which(sl[2]) == sl[2]:
                            sl[3] = int(sl[3])
                            if not (sl[3] >= 0) or not (sl[3] < 65536):
                                sl[3] = 0
                            self.devices.append(sl)

            return self.devices

    # Check if the program exists and is executable
    def which(self, program):
        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file

        return None
