import sys
import os
import glob
import time
import struct
import numpy as np
import cv2

magic_word=[1, 9, 8, 3]

if len(sys.argv)<2:
  print('''Usage: 
python3 visualizer.py DIRNAME FILE1 FILE2 ...
requires DIRNAME and at least one FILE--plays all files in DIRNAME

python3 visualizer.py DIRNAME
requires DIRNAME--plays all files in DIRNAME''')
  sys.exit()

files=[]
if(len(sys.argv)>2):
  for f in sys.argv[2:]:
    files.append(os.path.join(sys.argv[1], f))
else:
  files=glob.glob(os.path.join(sys.argv[1], "data*"))

print(files)

play=False
quit=False
for f in sorted(files):
  f_handle=open(f, 'rb')
  print(f)
  num_images=0
  marked=[]
  while not quit:
    chunk=f_handle.read(12)
    if chunk:
      *word, STR, THR=struct.unpack('4Bii', chunk)
      if word!=magic_word:
        print("header word is wrong")
        print(word)
        break
      else:
        print(STR, THR)
        image_bytes=f_handle.read(424*240*3)
        image=np.fromstring(image_bytes, np.uint8).reshape(240, 424, 3)
        new_image=cv2.resize(image, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
        cv2.imshow("images", new_image)
        if(play):
          char=cv2.waitKey(50)
          if char==ord(" "):
            play=False 
        else:
          char=cv2.waitKey(0)
          if char==ord(" "):
            play=True
          elif char==ord("l"):
            marked.append(num_images)
          elif char==ord("x"):
            quit=True
        num_images=num_images+1
    else:
      break
  print(marked)
  with open(os.path.dirname(f)+"/labels_"+os.path.basename(f)[5:], 'w') as l:
    for i in marked:
      l.write(str(i)+"\n")

  print(num_images)
  if quit:
    break


