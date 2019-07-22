import threading
import sys
import os
import io
import time
import serial
import datetime
import socket 
import struct

from observer import *
from cam import *
from button_poller import io_monitor
from app import *

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

def socket_read(sock, stufflen):
	chunks=io.BytesIO()
	bytes_recd=0
	while bytes_recd<stufflen:
		chunk=sock.recv(12)
		if chunk=='':
			return -1
		chunks.write(chunk)
		bytes_recd=bytes_recd+len(chunk)
	return chunks

def clip(value):
	value=value if value<2000 else 2000
	value=value if value>1000 else 1000
	return value

class SocketDriver(object):
	def __init__(self, sock, serial_obj):
		self.ser=serial_obj
		self.sock=sock
		self.process_thread=threading.Thread(target=self.calculate)
		self.current_output=[1500, 1500] #STR, THR
		self.output_lock=threading.Lock()
		self.stop_event=threading.Event()
		self.state=False

	def start(self):
		self.stop_event.clear()
		if self.process_thread==None:
			self.process_thread=threading.Thread(target=self.calculate)
		self.process_thread.start()
		self.state=True
		
	def stop(self):
		self.stop_event.set()
		self.process_thread.join()
		self.state=False
		self.process_thread=None

	def get_output(self):
		self.output_lock.acquire()
		output=self.current_output
		self.output_lock.release()
		return output

	def status(self):
		return self.state

	def calculate(self):
		while not self.stop_event.is_set():
			res=socket_read(self.sock, 12)
			if res==-1:
				self.stop_event.set()
				break
			command, STR, THR, time=struct.unpack('BhhI', res.getvalue())
			if command==1:
				Flag("shutdown", {})
			STR=clip(STR)
			THR=clip(THR)


			print([STR, THR])
			self.output_lock.acquire()
			self.current_output=[STR, THR]
			self.output_lock.release()
			serial_write(self.ser, [commandEnum.RUN_AUTONOMOUSLY, STR, THR, 0])
	
class termCondition(Observer):
	def __init__(self):
		self.term=False
		self.observe("shutdown", self.stop)

	def stop(self, flag):
		self.term=True

	def isSet(self):
		return self.term

def flaskThread():
	app.run(host='0.0.0.0')


start_auto=False
stop_auto=False


try:
	ser=serial.Serial('/dev/ttyACM1')
except serial.SerialException:
	try:
		ser=serial.Serial('/dev/ttyACM0')
	except serial.SerialException:
		print("can't connect to serial")
		sys.exit()
		
sock_server=socket.socket()
sock_server.bind(('', 8000))
sock_server.listen(0)

(input_sock, address)=sock_server.accept()
tc=termCondition()

flask_thread=threading.Thread(target=flaskThread)

try:
	cam=camera()
	cam.start_recording()
	flask_thread.start()
	driver=SocketDriver(input_sock, ser)
	data_recorder=recorder("testdata")
	with io_monitor(leds=ledstr) as monitor:
		monitor.set_led("status", 1)
		driver.start()
		monitor.set_led("auto", 1)
		while not tc.isSet():
			time.sleep(.02)
			data=serial_read(ser)
			Flag("data", {"STR":data[8], "THR":data[9]})
finally:
	driver.stop()
	cam.stop_recording
