//this file is the test bench of the lif_neuron file
//using cocotb to test lif which is a bridge between python and verilog, this is the verilog bridge
`timescale 1ns / 1ps //defines time unit and precision 
`include "2026-Research/Verilog/LIF_neuron/lif_neuron.v"

module tb_lif_neuron; 

    //declare signals to connect the neurons 
    reg clk; 
    reg reset;
    reg [3:0] x_in;
    wire [7:0] v_mem; 
    wire spike_out; 
    
    // plug in the neuron device under test (DUT) 
    lif_neuron dut(
        .clk(clk),
        .reset(reset),
        .x_in(x_in),
        .v_mem(v_mem),
        .spike_out(spike_out) 
    );

    //simulation logic 
    always #10 clk = ~clk;

    initial begin 
        //run on GTK wave 

        // Add these two lines to save the simulation data:
        $dumpfile("lif_simulation.vcd");
        $dumpvars(0, tb_lif_neuron);

        // Your existing initialization code...
        clk = 0;
        reset = 1;
        // ... rest of the testbench code ...

        //initialize signals
        clk=0;
        reset=1; 
        x_in=4'd0;
        #20;

        //release reset and apply constant input current of 15 
        reset=0; 
        x_in=4'd15;

        //run simulation fo r300 time units 
        #300; 
        $finish; 
    end


endmodule
