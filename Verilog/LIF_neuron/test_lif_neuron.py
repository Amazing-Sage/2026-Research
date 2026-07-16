#this is a file ment to be the python side of cocotb in the bridge between python and verilog 

import cocotb #interacts with verilog module signals 
from cocotb.triggers import Timer, RisingEdge #lets us wait for the clock signal to go from 0 to 1 
from cocotb.clock import Clock # automatically generate clock signal for testbench

from definitions import SCALE, THRESHOLD, LEAK_SHIFT

#hardcode parameters to match definitions.vh
THREASHOLD =768
LEAK_SHIFT = 2
SCALE = 256

@cocotb.test()
#async waits for the simulator clock to run 
async def run_test(dut):
    #start clock so harware can run 
    cocotb.start_soon(Clock(dut.clk,10,units="ns").start())
    
    #reset neuron 
    dut.reset.value =1
    dut.x_in.value=0
    await Timer(25, unit="ns")
    dut.reset.value =0
    
    #feed input of 10
    input_val_1=int(1.5*SCALE)
    dut.x_in.value=input_val_1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    
    #check value of v_mem
    #test line
    dut._log.info(f"At 31ns: reset={dut.reset.value}, x_in={dut.x_in.value}, v_mem={dut.v_mem.value}")
    assert  dut.v_mem.value = input_val_1
    dut.x_in.value= int(2.0*SCALE)
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    
    #check to see if mem_value has spiked by the second clock
    dut._log.info(f"At 51ns: v_mem={dut.v_mem.value}, spike_out={dut.spike_out.value}")
    assert  dut.v_mem.value ==input_val_1
    
    #feed input of 2 into scales Q8.8 fixed point 
    input_val_2 = int(2.0 *SCALE)
    dut.x_in.value = input_val_2
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    
    v_mem_2= input_val_1 - (input_val_1 >> LEAK_SHIFT) + input_val_2 #expected v mem
    dut._log.info(f"At 51ns: v_mem={dut.v_mem.value}, expected={v_mem_2}, spike_out={dut.spike_out.value}")
    
    assert dut.v_mem.value == v_mem_2
    assert dut.v_mem.value >= THREASHOLD
    assert dut.spike_out.value ==1 
    
    #soft reset subtraction on next clock cycle. 
    dut.x_in.value=0
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    
    dut._log.info(f"At 71ns: v_mem={dut.v_mem.value}, spike_out={dut.spike_out.value}")
    assert dut.spike_out.value ==0
    assert dut.v_mem.value==0 #18-15(threashold)=3
    
#end of def run_test 