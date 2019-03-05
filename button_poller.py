import mraa
import threading
import time
from observer import *




class io_monitor(object):
	def __init__(self, leds={}, buttons={}, switches={}, use_flags=False):
		#leds, buttons and switches arguments should be dicts of the form {'name':{'number':N}, ...}
		#where N is the pin number. Name should be consistent throughout the program
		#if use_flags is true, then generate a flag on every input state change. Otherwise, just call the poll 
		#function regularly.
		self.use_flags=use_flags
		self.buttons=buttons
		self.switches=switches
		self.leds=leds
		self.state_locks={"leds":threading.Lock(), "buttons":threading.Lock(), "switches":threading.Lock()}

		for led in leds:
			self.leds[led]["pin"]=mraa.Gpio(self.leds[led]["number"])
			self.leds[led]["pin"].dir(mraa.DIR_OUT)
			self.leds[led]["pin"].write(0)

		for switch in switches:
			#assumes switches are setup with pull-up resistors, so button presses pull the pin low
			self.switches[switch]["pin"]=mraa.Gpio(self.switches[switch]["number"])
			self.switches[switch]["pin"].dir(mraa.DIR_IN)
			self.switches[switch]["value"]=self.switches[switch]["pin"].read()
			if "debounce_time" not in self.switches[switch]:
				self.switches[switch]["debounce_time"]=.05 #seconds
			self.switches[switch]["timeout"]=time.time()+self.switches[switch]["debounce_time"]

		for button in buttons:
			#assumes buttons are setup with pull-up resistors, so button presses pull the pin low
			self.buttons[button]["pin"]=mraa.Gpio(self.buttons[button]["number"])
			self.buttons[button]["pin"].dir(mraa.DIR_IN)
			self.buttons[button]["value"]=self.buttons[button]["pin"].read()
			self.buttons[button]["fresh"]=0
			#"fresh" is an int that counts the number of toggles since the last time poll has been called
			if "debounce_time" not in self.buttons[button]:
				self.buttons[button]["debounce_time"]=.05 #seconds
			self.buttons[button]["timeout"]=time.time()+self.buttons[button]["debounce_time"]

		self.monitor_thread=threading.Thread(target=self.thread_func, args=[])
		self.stop_ev=threading.Event()

	def __enter__(self):
		self.monitor_thread.start()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.stop_ev.set()
		self.monitor_thread.join()

	def thread_func(self):
		while not self.stop_ev.is_set():
			time.sleep(.0001)
			self.state_locks["buttons"].acquire()
			for button in self.buttons:
				if time.time()>self.buttons[button]["timeout"]:
					if self.buttons[button]["value"]!=self.buttons[button]["pin"].read():
						self.buttons[button]["value"]=self.buttons[button]["pin"].read()
						self.buttons[button]["fresh"]=self.buttons[button]["fresh"]+1
						self.buttons[button]["timeout"]=time.time()+self.buttons[button]["debounce_time"]
						if self.use_flags:
							flag("toggle", {"button":button, "time":time.time()}) 
			self.state_locks["buttons"].release()

			self.state_locks["switches"].acquire()
			for switch in self.switches:
				if time.time()>self.switches[switch]["timeout"]:
					if self.switches[switch]["value"]!=self.switches[switch]["pin"].read():
						self.switches[switch]["value"]=self.switches[switch]["pin"].read()
						self.switches[switch]["timeout"]=time.time()+self.switches[switch]["debounce_time"]
						if self.use_flags:
							flag("toggle", {"switch":switch, "time":time.time()}) 
			self.state_locks["switches"].release()
	

	def poll(self):
		state={}
		self.state_locks["buttons"].acquire()
		for button in self.buttons:
			state[button]={"value":self.buttons[button]["value"], "toggles":self.buttons[button]["fresh"], 
				"last":(self.buttons[button]["timeout"]-self.buttons[button]["debounce_time"])}
			self.buttons[button]["fresh"]=0
		self.state_locks["buttons"].release()

		self.state_locks["switches"].acquire()
		for switch in self.switches:
			state[switch]={"value":self.switches[switch]["value"], 
				"last":(self.switches[switch]["timeout"]-self.switches[switch]["debounce_time"])}
		self.state_locks["switches"].release()
		return state

	def set_led(self, led, state):
		if led not in self.leds:
			print("requested led not being used")
			return 
		if (state!=0) and (state!=1):
			print("requested led state must be bool")
			return 
		self.leds[led]["pin"].write(state)
		print("writing "+led)


