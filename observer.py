import concurrent.futures
#the general structure for this was stolen shamelessly from a stackoverflow post

class Observer(object):
	observables={}
	def __init__(self):
		pass
	
	@staticmethod
	def observe(event_name, callback):
		if event_name in Observer.observables.keys():
			if callback not in Observer.observables[event_name]:
				Observer.observables[event_name].append(callback)
		else:
			Observer.observables[event_name]=[callback]

	@staticmethod
	def unobserve(event_name, callback):
		if event_name in Observer.observables.keys():
			if callback in Observer.observables[event_name]:
				Observer.observables[event_name].remove(callback)


class Flag(object):
	#executor=concurrent.futures.ThreadPoolExecutor()
	def __init__(self, name, attr_dict, autofire=True):
		self.name=name
		for key, value in attr_dict.items():
			setattr(self, key, value)
		if autofire:
			self.fire()
	
	def fire(self):
		#print("firing "+self.name)
		if self.name in Observer.observables.keys():
			for cb in Observer.observables[self.name]:
				cb(self)
				#Flag.executor.submit(cb, self)
