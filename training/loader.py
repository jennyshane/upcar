import os
import glob
import struct
import datetime
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

timestr='%Y-%m-%d_%H-%M-%S'

class drivingData(Dataset):

    def __init__(self, directories, nrows, row_crop): 
        #when we create a new dataset, we read in all the .npz files and save them as binary files
        self.nrows=nrows
        self.row_crop=row_crop
        self.save_dir="cache_"+datetime.datetime.now().strftime(timestr)
        os.mkdir(self.save_dir)
        directories.sort() #list of directories to pull .npz datafiles from
        steer=np.array([])
        self.data_lengths=[]

        for directory in directories:
            ctlfiles=glob.glob(os.path.join(directory, "commands*.npz"))
            for ctlfile in sorted(ctlfiles):
                ctldata=np.load(ctlfile)['arr_0']
                data_to_append=np.trim_zeros(ctldata[:, 1], trim='b') #if any of the labels, are zero, we should ignore those samples
                self.data_lengths.append(len(data_to_append))
                steer=np.concatenate((steer, data_to_append), axis=0)

        self.labels=torch.from_numpy(steer).float() #save labels as torch tensor
        self.steer_mean=self.labels.mean()
        self.steer_std=self.labels.std()
        np.savez("steerstats.npz", [self.steer_mean, self.steer_std])
        #TODO should save steerstats file here
        self.labels=(self.labels-self.steer_mean)/self.steer_std #normalize

        #we use this array to determine which file to open given a sample index
        self.start_idx=[sum(self.data_lengths[0:i]) for i in range(0, len(self.data_lengths))] 

        i=0
        for directory in directories:
            imgfiles=glob.glob(os.path.join(directory, "imgs*.npz"))
            for imgfile in sorted(imgfiles):
                imdata=np.load(imgfile)['arr_0'].astype(np.uint8)
                cropdata=imdata[0:self.data_lengths[i], row_crop:row_crop+nrows, :, :]
                filename="images"+str(i)
                f=open(self.save_dir+"/"+filename, "wb")
                #this header data is unecessary
                f.write(bytes([0x00, 0x00, 0x08, 0x03])) #Magic number, just in case
                f.write(struct.pack(">i", imdata.shape[0])) #number of samples in the file
                for image in cropdata:
                    f.write(image.tobytes())
                f.close()
                i+=1
        print("created cache")

    def __len__(self):
        return sum(self.data_lengths)

    def __getitem__(self, idx):
        filenum=0
        for i in range(0, len(self.data_lengths)):
            if idx>=self.start_idx[len(self.data_lengths)-1-i]:
                filenum=len(self.data_lengths)-1-i
                break
        local_idx=idx-self.start_idx[filenum]
        f=open(self.save_dir+"/images"+str(filenum), "rb")
        header=f.read(8)
        data=struct.unpack(">ii", header) #could check this. probably not necessary
        assert(local_idx<=data[1])
        assert(data[1]==self.data_lengths[filenum])

        f.seek(8+self.nrows*128*3*local_idx)
        imdata=f.read(self.nrows*128*3)
        image=torch.from_numpy(np.reshape(np.fromstring(imdata, dtype=np.uint8), (self.nrows, 128, 3))).permute(2, 0, 1).float()
        img_mean=image.mean()
        img_std=image.std()
        sample={"image":(image-img_mean)/img_std, "label":self.labels[idx]}
        return sample

