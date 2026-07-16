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

import sys
import os
import random 

#============================================================================================================
#global variables
#============================================================================================================
# Global configurations
num_epoch = 10  # Or whichever number of epochs you prefer to train for
device = torch.device("cpu")
loss_fn = SF.ce_rate_loss()

# History tracking lists
loss_hist = []
test_loss_hist = []
test_indicies=[]
#============================================================================================================
#set_seed
#============================================================================================================
def set_seed(seed: int):
    #locks down random seeds for reproduibility 
    random.seed(seed)
    os.environ['PYTHONHASHSEED']=str(seed)
    np.random.seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic=True
    torch.backends.cudnn.banchmark=False

#============================================================================================================
#cliped events
#============================================================================================================
def clip_events(events):
    #print("--- Running clip_events ---")
    events_copy=events.copy()
    events['x']= np.clip(events['x'],0,33)
    events['y']= np.clip(events['y'],0,33)
    return events
#end of def clip events 

#============================================================================================================
#Class Net
#============================================================================================================
class Net(nn.Module):
    def __init__(self,beta,slope,threshold):
        super().__init__()
        
        #spike_grad=surrogate.fast_sigmoid(slope=slope)
        spike_grad=surrogate.atan(alpha=2.0)
        
        self.fc1=nn.Linear(2312,128) #takes input, output to fc2
        self.lif1=snn.Leaky(beta=beta,threshold=threshold, spike_grad=spike_grad,reset_mechanism="subtract")
        
        self.fc2= nn.Linear(128,64)#creates final classes with fc1
        self.lif2= snn.Leaky(beta=beta,threshold=threshold, spike_grad=spike_grad,reset_mechanism="subtract")
        
        self.fc3= nn.Linear(64,34)
        self.lif3= snn.Leaky(beta=beta,threshold=threshold, spike_grad=spike_grad,reset_mechanism="subtract")
        
        self.fc4= nn.Linear(34,10)#output layer and how many catagories the dimentions need to be at
        self.lif4=snn.Leaky(beta=beta,threshold=threshold, spike_grad=spike_grad,reset_mechanism="subtract")
        
    #end of def __init__(self)
        
    def forward(self,x,*args):
        # max_val= x.max()
        # if max_val >0:
        #     x=(x/max_val)*2.5
        # # #end of if
        
        num_steps= x.size(1)
        
        #initialize layers 
        mem1=self.lif1.init_leaky()
        mem2=self.lif2.init_leaky()
        mem3=self.lif3.init_leaky()
        mem4=self.lif4.init_leaky()
        
        #list to record final output layer
        spk4_rec=[]
        mem4_rec=[]
        
        #cur1=self.fc1(x)
        num_steps =x.size(1) # re initialize here bc for some reason it keeped going to 64
        
        for step in range (num_steps):
            #flatten and feed layers 
            x_step=x[:,step]
            #steos, : selects 64 samples, ... includes all dimentions
            #if step==0:
                #print ("x_step",x_step.shape)
                
            x_flattened= torch.flatten(x_step, start_dim=1)
            #we only want to calulate this once before the loop
           # if step==0:
                #print ("x_flattened",x_flattened.shape)
                
            cur1= self.fc1(x_flattened)
            #if step==0:
                #print ("cur1",cur1.shape)
             
            spk1 , mem1= self.lif1(cur1,mem1)
            #if step==0:
                #print ("spk1",spk1.shape)
            
            cur2= self.fc2(spk1)
            spk2 , mem2= self.lif2(cur2,mem2)
            
            cur3= self.fc3(spk2)
            spk3 , mem3= self.lif3(cur3,mem3)
            
            cur4= self.fc4(spk3)
            spk4 , mem4= self.lif4(cur4,mem4)
            
            #if step==0:
                #print ("spk4_rec",len(spk4_rec))
            
            #record final layer to be used for later 
            spk4_rec.append(spk4)
            mem4_rec.append(mem4)
            
            #see how much LIF is firing to debug low accuracy 
            #if step ==0:
                #print("-------Step 0 spike counts---------")
                #print(f"LIF1 spikes {spk1.sum().item()}")
                #print(f"LIF4 spikes {spk4.sum().item()}")
                
        return torch.stack(spk4_rec,dim=0), torch.stack(mem4_rec,dim=0)
    
    #end of def forward(self,x)
