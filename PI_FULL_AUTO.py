import threading
import sys
import os
import time
import serial
import datetime
#import torch
import mraa

from controller_class import *
from observer import *
from cam import *
#from model import Net

pin_blue=8
pin_white=10
pin_red=12

def serial_write(serial_conn, speed, steer):
	assert(len(data)==2)
	sp_str=str(speed).zfill(3)
	st_str=str(steer).zfill(3)
	print("writing ", speed, steer)
	serial_conn.write((sp_str+","+st_str+"\n").encode("ascii"))
	serial_conn.readline()

def map_steering(value):
	return int(70*(1000-(value-1000))/1000+50)

def map_throttle(value):
	return int(510*(value-1000)/1000)



'''
class Driver(object):
	def __init__(self, net, stats, serial_obj):
		self.net=net
		self.steer_mean=stats[0]
		self.steer_std=stats[1]
		self.ser=serial_obj
		self.frame=None
		self.frame_event=threading.Event()
		self.process_thread=threading.Thread(target=self.calculate)
		self.current_output=1500
		self.output_lock=threading.Lock()
		self.stop_event=threading.Event()
		self.state=False

	def start(self):
		self.stop_event.clear()
		if self.process_thread==None:
			self.process_thread=threading.Thread(target=self.calculate)
		self.process_thread.start()
		Observer.observe("frame", self.new_frame)
		self.state=True
		
	def stop(self):
		self.stop_event.set()
		self.process_thread.join()
		Observer.unobserve("frame", self.new_frame)
		self.state=False
		self.process_thread=None

	def new_frame(self, flag):
		self.frame=flag.image
		self.frame_event.set()

	def get_output(self):
		self.output_lock.acquire()
		output=self.current_output
		self.output_lock.release()
		return output

	def status(self):
		return self.state

	def calculate(self):
		while not self.stop_event.is_set():
			self.frame_event.wait()
			self.frame_event.clear()
			image=torch.from_numpy(self.frame).permute(2, 0, 1).float()
			im_mean=image.mean()
			im_std=image.std()
			image=(image-im_mean)/im_std
			output=self.net.forward(image.unsqueeze(0)).item()
			output=output*self.steer_std+self.steer_mean
			if output>2000:
				output=2000
			if output<1000:
				output=1000
			print(output)
			self.output_lock.acquire()
			self.current_output=output
			self.output_lock.release()
			serial_write(self.ser, [commandEnum.RUN_AUTONOMOUSLY, int(output), THR_VAL, 0])
	
net=Net()
net.load_state_dict(torch.load('weight_file', map_location='cpu'))
net.eval()
steer_stats=np.load("steerstats.npz")['arr_0']
'''

start_auto=False
stop_auto=False

THR_VAL=1537
		
data_collect_flag=threading.Event()
autonomous_flag=threading.Event()

try:
	ser=serial.Serial('/dev/ttyACM1')
except serial.SerialException:
	try:
		ser=serial.Serial('/dev/ttyACM0')
	except serial.SerialException:
		print("can't connect to serial")
		sys.exit()
		
try:
	led_blue=mraa.Gpio(pin_blue)
	led_blue.dir(mraa.DIR_OUT)
	led_blue.write(0)
	
	led_white=mraa.Gpio(pin_white)
	led_white.dir(mraa.DIR_OUT)
	led_white.write(0)
	
	led_red=mraa.Gpio(pin_red)
	led_red.dir(mraa.DIR_OUT)
	led_red.write(0)

	cam=camera()
	cam.start_recording()
	#driver=Driver(net, steer_stats, ser)
	data_recorder=recorder("testdata")
	Observer.observe("3_button", lambda event : autonomous_flag.set() if event.value else None)
	Observer.observe("2_button", lambda event : data_collect_flag.set() if event.value else None)
	led_white.write(1)
	with joystick() as js:
		while True:
			time.sleep(.01)
			data=js.poll()
			steer_value=map_steering(data["STR"])
			throttle_value=map_throttle(data["THR"])
			Flag("data", {"STR":steer_value, "THR":throttle_value})
			###This bit should go in a function that handles all the state changes based on serial and gpio input
			if data_collect_flag.is_set():
				data_collect_flag.clear()
				if not data_recorder.status():
					data_recorder.start()
					led_blue.write(1)
				else:
					data_recorder.stop()
					led_blue.write(0)
			if autonomous_flag.is_set():
				autonomous_flag.clear()
				if not driver.status():
					#driver.start()
					led_red.write(1)
				else:
					#driver.stop()
					led_red.write(0)
			time.sleep(.01)
			#if not driver.status(): 
			serial_write(ser, throttle_value, steer_value)

				
finally:
	cam.stop_recording
	led_white.write(0)
