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

import torch
import torchinfo
import thop
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

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

#use this as sub seperator ----------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

#============================================================================================================
#Loading CIFAR-10 datasets 
#============================================================================================================
print("\n\n Loading CIFAR-10...")
print("==============================================================\n")


#dataset= load_dataset("CIFAR10")
#print(dataset)

# dataloader arguments
batch_size = 128
data_path='/tmp/data/CIFAR10'
beta=0.95

dtype = torch.float

# Force the network to use the CPU due to hardware mismatch
device = torch.device("cpu")

#use 4 seprate cpu cores to process images in parralel 
num_workers=4

# Define a transform, using data augmentation to help with overfitting
from torchvision import transforms

transform = transforms.Compose([
            transforms.Grayscale(1),
            transforms.RandomCrop(28),#augmentation (28 x 28)
            transforms.Resize(32), #resize back to 32
            transforms.RandomHorizontalFlip(),#augmentation
            transforms.ToTensor(),
            transforms.Normalize((0,),(1,))])

test_transform= transforms.Compose([
    transforms.ToTensor(), 
    transforms.Normalize((0,),(1,))])


CIFAR10_train= datasets.CIFAR10(data_path,train=True, download=True, transform=transform)
CIFAR10_test= datasets.CIFAR10(data_path,train=False, download=True, transform=test_transform)

#Create DataLoaders 
train_loader= DataLoader(CIFAR10_train, batch_size=batch_size, shuffle=True, drop_last=True, num_workers=num_workers )
test_loader= DataLoader(CIFAR10_test, batch_size=batch_size, shuffle=False, drop_last=False,num_workers=num_workers)

#============================================================================================================
#Define Layers and LIF
#============================================================================================================
print("\n\n Define Layers and LIF...")
print("==============================================================\n")


# Set up ----------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

# Network Architecture
num_inputs = 28*28 # number of input neurons
num_hidden = 1000 # middle layer of 1k neurons to find patterns in images
num_outputs = 10 #output layer neurons

# Temporal Dynamics
num_steps = 25 #number of steps to 

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        
        self.fc1=nn.Linear(1024,64) #takes input, output to fc2
        self.lif1=snn.Leaky(beta=beta)
        
        self.fc2=nn.Linear(num_hidden,num_outputs) #creates final classes with fc1
        self.lif2=snn.Leaky(beta=beta)
    #end of def __init__(self)
        
    def forward(self,x):
        #flatten input from (1,1,32,32) to (1,1024)
        x=torch.flatten(x,start_dim=1)
        
        #initialize layers 
        mem1=self.lif1.init_leaky()
        mem2=self.lif2.init_leaky()
        
        #list to record final output layer
        spk2_rec=[]
        mem2_rec=[]
        
        for step in range (num_steps):
            
            #flatten and feed layers 
            cur1= self.fc1(x)
            spk1 , mem1= self.lif1(cur1,mem1)
            
            cur2= self.fc2(spk1)
            spk2 , mem2= self.lif2(cur2,mem2)
            
            #record final layer to be used for later 
            spk2_rec.append(spk2)
            mem2_rec.append(mem2)
        return torch.stack(spk2_rec,dim=0), torch.stack(mem2_rec,dim=0)
    
    #end of def forward(self,x)
#end of class Net(nn.Module)

# LIF Graph using Lapicqe neuron model ----------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
num_steps=200

#LIF with reset 
def leaky_integrate_and_fire(mem, cur=0,threashold=0.4,time_step=1e-3,R=10, C=5e-3):
    tau_mem=R*C 
    spk=(mem>threashold)
    mem= mem+(time_step/tau_mem)*(-mem + cur*R) - spk*threashold #sub threashold everytime spk=1
    return mem,spk


#create same neuron 
lif2=snn.Lapicque(R=5.1,C=5e-3, time_step=1e-3)

#initialize inputs and outputs 
cur_in=torch.cat((torch.zeros(10,1), torch.ones(190,1)*0.2),0) #change 0.4 to change current
mem=torch.zeros(1)
spk_out=torch.zeros(1)

mem_rec=[mem]
spk_rec=[spk_out]

#run across 100 time steps 
for step in range(num_steps):
    spk_out,mem=lif2(cur_in[step],mem)
    mem_rec.append(mem) 
    spk_rec.append(spk_out)
# end of run across 100 time steps 