#end of class Net(nn.Module)

#============================================================================================================
#LIF
#============================================================================================================
def leaky_integrate_and_fire(mem, cur=0,threshold=0.4,time_step=1e-3,R=10, C=5e-3):
    tau_mem=R*C 
    spk=(mem>threshold)
    mem= mem+(time_step/tau_mem)*(-mem + cur*R) - spk*threshold #sub threshold everytime spk=1
    return mem,spk
#end of LIF def

#============================================================================================================
#Forward Pass
#============================================================================================================
def forward_pass(lif1,net,num_steps,data):
    utils.reset(net)
    syn_rec=[]
    mem_rec=[]
    spk_rec=[]
    
    syn, mem = lif1.init_synaptic()
    
    #simpulate neurons 
    for steps in range(num_steps):
        spk_out,syn, mem= lif1(data[steps],syn,mem)
        syn_rec.append(syn)
        mem_rec.append(mem)
        spk_rec.append(spk_out)
    #end for loop 
    
    return torch.stack(syn_rec), torch.stack(mem_rec), torch.stack(spk_rec)
#end of forward_pass

#============================================================================================================
#Generate Hardware Report
#============================================================================================================
def generate_hardware_report(net_model):
    print("\n Hardware Report ...")
    print("_______________________________________________\n")
    
    # print layers memory and parameters
    torchinfo.summary(net_model, input_size=(1,25,2,34,34),device=('cpu'))

    #move to cpu for report 
    #net_model.to("cpu")
    
    #use thop to calculate MAC Operations
    dummy_input= torch.rand(1,25,2,34,34)
    macs, params= thop.profile(net_model, inputs=(dummy_input,))
    print(f"MACS: {macs},  Params:{params}")
#end of def generate_hardware_report(net_model)

#============================================================================================================
#custom fast sigmoid
#============================================================================================================
def custom_fast_sigmoid(input,grad_input, spikes):
    #hyperparameter slope 
    slope=25
    grad= grad_input/ (slope * torch.abs(input)+1.0)**2
    
    return grad 
#end of def custom_fast_sigmoid(input,grad_input, spikes)

#============================================================================================================
#Regularization
#============================================================================================================
def regularization(model:nn.Module, reg_type:str, coef:float):
    int_type=int(reg_type[1])
    reg_loss=0
    
    for param in model.parameters():
        reg_loss+= torch.norm(param, int_type)
    #end for param in module.parameters()
    return reg_loss*coef
#end of def regularization(model:nn.Module, reg_type:str, coef:float)

#============================================================================================================
#test set
#============================================================================================================
def test_set(net_model,test_loss_hist,test_loader):
    #test set
    correct=0
    total=0
    
    with torch.no_grad():
        net_model.eval()
        running_test_loss= 0.0 #test loss for epoch
        
        for test_data, test_targets in test_loader:
           
            #test_data, test_targets= next(iter(test_loader))
            test_data =test_data.to(device)
            test_targets = test_targets.to(device)
            
            actual_time_steps= test_data.size(0)
            
            #test set foward pass 
            test_spk, test_mem= net_model(test_data*5.0,actual_time_steps)
                
            #print to see if network is working and not at 0 -> if test accuracy doesn't change use this
            #print("Total spikes in this batch:", test_spk.sum().item())
               
            #test set loss 
            test_loss = loss_fn(test_spk, test_targets) 
                
            #calculate total accuracy 
            predicted= test_spk.sum(dim=0).argmax(1)
            total +=test_targets.size(0)
            correct +=(predicted == test_targets). sum().item()
        #end for for loop
        
        test_loss_hist.append(test_loss.item())
        accuracy=(correct/total)*100
    #end of with torch.no_grad()
    return net_model,test_loss_hist,accuracy 
