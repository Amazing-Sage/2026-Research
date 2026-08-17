#this is a file ment to be the python side of cocotb in the bridge between python and verilog 
import sys 
import os 
# Dynamically inject the testbench folder into the python path at runtime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import cocotb #interacts with verilog module signals 
from cocotb.triggers import Timer, RisingEdge, ReadOnly #lets us wait for the clock signal to go from 0 to 1 
from cocotb.clock import Clock # automatically generate clock signal for testbench

# Go up two folder levels to reach the PyTorch directory 
pytorch_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..","..", "PyTorch")
)
# sys.path.append(pytorch_dir)
# print("PyTorch path:", pytorch_dir)
# from definitions import sim_lif

#from definitions import SCALE, THRESHOLD, LEAK_SHIFT #type :ignore
#hardcode parameters to match definitions.vh
THREASHOLD = 10
LEAK_SHIFT = 2
SCALE = 256

#in this code, the 4 bit quantization is done through scaling by multuplying 8 bits (256) by 1-3 to represent it in decimal value
@cocotb.test()
#async waits for the simulator clock to run 
async def run_test(dut):
    #initialize control signals 
    dut.write_en.value=0
    dut.write_addr.value=0
    dut.w_in_data.value =0
    dut.read_en.value=0
    dut.read_addr.value=0
    
    
    #start clock so harware can run 
    cocotb.start_soon(Clock(dut.clk,10,units="ns").start())
    
    # run pytorch comparison 
    py_vmem=0
    py_ref=0
    inputs_1=[5,5,0,5,0] # values sent to each of the 4 channels per cycle
    #neruon 2 
    py_vmem_1=0
    py_ref_1=0
    inputs_2=[2,2,0,2,0]
    
    
    
    #apply reset to hardware 
    dut.reset.value =0
    await RisingEdge(dut.clk)
    dut.reset.value=1
    
    #reset neuron 
    dut.reset.value =1
    dut.x_in.value=0 #768
    #dut. w_in.value=0
    #await Timer(20, unit="ns")
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value =0
    
    #below are our synapses weights 
    #weights initialized 
    # w3,w2,w1,w0= 2,2,2,2
    # dut.w_in.value= (w3<<48) | (w2<<32) |(w1<<16) | w0
    dut.write_en.value=1
    dut.write_addr.value= 0
    dut.w_in_data.value= 5
    await RisingEdge(dut.clk)
    dut.write_en.value= 0
    
    dut.read_en.value= 1
    dut.read_addr.value= 0
    await RisingEdge(dut.clk)
    dut.read_en.value= 0
    await Timer(1,unit="ns")
    
    #
        
    #start test loop 
    for i, (input_1,input_2) in enumerate(zip(inputs_1,inputs_2)):
        #apply x in neuron 1 and 2
        #input for one logical neuron cycle
        dut.x_in.value= ((input_2 & 0xF) <<4) | (input_1 & 0xF)
            
        #update inputs 
        # dut.input_val.value
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        
        #update python refrence model 
        total_sum_1 =5 * input_1
        total_sum_2 =5 * input_2
        
        # py_vmem, py_spk, py_ref = sim_lif (
        #         py_vmem, py_ref, total_sum_1, threshold=THREASHOLD, leak_shift=LEAK_SHIFT
        #         )
        
        # py_vmem_1, py_spk_1, py_ref_1 = sim_lif (
        #         py_vmem_1, py_ref_1, total_sum_2, threshold=THREASHOLD, leak_shift=LEAK_SHIFT
        #         )
        
        dut._log.info(
            f"Loop {i}: "
            f"N1 RTL= {dut.v_mem.value.to_signed()},{int(dut.spike_out.value)} |"
            f"N2 RTL= {dut.v_mem_1.value.to_signed()},{int(dut.spike_out_1.value)} |"
            )
                
        #assert hardware matches to refrence model 
        # assert dut.v_mem.value.to_signed() == py_vmem
        # assert dut.spike_out.value == py_spk
        
        # assert dut.v_mem_1.value.to_signed() == py_vmem_1
        # assert dut.spike_out_1.value == py_spk_1
    #end of forloop
    
    ##the rest after this test the v mem at a specific clock cycle to make sure its accumulating 
# # ---------------------------------------------------------------------------------------------------------
# # 31ns Cycle: Accumulate second input
# # ---------------------------------------------------------------------------------------------------------
    
#     #feed input of 10
#     input_val_1=int(2*SCALE) #2*256 = 512
#     # dut.x_in.value=input_val_1
#     val_per_channel = 64
#     dut.x_in.value =(val_per_channel <<48) | (val_per_channel<<32) | (val_per_channel <<16) | val_per_channel
    
#     await RisingEdge(dut.clk)
#     await Timer(1, unit="ns")
    
#     await RisingEdge(dut.clk)
#     await Timer(1, unit="ns")
    
#     dut._log.info(f"After extra cycle: v_mem={dut.v_mem.value.to_signed()}")
    
