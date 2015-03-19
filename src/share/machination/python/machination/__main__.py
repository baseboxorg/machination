#!/usr/bin/env python

##########################################################################
# Machination
# Copyright (c) 2014, Alexandre ACEBEDO, All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.
##########################################################################
import os
import sys
sys.path.append(os.path.abspath(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','share','machination','python'))))
from machination.cmdline import CmdLine
from machination.helpers import mkdir_p
from machination.constants import MACHINATION_USERINSTANCESDIR

def __main__():
    mkdir_p(MACHINATION_USERINSTANCESDIR)
    cmd = CmdLine()
    cmd.parseArgs(sys.argv)

if __name__ == "__main__":
    __main__()