#end of def test_set(net_model, optimizer)

#============================================================================================================
#Training Loop
#============================================================================================================
def training_loop(net_model,optimizer,test_loss_hist,l1_alpha, train_loader, test_loader):
    loss_val=0
    counter=0
    
    print("--- Initializing model and preparing loop ---")
    for epoch in range (num_epoch):
        net_model.train()
        
        for data, targets in iter(train_loader):
            counter +=1#increment every batch
            
            data= data.to(device)
            targets= targets.to(device)
            
            #Zero the gradients 
            optimizer.zero_grad()
            #print("zero the gradients")
            
            #premute data for tonic 
            #data= data.permute(1,0,2,3,4)
            actual_time_steps=data.size(0) 
            #print("premute data for tonic ")
            
            #forward pass through 4 layer network 
            spk_rec,_=net_model(data*3, actual_time_steps)
            #print("forward pass through 4 layer network")
            
            #bass loss calculation 
            loss_val =loss_fn(spk_rec, targets)
            #print("CRITICAL CHECK - spk_rec shape is:", spk_rec.shape)
            
            #L1 penalty 
            l1_penalty=regularization(net_model,'l1',l1_alpha)
            total_loss= loss_val + l1_penalty
            
            #backward pass 
            total_loss.backward()
            optimizer.step()
            #print("backward pass")
            
            #append loss history for graphing 
            loss_hist.append(total_loss.item())
            #print("append loss history for graphing")
            
            if counter % 100==0:
                net_model, test_loss_hist, accuracy= test_set(net_model,test_loss_hist,test_loader)
                test_indicies.append(counter) #save iteration number)
                print(f"Iteration{counter}. Test accuracy: {accuracy: .2f}%")
        #end of for data, targets in iter(train_loader) 
        
        # Inside your training loop (for epoch in range...):
        print(f"Epoch {epoch} completed successfully!")
    #end of for epoch in range (num_epoch)
         
    return net_model,loss_hist,test_loss_hist,l1_alpha
#end of def training_loop(net_model, optimizer)

#============================================================================================================
#Optimization in Optuna
#============================================================================================================
def objective(trial, train_loader, test_loader):
    print("--- Optuna Trial Started! ---")
    #clear test loss history to prevent building on old 
    test_loss_hist=[] 
    beta=trial.suggest_float('beta',0.80,0.99) #og at 80 and 90
    lr = trial.suggest_float('lr',1e-3,5e-4,log=True)
    
    #l1 coeff change this to change weight penalty
    l1_lambda= trial.suggest_float('l1_lambda',1e-6,1e-3,log=True)
    
    #tune firing threshold 
    threshold=trial.suggest_float('threshold',0.2,0.2)
    print(f"--- Running Trial {trial.number} | Chosen Threshold: {threshold:.4f} ---")
    
    #tune sharpness from surrogate gradient
    slope=trial.suggest_float('slope',10.0,50.0)# og at 10 to 50
    
    #initialize net and optimizer 
    net=Net(beta=beta,threshold=threshold, slope=slope)
    optimizer=torch.optim.Adam(net.parameters(), lr=lr)
    
    #train model 
    training_net,loss_hist,_, l1_lambda =training_loop(net, optimizer,test_loss_hist,l1_lambda, train_loader, test_loader)
    training_net.eval()
    
    correct=0 
    total=0 
    
    with torch.no_grad():
        for data, targets in test_loader: #val_loader= validation loader 
            
            actual_time_steps= data.size(0)
            #grayscale_data=data.mean(dim=1)
            outputs,_=training_net(data,actual_time_steps)
            
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
    
    #call graph to visualize 
   # weight_behavior(net,trial.number, l1_lambda)
    #best_result=False

    print(f"Trial {trial.number}: Test Accuracy = {accuracy}%")
    
    return accuracy
#end of def objective(trial,epoch)