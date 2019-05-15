import threading
import sys
import os
import time
import serial
import datetime
import cv2
from observer import *
from cam import *
from button_poller import io_monitor

class viewer(object):
	def __init__(self):
		self.frame=None
		self.frame_event=threading.Event()
		self.view_thread=threading.Thread(target=self.view_func)
		self.view_thread.start()
		Observer.observe("frame", self.new_frame)

	def new_frame(self, flag):
		self.frame=flag.image
		self.frame_event.set()

	def view_func(self):
		while True:
			self.frame_event.wait()
			self.frame_event.clear()
			cv2.namedWindow("stream", cv2.WINDOW_AUTOSIZE)
			cv2.imshow("stream", self.frame)
			cv2.waitKey(1)
			

try:
	cam=camera()
	cam.start_recording()
	v=viewer()
	data_recorder=recorder("/home/jenny/upcar/testdata")
	Flag("data", {"STR":0, "THR":0})
	data_recorder.start()
	while True:
		Flag("data", {"STR":0, "THR":0})
		time.sleep(.01)
finally:
	data_recorder.stop()
	cam.stop_recording()