#     #check value of v_mem
#     #test line
#     dut._log.info(f"At 31ns: reset={dut.reset.value}, x_in={dut.x_in.value}, v_mem={dut.v_mem.value.to_signed()}")
#     #assert  dut.v_mem.value.to_signed() == 4 #input_val_1, use 2 because 512/256= 2  which is our sum 4 channels/ 4 bits
    
# # ---------------------------------------------------------------------------------------------------------
# # 41ns Cycle: Accumulate second input
# # ---------------------------------------------------------------------------------------------------------
  
#     input_val_2= 2 #int(2.0*SCALE) #2*256 =512
#     val_per_channel = 64
#     dut.x_in.value =((val_per_channel <<48) | (val_per_channel<<32) | (val_per_channel <<16) | val_per_channel)

#     #check to see if mem_value has spiked by the second clock
#     prev_v = dut.v_mem.value.to_signed()
#     await RisingEdge(dut.clk)
#     await Timer(1, unit="ns")
    
#     expected_v_mem_41 = prev_v - (prev_v >> LEAK_SHIFT) + 2 
#     v_mem_accumuated = expected_v_mem_41
    
#     dut._log.info(f"At 41ns: v_mem={dut.v_mem.value}, spike_out={dut.spike_out.value}")
#     assert dut.v_mem.value.to_signed() == expected_v_mem_41
# # ---------------------------------------------------------------------------------------------------------
# # 51ns Cycle: Accumulate second input
# # ---------------------------------------------------------------------------------------------------------
  
#     #assert  dut.v_mem.value ==input_val_1
#     assert dut. v_mem.value.to_signed() == expected_v_mem_41 #should be 800
#     #assert v_mem_accumuated >= THREASHOLD
#     assert dut. spike_out.value ==0
    
#     #feed input of 2 into scales Q8.8 fixed point 
#     #expected_val = int(2.0 *SCALE)
#     dut.x_in.value = 0
#     await RisingEdge(dut.clk)
#     #await RisingEdge(dut.clk)
#     await Timer(1, unit="ns")
    
#     leak_2= v_mem_accumuated >> LEAK_SHIFT #expected v mem
#     expected_v_mem_51 = v_mem_accumuated - leak_2 #4
    
#     dut._log.info(f"At 51ns: v_mem={dut.v_mem.value}, expected={expected_v_mem_51}, spike_out={dut.spike_out.value}")
#     assert dut.spike_out.value ==0 # 0 because it shouldn't be at 4 yet
#     assert dut.v_mem.value.to_signed()== expected_v_mem_51 # use 360 because the v at 51 ns was 480 and the leak is 120 (480/4 or 480 >>2), 480-120=360
# # ---------------------------------------------------------------------------------------------------------
# # 71ns Cycle: Accumulate second input
# # ---------------------------------------------------------------------------------------------------------
  
#     #reset before next clock cycle
#     dut._log.info(f"At 71ns: v_mem={dut.v_mem.value}, spike_out={dut.spike_out.value}")
#     assert dut.spike_out.value ==0 # 0 because it shouldn't be at 4 yet
#     assert dut.v_mem.value.to_signed()== expected_v_mem_51  #3 # use 360 because the v at 51 ns was 480 and the leak is 120 (480/4 or 480 >>2), 480-120=360
    
#     #reset signal active 
#     dut.reset.value=1
    
#     #wait for one cycle to let reset happen 
#     await RisingEdge(dut.clk)
#     await Timer(1,unit="ns")
    
#     #de assert reset so neuron can resume normaly
#     dut.reset.value=0
    
#     dut._log.info(f"After reset cycle: v_mem={dut.v_mem.value.to_signed()}, spike_out={dut.spike_out.value}")
#     assert dut.v_mem.value.to_signed() == 0, f"Expected v_mem to reset to 0, but got {dut.v_mem.value.to_signed()}"
    
#     #drive large input values to trigger a spike
#     val_per_channel= 10000
#     dut.x_in.value =(val_per_channel <<48) | (val_per_channel<<32) | (val_per_channel <<16) | val_per_channel
    
#     #advance to next clock edge for neuron process the input
#     print("--- TESTING CLOCK ADVANCE ---")
#     await RisingEdge(dut.clk)
#     #await Timer(1,unit="ns")

#    # await RisingEdge(dut.clk)
#     await ReadOnly()
    
#     #spike is 1 in binnary
#     assert dut.spike_out.value ==1
#     await Timer(1,unit="ns")
    
#     #clear inputs for refrac test 
#     dut.x_in.value = 0

#     #run test clock cycles------------------------------------
#     for cycle in range(4):
#         print(f"Cycle {cycle} at {cocotb.utils.get_sim_time('ns')}ns: v_mem = {dut.v_mem.value.to_signed()}, spike_out = {dut.spike_out.value}")
        
#         await RisingEdge(dut.clk)
#         await Timer(1,unit="ns")
        
#         assert dut.v_mem.value.to_signed() == 0
#         assert dut.spike_out.value ==0
        
#         print (f"Cycle {cycle}: Expected v_mem=0 during refractory, got {dut.v_mem.value.to_signed()}")
# #end of def run_test 
