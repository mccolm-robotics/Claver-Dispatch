#!/usr/bin/python

import os
import subprocess

dir_path = os.path.dirname(os.path.realpath(__file__))

subprocess.run(['python3', dir_path+"/ClaverTest.py"])


exit("Starting Claver Dispatch")