#convert list to tensors 
mem_rec=torch.stack(mem_rec) 
spk_rec=torch.stack(spk_rec)


ps.plot_cur_mem_spk(cur_in, mem_rec, spk_rec, thr_line=1, ylim_max2=1.3,
                 title="Lapicque Neuron Model With Periodic Firing")
plt.savefig("plots/Lapicque Neuron Model With Periodic Firing.png", dpi=300, bbox_inches="tight")
print("Plot saved successfully as Lapicque Neuron Model With Periodic Firing.png!")


#============================================================================================================
#Define Forward Pass
#============================================================================================================
print("\n\n Define Forward Pass...")
print("==============================================================\n")


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

#define data and targets
data,targets=next(iter(train_loader))
data=data.to(device)
targets=targets.to(device)

#initalize 
syn,mem=lif1.init_synaptic()
spk_out= torch.zeros(1)


def forward_pass(net,num_steps,data):
    utils.reset(net)
    syn_rec=[]
    mem_rec=[]
    spk_rec=[]
    
    syn, mem = net.init_synaptic()
    
    #simpulate neurons 
    for steps in range(num_steps):
        spk_out,syn, mem= lif1(spk_in[steps],syn,mem)
        syn_rec.append(syn)
        mem_rec.append(mem)
        spk_rec.append(spk_out)
    #end for loop 
    
    return torch.stack(syn_rec), torch.stack(mem_rec), torch.stack(spk_rec)

#run the forward pass 
syn_rec, mem_rec, spk_rec=forward_pass(lif1,num_steps,spk_in)


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
alpha_mem_rec = []
alpha_spk_rec = []
alpha_spk_in=[]

# run simulation
for step in range(num_steps):
  spk_out, syn_exc, syn_inh, mem = lif2(spk_in[step], syn_exc, syn_inh, mem)
  alpha_mem_rec.append(mem.squeeze(0))
  alpha_spk_rec.append(spk_out.squeeze(0))

#run the forward pass 
syn_rec, mem_rec, spk_rec=forward_pass(lif1,num_steps,spk_in)

# convert lists to tensors
mem_rec = torch.stack(alpha_mem_rec)
spk_rec = torch.stack(alpha_spk_rec)

ps.plot_cur_mem_spk(spk_in[:num_steps], mem_rec, spk_rec, "Alpha Neuron Model With Input Spikes")
plt.savefig("plots/Alpha Neuron Model With Input Spikes.png", dpi=300, bbox_inches="tight")
print("Plot saved successfully as Alpha Neuron Model With Input Spikes.png!")


#============================================================================================================
#Training Network 
#============================================================================================================
print("\n\n Training Network...")
print("==============================================================\n")

# Define Loss functions -------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
net_model= Net().to(device)

#covert RBG to grayscale so it fits
grayscale_data=data.mean(dim=1)
spk_rec,_=net_model(grayscale_data.view(batch_size,-1))

loss_fn= SF.ce_rate_loss()
loss_val = loss_fn(spk_rec, targets)

#first run was 4.23 which is higher than Loss= 2.30
#(using cross entropy. 0.1 due to 10% chance prob. per class which is 2.30, should be this or less)
print(f"Loss Value: {loss_val.item()}")

# Loss Function Graph ---------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------



#define hardware report -------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

#print("Model device:", next(net_model.parameters()).device)
#put here because we defined net_model earler and finished that section before defining 
def generate_hardware_report(net_model):
    print("\n Hardware Report ...")
    print("_______________________________________________\n")
    
    # print layers memory and parameters
    torchinfo.summary(net_model, input_size=(1,1,32,32),device=('cpu'))

    #move to cpu for report 
    #net_model.to("cpu")
    
    #use thop to calculate MAC Operations
    dummy_input= torch.rand(1,1,32,32)
    macs, params= thop.profile(net_model, inputs=(dummy_input,))
    print(f"MACS: {macs},  Params:{params}")

#end of def generate_hardware_report(net_model)


# Define Gradient Functions ---------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#initialize surrogate gradients 
spike_grad1=surrogate.fast_sigmoid() 
spike_grad2=surrogate.fast_sigmoid()
spike_grad3=surrogate.fast_sigmoid(slope=50)

#define custom surrogate gradient 

