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
        self.conv1=nn.Conv2d(3, 24, 5, stride=2, padding=2)
        self.dropout1=nn.Dropout2d(conv_dropout_rate)
        self.conv2=nn.Conv2d(24, 32, 5, stride=2, padding=2)
        self.dropout2=nn.Dropout2d(conv_dropout_rate)
        self.conv3=nn.Conv2d(32, 40, 5, stride=2, padding=2)
        self.dropout3=nn.Dropout2d(conv_dropout_rate)
        self.conv4=nn.Conv2d(40, 48, 3, stride=2, padding=1)
        self.dropout4=nn.Dropout2d(conv_dropout_rate)
        self.conv5=nn.Conv2d(48, 48, 3, stride=2, padding=1)
        self.dropout5=nn.Dropout2d(conv_dropout_rate)

        self.linear1=nn.Linear(2*4*48, 100)
        self.linear2=nn.Linear(100, 1)

    def num_flat_features(self, x):
        size=x.size()[1:]
        num_features=1
        for s in size:
            num_features*=s
        return num_features

    def forward(self, x):
        '''
        x=self.dropout1(F.elu(self.conv1(x)))
        x=self.dropout2(F.elu(self.conv2(x)))
        x=self.dropout3(F.elu(self.conv3(x)))
        x=self.dropout4(F.elu(self.conv4(x)))
        x=self.dropout5(F.elu(self.conv5(x)))
        '''
        x=F.dropout(F.elu(self.conv1(x)), p=fc_dropout_rate, training=self.training)
        x=F.dropout(F.elu(self.conv2(x)), p=fc_dropout_rate, training=self.training)
        x=F.dropout(F.elu(self.conv3(x)), p=fc_dropout_rate, training=self.training)
        x=F.dropout(F.elu(self.conv4(x)), p=fc_dropout_rate, training=self.training)
        x=F.dropout(F.elu(self.conv5(x)), p=fc_dropout_rate, training=self.training)
        x=x.view(-1, self.num_flat_features(x))
        x=F.dropout(F.elu(self.linear1(x)), p=fc_dropout_rate, training=self.training)
        x=self.linear2(x)
        return x


net=Net()
print(net)

