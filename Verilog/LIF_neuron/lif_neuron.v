// This file is for the core neuron logic (v_mem and stuff)
`timescale 1ns / 1ps

module lif_neuron(
    input clk, 
    input reset, 
    input wire signed [15:0] x_in, 
    output reg spike_out,
    output reg signed [15:0] v_mem
);

// Paste shared parameters directly into the module namespace
`include "definitions.vh"

//declared temp variables
reg signed [15:0] v_after_reset; 
reg  next_spike;

always @(posedge clk) begin 
    //hardware updates here 
    if(reset == 1'b1 )begin 
        v_mem <= 16'b0000;   // clear mem pot and carry any left over spiked out of membrane to the next and clear
        spike_out <= 1'b0;
    end 
    else begin
        //determine if we spiked or not in past and calculate mem pot 
        
        next_spike =(v_mem >= `THREASHOLD); //768 converted from floating point 3, 3*256=768 (16'd768)
        v_after_reset= next_spike ? (v_mem -`THREASHOLD):v_mem; //? and : make up conditional operator (single line if else)
        // v_mem <= v_mem - `THREASHOLD;   // clear mem pot 
        // spike_out <= 1'b1;

        // neuron not reseting we add new incoming signals to current value
        // here we also add a -1 to on every clock cycle so the charge decays over time 
        if (v_mem > 0)begin
            v_mem <=v_mem -(v_after_reset >>> `LEAK_SHIFT)+x_in; 

        end else begin 
            v_mem <= v_after_reset + x_in; // add input to prevent underflow
            //spike_out <=0;
        end 
        spike_out<= next_spike;
    end
end

endmodule