#============================================================================================================
#Importing packages and setting up enviroments 
#============================================================================================================

import snntorch as snn
from snntorch import spikeplot as splt
from snntorch import spikegen
from snntorch import functional as SF
from snntorch import utils
from snntorch import spikeplot as splt
from snntorch import surrogate
import snntorch.surrogate as surrogate

import torch
import torchinfo
import thop
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

#for NMIST
import tonic
import tonic.transforms as transforms
from torch.utils.data import DataLoader

from datasets import load_dataset

import optuna 
from sklearn.datasets import load_iris
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score

import matplotlib.pyplot as plt
import numpy as np
import itertools

# plot settings (copied& from another folder)
import plot_settings as ps

#import all definitions 
from definitions import set_seed
from definitions import clip_events
from definitions import Net
from definitions import leaky_integrate_and_fire
from definitions import forward_pass
from definitions import generate_hardware_report
from definitions import custom_fast_sigmoid
from definitions import regularization
from definitions import test_set
from definitions import training_loop
from definitions import objective

import sys

#use this as sub seperator ----------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#============================================================================================================
#load seed
#============================================================================================================
#this helps it prevent traing starting from a random place 
#define options
CONFIG = {
    "seed": 42,
    "lr": 5e-4,
    "batch_size":64,
    "beta":0.95,
    "threshold": 0.2,
    "slope": 12.5
}

#configure seed here 
set_seed(CONFIG["seed"])

#============================================================================================================
#Loading Datasets
#============================================================================================================
print("\n\n Datasets..")
print("==============================================================\n")

# dataloader arguments
batch_size = 64
beta=0.95

dtype = torch.float
# Force the network to use the CPU due to hardware mismatch
device = torch.device("cpu")

#use 4 seprate cpu cores to process images in parralel 
num_workers=4

# Define a transform, using data augmentation to help with overfitting
from torchvision import transforms

#check clips and gitter events back into pixle boundary 
#def cliped events 

sensor_size= (34,34,2)

train_transform = tonic.transforms.Compose([
            tonic.transforms.SpatialJitter(sensor_size=sensor_size, var_x=1.0, var_y=1.0),
            clip_events,
            tonic.transforms.RandomFlipLR(sensor_size=sensor_size,p=0.5),
            tonic.transforms.ToFrame(sensor_size=sensor_size, n_time_bins=25)
            ])

test_transform= tonic.transforms.Compose([
    tonic.transforms.SpatialJitter(sensor_size=sensor_size, var_x=1.0, var_y=1.0),
    clip_events,
    tonic.transforms.RandomFlipLR(sensor_size=sensor_size,p=0.5),
    tonic.transforms.ToFrame(sensor_size=sensor_size, n_time_bins=25)
    ])

train_set= tonic.datasets.NMNIST(save_to='./data', train=True, transform=train_transform)
test_set= tonic.datasets.NMNIST(save_to='./data', train=False, transform=test_transform)

#Create DataLoaders 
train_loader= DataLoader(train_set, batch_size=64,shuffle=True, collate_fn=tonic.collation.PadTensors())
test_loader= DataLoader(test_set, batch_size=64,shuffle=False, collate_fn=tonic.collation.PadTensors(),num_workers=0)
# Right after your train_loader and test_loader are defined:
print("--- Data loaders initialized successfully! ---")

#============================================================================================================
#Define Forward Pass
#============================================================================================================
print("\n\n Define Forward Pass...")
print("==============================================================\n")

batch=34
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

#define data and targets
data,targets=next(iter(train_loader))
data=data.to(device)
targets=targets.to(device)

#initalize 
syn,mem=lif1.init_synaptic()
spk_out= torch.zeros(1)

#forward pass definition

net= Net(beta=CONFIG["beta"], slope=CONFIG["slope"], threshold=CONFIG["threshold"])
#run the forward pass 
syn_rec, mem_rec, spk_rec = forward_pass(lif1, net, num_steps, data=spk_in)
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
alpha_mem_rec = []
alpha_spk_rec = []
alpha_spk_in=[]

# run simulation
for step in range(num_steps):
  spk_out, syn_exc, syn_inh, mem = lif2(spk_in[step], syn_exc, syn_inh, mem)
  alpha_mem_rec.append(mem.squeeze(0))
  alpha_spk_rec.append(spk_out.squeeze(0))

#run the forward pass 
syn_rec, mem_rec, spk_rec=forward_pass(lif1,net,num_steps,data=spk_in)

# convert lists to tensors
mem_rec = torch.stack(alpha_mem_rec)
spk_rec = torch.stack(alpha_spk_rec)

#============================================================================================================
#Training Network 
#============================================================================================================
print("\n\n Training Network...")
print("==============================================================\n")

# Define Loss functions -------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
net_model= Net(beta=CONFIG["beta"], slope=CONFIG["slope"], threshold=CONFIG["threshold"]).to(device)

#covert RBG to grayscale so it fits
grayscale_data=data.mean(dim=1)
spk_rec,_=net_model(data)
print("before spk_rec shape:", spk_rec.shape)
print("before spk_rec ndim", spk_rec.ndim)

loss_fn= SF.ce_rate_loss(population_code=False)
#spk_rec=spk_rec.permute(1,0,2,3,4)

