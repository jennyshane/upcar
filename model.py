import os
import math
import glob
import numpy as np


import torch
import torch.nn as nn
import torch.nn.functional as F

conv_dropout_rate=0.125 # dropout rate for 2d dropout in convolutional layers
fc_dropout_rate=0.125 # dropout rate for fully connected layers

#NOTE: 2d dropout randomly zeros whole channels during training. 

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1=nn.Conv2d(3, 24, 5, stride=3, padding=2)
        self.dropout1=nn.Dropout2d(conv_dropout_rate)
        self.conv2=nn.Conv2d(24, 28, 5, stride=3, padding=2)
        self.dropout2=nn.Dropout2d(conv_dropout_rate)
        self.conv3=nn.Conv2d(28, 32, 3, stride=2, padding=1)
        self.dropout3=nn.Dropout2d(conv_dropout_rate)
        self.conv4=nn.Conv2d(32, 36, 3, stride=2, padding=1)
        self.dropout4=nn.Dropout2d(conv_dropout_rate)
        #self.conv5=nn.Conv2d(48, 48, 3, stride=2, padding=1)
        #self.dropout5=nn.Dropout2d(conv_dropout_rate)

        self.linear1=nn.Linear(7*12*36, 100) #this is different depending on input image size
        self.linear2=nn.Linear(100, 1)

    def num_flat_features(self, x):
        size=x.size()[1:]
        num_features=1
        for s in size:
            num_features*=s
        return num_features

    def forward(self, x):
        x=self.dropout1(F.relu(self.conv1(x)))
        x=self.dropout2(F.relu(self.conv2(x)))
        x=self.dropout3(F.relu(self.conv3(x)))
        x=self.dropout4(F.relu(self.conv4(x)))
        #x=self.dropout5(F.relu(self.conv5(x)))

        x=x.view(-1, self.num_flat_features(x))
        x=F.dropout(F.relu(self.linear1(x)), p=fc_dropout_rate, training=self.training)
        x=self.linear2(x)
        return x


net=Net()
print(net)

