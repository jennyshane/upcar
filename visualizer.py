import sys
import os
import glob
import time
import struct
import numpy as np
import cv2

magic_word=[1, 9, 8, 3]

if len(sys.argv)<3:
	print('''Usage: 
		python3 visualizer.py DIRNAME FILE1 FILE2 ...
		requires DIRNAME and at least one FILE''')
	sys.exit()

files=[]
for f in sys.argv[2:]:
	files.append(os.path.join(sys.argv[1], f))

print(files)

for f in files:
	f_handle=open(f, 'rb')
	print(f)
	num_images=0
	while True:
		chunk=f_handle.read(12)
		if chunk:
			*word, STR, THR=struct.unpack('4Bii', chunk)
			if word!=magic_word:
				print("header word is wrong")
				break
			else:
				print(STR, THR)
				#image_bytes=f_handle.read(120*160*3)
				image_bytes=f_handle.read(424*240*3)
				image=np.fromstring(image_bytes, np.uint8).reshape(240, 424, 3)
				new_image=cv2.resize(image, (0, 0), fx=5, fy=5, interpolation=cv2.INTER_NEAREST)
				num_images=num_images+1
				cv2.imshow("images", new_image)
				cv2.waitKey(50)
		else:
			break
	print(num_images)



