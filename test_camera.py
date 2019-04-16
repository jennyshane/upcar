import threading
import sys
import os
import time
import serial
import datetime
from observer import *
from cam import *
from button_poller import io_monitor


try:
	cam=camera()
	cam.start_recording()
	data_recorder=recorder("/home/jenny/upcar/testdata")
	Flag("data", {"STR":0, "THR":0})
	data_recorder.start()
	while True:
		Flag("data", {"STR":0, "THR":0})
		time.sleep(.01)
finally:
	data_recorder.stop()
	cam.stop_recording()

