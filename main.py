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

#============================================================================================================
#Define Forward Pass
#============================================================================================================
print("\n\n Define Forward Pass...")
print("--------------------------------------------------------------\n")

batch=32
num_hidden=64


# synaptic Neuron--------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

alpha=0.9
beta=0.8
num_steps=64 #(look back to see if this is a good value or not)

#ininitialize LIF
lif1=snn.Synaptic(alpha=alpha, beta=beta)

#period spiking
w=0.2 #0.2v

spk_period=torch.cat((torch.ones(1)*w, torch.zeros(9)),0)
spk_in=spk_period.repeat(20)

#initalize 
syn,mem=lif1.init_synaptic()
spk_out= torch.zeros(1)

syn_rec=[]
mem_rec=[]
spk_rec=[]

#simpulate neurons 
for steps in range(num_steps):
    spk_out,syn, mem= lif1(spk_in[steps],syn,mem)
    syn_rec.append(syn)
    mem_rec.append(mem)
    spk_rec.append(spk_out)
#end for loop 

#convert list to tensors 
syn_rec=torch.stack(syn_rec) 
mem_rec=torch.stack(mem_rec) 
spk_rec=torch.stack(spk_rec) 

#plot synaptic neurons 
ps.plot_cur_mem_spk(syn_rec, mem_rec, spk_rec, title="Synaptic Neuron Model With Input Spikes")
plt.savefig("plots/Synaptic Neuron Model With Input Spikes.png", dpi=300, bbox_inches="tight")
print("Plot saved successfully as Synaptic Neuron Model With Input Spikes.png!")

# Alpha Neuron-----------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

#initalize neuron 
lif2= snn.Alpha(alpha=alpha, beta=beta)

#input spike and period spiking 
w=0.85
spk_in = (torch.cat((torch.zeros(10), torch.ones(1), torch.zeros(89),
                    (torch.cat((torch.ones(1), torch.zeros(9)),0).repeat(10))), 0) * w).unsqueeze(1)

# initialize parameters
syn_exc, syn_inh, mem = lif2.init_alpha()
mem_rec = []
spk_rec = []

# run simulation
for step in range(num_steps):
  spk_out, syn_exc, syn_inh, mem = lif2(spk_in[step], syn_exc, syn_inh, mem)
  mem_rec.append(mem.squeeze(0))
  spk_rec.append(spk_out.squeeze(0))

# convert lists to tensors
mem_rec = torch.stack(mem_rec)
spk_rec = torch.stack(spk_rec)

ps.plot_cur_mem_spk(spk_in, mem_rec, spk_rec, "Alpha Neuron Model With Input Spikes")
plt.savefig("plots/Alpha Neuron Model With Input Spikes.png", dpi=300, bbox_inches="tight")
print("Plot saved successfully as Alpha Neuron Model With Input Spikes.png!")


#============================================================================================================
#Training Loop
#============================================================================================================
print("\n\n Training Loop...")
print("--------------------------------------------------------------\n")