def custom_fast_sigmoid(input,grad_input, spikes):
    #hyperparameter slope 
    slope=25
    grad= grad_input/ (slope * torch.abs(input)+1.0)**2
    
    return grad 
#end of def custom_fast_sigmoid(input,grad_input, spikes)

spike_grad= surrogate.custom_surrogate(custom_fast_sigmoid)

# Gradient Function Graph -----------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------



# Optimization ----------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
#use L1 and L2  along with data augmentation to help help overfitting,
#use l1/l2 because it takes a lot less space and energy 
#data augmentation was defined in "Loading CIFAR-10"

#adding L1 hyperparameters
l1_alpha=1e-5
l1_loss=0
beta=0.95

num_epoch=1
loss_hist=[]
test_acc_hist=[]
counter=0

optimizer = torch.optim.Adam(net_model.parameters(), lr=1e-2, betas=(0.9, 0.999), weight_decay=1e-4)

#this adds l1 and l2 parameter to every layer to the final loss
def regularization(model:nn.Module, reg_type:str, coef:float):
    int_type=int(reg_type[1])
    reg_loss=0
    
    for param in model.parameters():
        reg_loss+= torch.norm(param, int_type)
    #end for param in module.parameters()
    return reg_loss*coef

#end of def regularization(model:nn.Module, reg_type:str, coef:float)

# L1 & L2 Graph ---------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

# Hardware Report -------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
generate_hardware_report(net_model)

# Training Loop (in a definition so it can run in optuna) ---------------------------------------------------
#------------------------------------------------------------------------------------------------------------
def training_loop(net_model,optimizer):
    for epoch in range (num_epoch):
        for data, targets in iter(train_loader):
            #Zero the gradients 
            optimizer.zero_grad()
            
            #forward pass 
            net_model.train()
            
            grayscale_data= data.mean(dim=1)
            spk_rec,_=net_model(grayscale_data.view(data.size(0),-1))
            
            #bass loss calculation 
            loss_val=loss_fn(spk_rec, targets)

            #L1 penalty 
            regularization(net_model,'l1',l1_alpha)
            
            total_loss= loss_val+regularization(net_model,'l1',l1_alpha)
            
            #backward pass 
            total_loss.backward()
            
            #optimizer step 
            optimizer.step()
        #end of for data, targets in iter(train_loader) 
    #end of for epoch in range (num_epoch)
    return net_model
#end of def training_loop(net_model, optimizer)

# Training Loop Graph ---------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------



#define objective for optuna as beta and lr and run training loop
def objective(trial):
    beta=trial.suggest_float('beta',0.5,0.99)
    lr = trial.suggest_float('lr',1e-4,1e-2,log=True)
    
    #initialize net and optimizer 
    net=Net()
    optimizer=torch.optim.Adam(net.parameters(), lr=lr)
    
    #train model 
    training_net =training_loop(net, optimizer)
    training_net.eval()
    
    correct=0 
    total=0 
    
    with torch.no_grad():
        for data, targets in test_loader: #val_loader= validation loader 
            grayscale_data=data.mean(dim=1)
            outputs,_=training_net(grayscale_data.view(data.size(0),-1))
            
            #compress the 64 time step 
            outputs_sum= outputs.sum(dim=0)
            
            #predict class index 
            _,predicted= torch.max(outputs_sum.data,1) 
            
            #count total items and correct predictions 
            total += targets.size(0)
            correct +=(predicted==targets).sum().item()
        #end of for for data, targets in val_loader:
    
    #run training loop function and get a score 
    accuracy=100 *correct/total
    
    return accuracy
#end of def objective(trial)


# Hardware Report -------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
generate_hardware_report(net_model)

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

# 
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
generate_hardware_report(net_model)


#============================================================================================================
#Optuna Results 
#============================================================================================================

print("\n\n Optuna Results ")
print("==============================================================\n")

#create study object to look for max accuracy 
study = optuna.create_study(direction='maximize') 
#direction='maximize' means higher accuracy means better model

#run optimimization process 
study.optimize(objective, n_trials=20)
#n_trials=20 is repeated times of guessing beta and lr

#print best hyper parameters found
print("Best Trial:")
print("_______________________________________________\n")
trial=study.best_trial
print(f"Accuracy: {trial.value}%")

print("\nparameters:")
print("_______________________________________________\n")

for key, value in trial.params.items():
    print(f"    {key}: {value}")