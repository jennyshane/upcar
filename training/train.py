import os 
import math
import numpy as np
import glob
import datetime
import argparse

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data.sampler import SubsetRandomSampler

# Import image crop window and other pre defined settings
#from defines import *
from loader import drivingData
from model import Net


#This code sets up the parser for command line arguments specifying parameters for training.
parser=argparse.ArgumentParser()
parser.add_argument('--weight_filename', action='store', default='weights', help='prefix for saved weight files')
parser.add_argument('--init_weights', action='store', default='', 
        help='specifies an existing weight file to use as an initial condition for the network at the start of training')
parser.add_argument('--delay', action='store', default=0, type=int, 
        help='delay between image and steering training data to compensate for processing delay during runtime')
parser.add_argument('--epochs', action='store', default=100, type=int, 
        help='number of epochs to train over')
parser.add_argument('--save_frequency', action='store', default=10, type=int, 
        help='number of epochs between weight file saves')
parser.add_argument('directories', nargs='+', help='list of directories to read training data from')

args=parser.parse_args()

args.directories.sort() #sort directories once, so they will be in the same order when we read images and commands
time_format='%Y-%m-%d_%H-%M-%S'
trainstart=datetime.datetime.now()
time_string=trainstart.strftime(time_format)


#this loads the predefined network architecture from dropout_model.py

num_epochs=args.epochs#number of epochs to train over
save_epochs=args.save_frequency#number of epochs between weight file saves

dataset=drivingData(args.directories)

ntrain=len(dataset)
indices=list(range(ntrain))
nval=int(ntrain*0.02)

validation_idx=np.random.choice(ntrain, size=nval, replace=False)
train_idx=list(set(indices)-set(validation_idx))

train_sampler=SubsetRandomSampler(train_idx)
validation_sampler=SubsetRandomSampler(validation_idx)

train_loader=torch.utils.data.DataLoader(dataset, batch_size=32, sampler=train_sampler, num_workers=4)
validation_loader=torch.utils.data.DataLoader(dataset, batch_size=32, sampler=validation_sampler, num_workers=4)

dev=torch.device('cuda:0')
net=Net().to(device=dev)

criterion=nn.MSELoss()
optimizer=optim.SGD(net.parameters(), lr=0.001, momentum=0.9, weight_decay=1e-6, nesterov=True)


for epoch in range(num_epochs):
    running_loss=0.0
    net.train()
    print("Epoch {0}".format(epoch))
    for i, data in enumerate(train_loader):
        inputs, labels=data["image"].to(dev), data["label"].unsqueeze(1).to(dev)
        optimizer.zero_grad()
        outputs=net.forward(inputs)
        loss=criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss+=loss
        if i%50==49:
            print("Batch {0}: error={1}".format(i, running_loss/50))
            running_loss=0.0
    net.eval()
    val_loss=0.0
    for i, data in enumerate(validation_loader):
        inputs, labels=data["image"].to(dev) , data["label"].unsqueeze(1).to(dev) 
        outputs=net.forward(inputs)
        loss=criterion(outputs, labels)
        val_loss+=loss
    print("Epoch {0}, validation loss={1}".format(epoch, val_loss/len(validation_loader)))
    if epoch%save_epochs==0:
        save_name="weight_file_epoch"+str(epoch)
        torch.save(net.state_dict(), save_name)

        
    

'''
#if the user inputs a weight file for initial state, load it:
if args.init_weights!="":
    model.load_weights(args.init_weights)

for n in range(num_epochs):
    print("starting epoch {0}".format(n))
    h=model.fit([training_images], [(steer-steerSampleMean)/steerSampleSTD], 
                batch_size=25, epochs=1, verbose=1, validation_split=0.1, shuffle=True)

    if n%save_epochs ==0 :
        savename='%s_%s_epoch_%d.h5'%(args.weight_filename, time_string, n)
        print("Saving epoch {0} to {1}".format(n, savename))
        model.save_weights(savename, overwrite=True)

savename='%s_%s_complete.h5'%(args.weight_filename, time_string)
model.save_weights(savename, overwrite=True)
'''
