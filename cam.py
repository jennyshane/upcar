import time
import datetime
import struct
import threading
import cv2
import numpy as np
import pyrealsense2 as rs
from observer import *

time_format='%Y-%m-%d_%H-%M-%S'
magic_word=[1, 9, 8, 3]

class timeout(Exception):
	def __init__(self, message):
		self.message=message

class recorder(object):

	def __init__(self, save_dir, filename_prefix="data"):
		self.save_directory=save_dir
		self.filename_prefix=filename_prefix
		self.active_file={'lock': threading.Lock(), 'file':None}
		self.frameidx=0
		self.current_data={'lock':threading.Lock(), 'data':{"time":time.time()}}
		self.is_recording=False

	def start(self):
		print("starting recording")
		filename=self.save_directory+'/'+self.filename_prefix+'_{0}'.format(datetime.datetime.now().strftime(time_format))
		self.active_file['file']=open(filename, "wb")
		self.frameidx=0
		Observer.observe("data", self.data_callback)
		Observer.observe("frame", self.frame_callback)
		self.is_recording=True
		
	def stop(self):
		Observer.unobserve("frame", self.frame_callback)
		Observer.unobserve("data", self.data_callback)
		self.active_file['lock'].acquire()
		self.active_file['file'].close()
		self.active_file['lock'].release()
		self.is_recording=False

	def frame_callback(self, flag):
		#print("frame_callback:  "+str(time.time()))
		#copy the data so we don't have to worry about it changing
		self.current_data['lock'].acquire()	#ACQUIRE DATA LOCK
		temp_data=self.current_data['data'].copy() 
		self.current_data['lock'].release()	#RELEASE DATA LOCK
		#make sure that the data isn't too old
		if time.time()-temp_data['time']>.05: 	#this value is just a guess, idk if it's reasonable
			print("stale data")
			return
		#write data and image to file
		self.active_file['lock'].acquire()	#ACQUIRE FILE LOCK
		self.active_file['file'].write(struct.pack('4Bii', *magic_word, int(temp_data['STR']), int(temp_data['THR'])))
		self.active_file['file'].write(flag.image.tobytes())
		self.frameidx=self.frameidx+1
		#if we have written 100 images to the file
		if self.frameidx==100:
			print("!")
			self.frameidx=0
			self.active_file['file'].close() #close it
			filename=self.save_directory+'/'+self.filename_prefix+'_{0}'.format(datetime.datetime.now().strftime(time_format))
			self.active_file['file']=open(filename, "wb") # and open a new one
		self.active_file['lock'].release()	#RELEASE FILE LOCK

	def data_callback(self, flag):
		if hasattr(flag, 'STR') and hasattr(flag, 'THR'):
			#print("data_callback:  "+str(time.time()))
			self.current_data['lock'].acquire()	#ACQUIRE DATA LOCK
			self.current_data['data']={'time':time.time(), 'STR':flag.STR, 'THR':flag.THR}
			self.current_data['lock'].release()	#RELEASE DATA LOCK

	def status(self):
		return self.is_recording


class camera(object):
	def __init__(self, *args):
		#passes in optional number of callbacks to receive notification when there is a new frame 
		for arg in args:
			if callable(arg):
				Observer.observe("frame", arg) #this might be a bad idea:
							       #Probably either publishers or subscribers should do this, but not both
		self.camera_thread=threading.Thread(target=self.thread_func, args=[])
		self.stop_event=threading.Event()
		self.pipe=rs.pipeline()
		self.config=rs.config()
		self.config.enable_stream(rs.stream.color, 424, 240, rs.format.bgr8, 30)
		self.profile=self.pipe.start(self.config)


	def start_recording(self):
		# start recording: start thread
		print("camera start")
		self.camera_thread.start()

	def stop_recording(self):
		# stop recording: set stop flag and join
		self.stop_event.set()
		self.camera_thread.join()
		self.pipe.stop()

	def thread_func(self):
		# get new image every 1/fps seconds, then create flag with image as argument
		while not self.stop_event.isSet():
			frames=self.pipe.wait_for_frames()
			color_frame=frames.get_color_frame()
			color_image=np.asanyarray(color_frame.get_data())
			Flag("frame", {"image":color_image.copy()})

			


