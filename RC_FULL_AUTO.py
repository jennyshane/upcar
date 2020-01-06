import threading
import sys
import os
import time
import serial
import datetime
import torch

from observer import *
from cam import *
from button_poller import io_monitor
from model import Net

def enum(**enums):
	return type('Enum', (), enums)

commandEnum=enum(
	NOT_ACTUAL_COMMAND=0,
	RC_SIGNAL_WAS_LOST=1,
	RC_SIGNALED_STOP_AUTONOMOUS=2, 
	STEERING_VALUE_OUT_OF_RANGE=3,
	THROTTLE_VALUE_OUT_OF_RANGE=4,
	RUN_AUTONOMOUSLY=5,
	STOP_AUTONOMOUS=6,
	STOPPED_AUTO_COMMAND_RECIEVED=7,
	NO_COMMAND_AVAILABLE=8,
	GOOD_PI_COMMAND_RECIEVED=9,
	TOO_MANY_VALUES_IN_COMMAND=10,
	GOOD_RC_SIGNALS_RECIEVED=11)


buttonstr={"button":{"number":15}}
switchstr={"data_collect":{"number":21}, "auto":{"number":23}}
ledstr={"data_collect":{"number":8}, "auto":{"number":10}, "status":{"number":12}}


def serial_read(serial_conn):
	serial_conn.flushInput()
	n_read_items=0
	data=[]
	while n_read_items!=10:
		try:
			data_input=serial_conn.readline()
			data=list(map(float, str(data_input, 'ascii').split(',')))
			n_read_items=len(data)
		except ValueError:
			continue
	#print(data)
	return data

def serial_write(serial_conn, data):
	assert(len(data)==4)
	dataline='{0}, {1}, {2}, {3}\n'.format(data[0], data[1], data[2], data[3])
	#print(dataline)
	serial_conn.write(dataline.encode('ascii'))
	serial_conn.flush()


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

start_auto=False
stop_auto=False

THR_VAL=1537

try:
	ser=serial.Serial('/dev/ttyACM1')
except serial.SerialException:
	try:
		ser=serial.Serial('/dev/ttyACM0')
	except serial.SerialException:
		print("can't connect to serial")
		sys.exit()
		
try:
	cam=camera()
	cam.start_recording()
	driver=Driver(net, steer_stats, ser)
	data_recorder=recorder("testdata")
	with io_monitor(leds=ledstr, buttons=buttonstr, switches=switchstr) as monitor:
		monitor.set_led("status", 1)
		while True:
			time.sleep(.01)
			state=monitor.poll()
			#for i in range(0, state["button"]["toggles"]):
			#	button_state=(button_state==False)
			#	if button_state==False:
			#		recording_toggle=(recording_toggle==False)
			

			#print("reading in main loop")
			data=serial_read(ser)
			Flag("data", {"STR":data[8], "THR":data[9]})
			###This bit should go in a function that handles all the state changes based on serial and gpio input
			if state["data_collect"]["value"]==1 and not data_recorder.status():
				data_recorder.start()
				monitor.set_led("data_collect", 1)
			elif state["data_collect"]["value"]==0 and data_recorder.status():
				data_recorder.stop()
				monitor.set_led("data_collect", 0)

			if state["auto"]["value"]==1 and not driver.status():
				driver.start()
				monitor.set_led("auto", 1)
			elif state["auto"]["value"]==0 and driver.status():
				stop_auto=True
				monitor.set_led("auto", 0)
			time.sleep(.01)
#~~~~~~~~~~~~~~Calculate new state based on inputs~~~~~~~~~~~~~~~~~~~~~~~~~~
			if driver.status(): #if we are in autonomous mode
				if data[0]==commandEnum.RC_SIGNALED_STOP_AUTONOMOUS: #check for RC kill
					driver.stop()
					for i in range(0, 5):
						time.sleep(.01)
						serial_write(ser, [commandEnum.STOPPED_AUTO_COMMAND_RECIEVED, 1500, 1500, 0])
					while monitor.poll()['auto']['value']==1:
						time.sleep(.5)
						monitor.set_led("auto", 0)
						time.sleep(.5)
						monitor.set_led("auto", 1)
					monitor.set_led('auto', 0)
				elif stop_auto==True: #check for gpio kill
					driver.stop()
					serial_write(ser, [commandEnum.STOP_AUTONOMOUS, 1500, 1500, 0])
					time.sleep(.01)
					#print("reading in stop auto")
					data=serial_read(ser)
					while data[0]!=commandEnum.STOPPED_AUTO_COMMAND_RECIEVED:
						serial_write(ser, [commandEnum.STOP_AUTONOMOUS, 1500, 1500, 0])
						#print("reading in stop auto loop")
						data=serial_read(ser)
				else: #normal autonomous 
					pass
					#steering_value=driver.get_output()
					#if steering_value>2000:
					#	steering_value=2000
					#if steering_value<1000:
					#	steering_value=1000
					#serial_write(ser, [commandEnum.RUN_AUTONOMOUSLY, int(steering_value), THR_VAL, 0])


finally:
	cam.stop_recording
