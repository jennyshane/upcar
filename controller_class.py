import io
import struct
import threading
import time
from observer import *

button_names={0:'A', 1:'B', 2:'X', 3:'Y', 4:'LB', 5:'RB', 6:'screen', 7:'menu', 8:'xbox'}
analog_names={0:'js1-x', 1:'js1-y', 2:'LT', 3:'js2-x', 4:'js2-y', 5:'RT', 6:'DPad-x', 7:'DPad-y'}

class joystick(object):
	def __init__(self):
		self.joystick_file='/dev/input/js0'
		self.js_data=open(self.joystick_file, 'rb')

		self.data={'lock':threading.Lock(), 'values':{'STR':1500, 'THR':1500}}

		self.stop_ev=threading.Event()
		self.data_thread=threading.Thread(target=self.thread_func)

	def __enter__(self):
		print("!")
		self.data_thread.start()
		return self

	def __exit__(self, exc_type, exc_value, tb):
		self.stop_ev.set()
		self.js_data.close()
		self.data_thread.join()


	def thread_func(self):
		print("starting thread")
		while not self.stop_ev.is_set():
			input_buffer=self.js_data.read(8)
			t, value, in_type, in_id=struct.unpack('IhBB', input_buffer);
			if in_type==2 and analog_names[in_id]=='js1-x':
				self.data['lock'].acquire()
				self.data['values']['STR']=int(1500-(float(value)/2**15)*500)
				self.data['lock'].release()
		
			elif in_type==2 and analog_names[in_id]=='js2-y':
				self.data['lock'].acquire()
				self.data['values']['THR']=int(1500-(float(value)/2**15)*500)
				self.data['lock'].release()
		
			elif in_type==1:
				Flag(button_names[in_id]+"_button", {"value":value, "time":time.time()})

	def poll(self):	
		state={}
		self.data['lock'].acquire()
		state["THR"]=self.data['values']['THR']
		state["STR"]=self.data['values']['STR']
		self.data['lock'].release()
		return state
	
if __name__=="__main__":
	for _, button in button_names.items():
		Observer.observe(button+"_button", lambda event, button=button: print(button, event.value, event.time))

	done=threading.Event()
	Observer.observe("B_button", lambda event : done.set())

	with joystick() as js:
		while not done.is_set():
			state=js.poll()
			print(state['THR'], state['STR'])
			time.sleep(.1)

