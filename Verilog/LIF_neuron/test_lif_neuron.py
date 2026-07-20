#this is a file ment to be the python side of cocotb in the bridge between python and verilog 
import sys 
import os 
# Dynamically inject the testbench folder into the python path at runtime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import cocotb #interacts with verilog module signals 
from cocotb.triggers import Timer, RisingEdge #lets us wait for the clock signal to go from 0 to 1 
from cocotb.clock import Clock # automatically generate clock signal for testbench

#from definitions import SCALE, THRESHOLD, LEAK_SHIFT #type :ignore

#hardcode parameters to match definitions.vh
THREASHOLD =768
LEAK_SHIFT = 2
SCALE = 256

#in this code, the 4 bit quantization is done through scaling by multuplying 8 bits (256) by 1-3 to represent it in decimal value

@cocotb.test()
#async waits for the simulator clock to run 
async def run_test(dut):
    
    #start clock so harware can run 
    cocotb.start_soon(Clock(dut.clk,10,units="ns").start())
    
    #reset neuron 
    dut.reset.value =1
    dut.x_in.value=768 #0
    await Timer(25, unit="ns")
    dut.reset.value =0
    
    #feed input of 10
    input_val_1=int(2*SCALE) #2*256 = 512
    dut.x_in.value=input_val_1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    
    #check value of v_mem
    #test line
    dut._log.info(f"At 31ns: reset={dut.reset.value}, x_in={dut.x_in.value}, v_mem={dut.v_mem.value}")
    assert  dut.v_mem.value == input_val_1
    
    input_val_2=int(2.0*SCALE) #2*256 =512
    dut.x_in.value= input_val_2
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    
    #check to see if mem_value has spiked by the second clock
    leak_1= input_val_1 >>LEAK_SHIFT
    v_mem_accumuated= input_val_1-leak_1 +input_val_2 #EXPECTED V MEM(800)
    expected_v_mem_41 = v_mem_accumuated #-THREASHOLD
    
    if expected_v_mem_41 >= THREASHOLD:
        v_mem_accumuated = expected_v_mem_41 -THREASHOLD
    else:
        v_mem_accumuated = expected_v_mem_41
    
    #leak_2= expected_v_mem_41 >> LEAK_SHIFT #expected v mem
    
    dut._log.info(f"At 51ns: v_mem={dut.v_mem.value}, spike_out={dut.spike_out.value}")
    #assert  dut.v_mem.value ==input_val_1
    assert dut. v_mem.value == expected_v_mem_41 #should be 800
    #assert v_mem_accumuated >= THREASHOLD
    assert dut. spike_out.value ==0
    
    #feed input of 2 into scales Q8.8 fixed point 
    #expected_val = int(2.0 *SCALE)
    dut.x_in.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    
    leak_2= v_mem_accumuated >> LEAK_SHIFT #expected v mem
    expected_v_mem_51 = v_mem_accumuated - leak_2 
    
    dut._log.info(f"At 51ns: v_mem={dut.v_mem.value}, expected={expected_v_mem_51}, spike_out={dut.spike_out.value}")
    assert dut.spike_out.value==1
    assert dut.v_mem.value== 96 # use 360 because the v at 51 ns was 480 and the leak is 120 (480/4 or 480 >>2), 480-120=360
    
    #reset before next clock cycle
    dut._log.info(f"At 71ns: v_mem={dut.v_mem.value}, spike_out={dut.spike_out.value}")
    assert dut.spike_out.value ==1
    assert dut.v_mem.value== 96 # use 360 because the v at 51 ns was 480 and the leak is 120 (480/4 or 480 >>2), 480-120=360
    
#end of def run_test 