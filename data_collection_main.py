import threading
import sys
import os
import time
import serial
import datetime
from observer import *
from cam import *
from button_poller import io_monitor


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
	return data

def serial_write(serial_conn, data):
	assert(len(data)==4)
	dataline='{0}, {1}, {2}, {3}\n'.format(data[0], data[1], data[2], data[3])
	serial_conn.write(dataline.encode('ascii'))
	serial_conn.flush()

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
	data_recorder=recorder("testdata")
	with io_monitor(leds=ledstr, buttons=buttonstr, switches=switchstr) as monitor:
		time.sleep(1)
		monitor.set_led("status", 1)
		while True:
			state=monitor.poll()
			#for i in range(0, state["button"]["toggles"]):
			#	button_state=(button_state==False)
			#	if button_state==False:
			#		recording_toggle=(recording_toggle==False)
			

			data=serial_read(ser)
			Flag("data", {"STR":data[8], "THR":data[9]})
			###This bit should go in a function that handles all the state changes based on serial and gpio input
			if state["data_collect"]["value"]==1 and not data_recorder.status():
				data_recorder.start()
				monitor.set_led("data_collect", 1)
			elif state["data_collect"]["value"]==0 and data_recorder.status():
				data_recorder.stop()
				monitor.set_led("data_collect", 0)

			time.sleep(.01)

finally:
	cam.stop_recording
