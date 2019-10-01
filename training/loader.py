import os
import glob
import struct
import datetime
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

timestr='%Y-%m-%d_%H-%M-%S'

magic_word=[1, 9, 8, 3]

image_size=424*240*3

class drivingData(Dataset):

    def __init__(self, directories): 
        #when we create a new dataset, we read in all the .npz files and save them as binary files
        directories.sort() #list of directories to pull .npz datafiles from
        steer=np.array([])
        throttle=np.array([])
        self.data_lengths=[]
        self.files_list=[]


        for directory in directories:
            files=glob.glob(os.path.join(directory, "data*"))
            for f in sorted(files):
                self.files_list.append(f)
                f_handle=open(f, 'rb')
                print(f)
                num_images=0
                while True:
                    chunk=f_handle.read(12)
                    if chunk:
                        *word, STR, THR=struct.unpack('4Bii', chunk)
                        if word!=magic_word:
                            print("Error reading file: incorrect header word")
                            print(word)
                            break
                        else:
                            image_bytes=f_handle.read(image_size)
                            num_images=num_images+1
                            steer=np.append(steer, STR)
                            throttle=np.append(throttle, THR)
                    else:
                        break
                self.data_lengths.append(num_images)
        self.labels=torch.from_numpy(steer).float() #save labels as torch tensor
        self.steer_mean=self.labels.mean()
        self.steer_std=self.labels.std()
        print(self.steer_mean)
        print(self.steer_std)
        np.savez("steerstats.npz", [self.steer_mean, self.steer_std])
        self.labels=(self.labels-self.steer_mean)/self.steer_std #normalize
        #we use this array to determine which file to open given a sample index
        self.start_idx=[sum(self.data_lengths[0:i]) for i in range(0, len(self.data_lengths))] 
        print("parsed dataset")

    def __len__(self):
        return sum(self.data_lengths)

    def __getitem__(self, idx):
        fileidx=np.searchsorted(self.start_idx, idx, side='right')-1
        local_idx=idx-self.start_idx[fileidx]
        f=open(self.files_list[fileidx], "rb")
        f.seek(local_idx*(image_size+12))
        header=f.read(12)
        *word, STR, THR=struct.unpack('4Bii', header)
        if word!=magic_word:
            print("Error reading file: incorrect header word")
            print(word)
        imdata=f.read(image_size)
        image=torch.from_numpy(np.reshape(np.fromstring(imdata, dtype=np.uint8), (240, 424, 3))).permute(2, 0, 1).float()
        img_mean=image.mean()
        img_std=image.std()
        sample={"image":(image-img_mean)/img_std, "label":(STR-self.steer_mean)/self.steer_std}
        return sample