print("after spk_rec shape:", spk_rec.shape)
print("after spk_rec dim:", spk_rec.ndim)

#2 class random guess is -ln(0.5)= 0.69 
#(using cross entropy. 0.1 due to 10% chance prob. per class which is 0.69, should be this or less)
print(f"targets", targets.shape)

loss_val = loss_fn(spk_rec, targets)

# Define Gradient Functions ---------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#initialize surrogate gradients 
spike_grad1=surrogate.fast_sigmoid() 
spike_grad2=surrogate.fast_sigmoid()
spike_grad3=surrogate.fast_sigmoid(slope=50)

#define custom surrogate gradient 
spike_grad= surrogate.custom_surrogate(custom_fast_sigmoid)

#adding L1 hyperparameters
l1_alpha=5e-5
l1_loss=0
beta=0.95

num_epoch=10
loss_hist=[]
test_loss_hist=[]
test_indicies=[]
counter=0

optimizer = torch.optim.Adam(net_model.parameters(), lr=1e-4, betas=(0.9, 0.999), weight_decay=1e-4)

# Training Loop and loss function Graph ---------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
# net_model,loss_hist,test_loss_hist,_= training_loop(net_model,optimizer,test_loss_hist,l1_alpha,train_loader, test_loader)
# print("--- Training finished, entering plotting block ---")
# # Your plotting code here...
# # Plot Loss
# test_x_axis=[i*100 for i in range(ln(test_loss_hist))]

# fig = plt.figure(facecolor="w", figsize=(10, 5))
# plt.plot(loss_hist, lable="Train Loss", alpha=0.6)
# plt.plot(test_x_axis, test_loss_hist, lable="Test Loss", linewidth=2)
# plt.title("Loss Curves")
# plt.legend(["Train Loss", "Test Loss"])
# plt.xlabel("Iteration")
# plt.ylabel("Loss")

# plt.savefig("plots/Training and Loss.png", dpi=150, bbox_inches="tight")
# print("\nPlot saved successfully as Training_and_Loss.png")
# plt.show()

net_model, loss_hist, test_loss_hist, _ = training_loop(net_model, optimizer, test_loss_hist, l1_alpha, train_loader, test_loader)
print("--- Training finished, entering plotting block ---")

# 1. Fixed 'ln' to 'len'
test_x_axis = [i * 100 for i in range(len(test_loss_hist))]

fig = plt.figure(facecolor="w", figsize=(10, 5))

# 2. Fixed 'lable' to 'label'
plt.plot(loss_hist, label="Train Loss", alpha=0.6)
plt.plot(test_x_axis, test_loss_hist, label="Test Loss", linewidth=2)

plt.title("Loss Curves")

# 3. Simplified legend call to automatically pull the labels above
plt.legend(loc="upper right") 

plt.xlabel("Iteration")
plt.ylabel("Loss")

plt.savefig("plots/Training and Loss.png", dpi=150, bbox_inches="tight")
print("\nPlot saved successfully as Training_and_Loss.png")
plt.show()

# Weight Behavior Graph Def ---------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#create as a def so it can update in optuna and be placed in objective def
#define objective for optuna as beta and lr and run training loop

#============================================================================================================
#Quantisizing
#============================================================================================================
print("\n\n Quantisizing ...")
print("==============================================================\n")

# Inspection ------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#Find the min and max of the whole network by comparing all of the layers min and max weights 

#weighted_ is refering to every weight in every layer 
weighted_min=float("inf")
weighted_max=float('-inf')

for parameter in net_model.parameters():
    weighted_min= min(weighted_min,parameter.min().item())
    weighted_max= max(weighted_max,parameter.max().item())
        
    #calculate scaling factor, use 15 because there's 15 num_steps in 4 bit integer range 
    #represents 2^4 which is 16 , use 7 because pos nums is (0001-0111) and -8 bc neg nums (1000-1111)
    #-8+7=15 giving us our range 
    S= (weighted_max - weighted_min)/15
#end of for parameter in net_model.parameters()

# Quantisize into 4 bit integers  ---------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

with torch.no_grad():
    for parameter in net_model.parameters():
        #scale weights 
        scaled=parameter/S
        
        #round to nearest integer (whole number)
        rounded=torch.round(scaled)
        
        # clamp values between -8 and 7 to fit 4 bits
        clamped= torch.clamp(rounded, min=-8, max=7)
        
        #overwrite tensors data to fit the 4 bit criteria 
        parameter.copy_(clamped)
        
    # end for parameter in net_model.parameters()
# with torch.no_grad()

# Hardware Report -------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#generate_hardware_report(net_model)

#============================================================================================================
#Optuna Results 
#============================================================================================================

print("\n\n Optuna Results ")
print("==============================================================\n")

#create study object to look for max accuracy 
study = optuna.create_study(direction='maximize') 
#direction='maximize' means higher accuracy means better model

#run optimimization process 
study.optimize(lambda trial: definitions.objective(trial, train_loader, test_loader), n_trials=50)
#n_trials=20 is repeated times of guessing beta and lr

#print best hyper parameters found
print("Best Trial:")
print("_______________________________________________\n")
trial=study.best_trial
print(f"Accuracy: {trial.value}%")

print("\nparameters:")
print("_______________________________________________\n")

for key, value in trial.params.items():
    print(f" {key}: {value}")
#end of for loop 