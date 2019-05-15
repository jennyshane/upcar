import time
import torch
import numpy as np

from observer import *
from cam import *
from model import Net

class Driver(object):
	def __init__(self, net, stats):
		self.net=net
		self.steer_mean=stats[0]
		self.steer_std=stats[1]
		Observer.observe("frame", self.calculate)

	def calculate(self, flag):
		image=torch.from_numpy(flag.image).permute(2, 0, 1).float()
		im_mean=image.mean()
		im_std=image.std()
		image=(image-im_mean)/im_std
		output=self.net.forward(image.unsqueeze(0)).item()
		output=output*self.steer_std+self.steer_mean
		print(output)
		

net=Net()
net.load_state_dict(torch.load('weight_file', map_location='cpu'))
net.eval()
steer_stats=np.load("steerstats.npz")['arr_0']
driver=Driver(net, steer_stats)


try:
	cam=camera()
	cam.start_recording()
	while True:
		time.sleep(.001)
finally:
	cam.stop_recording()
