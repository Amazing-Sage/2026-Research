#============================================================================================================
#Importing packages and setting up enviroments 
#============================================================================================================

import snntorch as snn
from snntorch import spikeplot as splt
from snntorch import spikegen

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from datasets import load_dataset

import matplotlib.pyplot as plt
import numpy as np
import itertools

# plot settings (copied& from another folder)
import plot_settings as ps

#use this as sub seperator ----------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

#============================================================================================================
#Loading CIFAR-10 datasets 
#============================================================================================================
print("\n\n Loading CIFAR-10...")
print("--------------------------------------------------------------\n")

#dataset= load_dataset("CIFAR10")
#print(dataset)

# dataloader arguments
batch_size = 128
data_path='/tmp/data/CIFAR10'

dtype = torch.float

# Force the network to use the CPU due to hardware mismatch
device = torch.device("cpu")

# Define a transform
transform = transforms.Compose([
            transforms.Resize((28, 28)),
            transforms.Grayscale(),
            transforms.ToTensor(),
            transforms.Normalize((0,), (1,))])

CIFAR10_train= datasets.CIFAR10(data_path,train=True, download=True, transform=transform)
CIFAR10_test= datasets.CIFAR10(data_path,train=False, download=True, transform=True)

#Create DataLoaders 
train_loader= DataLoader(CIFAR10_test, batch_size=batch_size, shuffle=False, drop_last=True)
test_loader= DataLoader(CIFAR10_train, batch_size=batch_size, shuffle=True, drop_last=True)

#============================================================================================================
#Define Layers and LIF
#============================================================================================================
print("\n\n Define Layers and LIF...")
print("--------------------------------------------------------------\n")

# Set up ----------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

# Network Architecture
num_inputs = 28*28 # number of input neurons
num_hidden = 1000 # middle layer of 1k neurons to find patterns in images
num_outputs = 10 #output layer neurons

# Temporal Dynamics
num_steps = 25 #number of steps to un
beta = 0.95 #leak 5% with 95%retained of E charge from one time step 

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        
        self.fc1=nn.Linear(num_inputs,num_hidden)
        self.lif1=snn.Leaky(beta=beta)
        
        self.fc2=nn.Linear(num_hidden,num_outputs)
        self.lif2=snn.Leaky(beta=beta)
    #end of def __init__(self)
        
    def forward(self,x):
        #initialize layers 
        mem1=self.lif1.init_leaky()
        mem2=self.lif2.init_leaky()
        
        #list to record final output layer
        spk2_rec=[]
        mem2_rec=[]
        
        for step in range (num_steps):
            
            #flatten and feed layers 
            cur1= self.fc1(x)
            spk1 , mem1= self.lif(cur1,mem1)
            
            cur2= self.fc1(x)
            spk2 , mem2= self.lif(cur1,mem2)
            
            #record final layer to be used for later 
            spk2_rec.append(spk2)
            mem2_rec.append(mem2)
        return torch.stack(spk2_rec,dim=0), torch.stack(mem2_rec,dim=0)
    
    #end of def forward(self,x)
    
#end of class Net(nn.Module)