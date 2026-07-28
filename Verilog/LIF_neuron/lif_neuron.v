// This file is for the core neuron logic (v_mem and stuff)
`timescale 1ns / 1ps
// Paste shared parameters directly into the module namespace
`include "definitions.vh"
`include "weight_buff.v"

module lif_neuron #(
    parameter num_inputs =4)(
    input clk, 
    input reset, 
    input wire signed [(16*num_inputs)-1:0] x_in, 
    
    output reg spike_out,
    output reg signed [3:0] v_mem,
    output wire signed [3:0] v_mem_bit,

    //loading weights 
    input wire write_en, 
    input wire [3:0]write_addr,
    input wire signed [3:0] w_in_data,

    //read interface (feed neuron) 
    input wire read_en,
    input wire [3:0] read_addr
    
);
wire signed [3:0] w_out_data;
wire signed [(16*num_inputs)-1:0] w_in;

//intantiation of weight buffers for memory tilling 
weight_buffer uut(
    .clk(clk),
    .reset(reset),
    .write_en(write_en),
    .write_addr(write_addr),
    .w_in_data(w_in_data),
    .read_en(read_en), 
    .read_addr(read_addr),
    .w_out_data(w_out_data)

    );

//inputs into internal wires (for systolic array)///////////////////////////////////////////////
//declared temp variables
reg signed [15:0] v_after_reset;
reg next_spike;
reg signed [31:0] v_next;
reg signed [31:0] sum_temp;
wire signed [31:0] total_sum; //signed keeps negitive numbers out
//scale sum_temp into 16 bits from 32 bits 
assign total_sum = sum_temp; //>>> 16;

//define clock cycle parameters 
parameter refract_cycles=4; 
reg signed [3:0] ref_counter; 

//original wires signed logic is saved on personal notion 
wire signed [31:0] products [0:num_inputs-1]; 
genvar i;
generate
    for (i=0; i<num_inputs; i=i+1)begin :mult_gen;
        assign products[i]= x_in[(16*i)+:16]*w_in[(16*i)+:16];
    end
endgenerate

wire signed [31:0] leak = v_mem >>> `LEAK_SHIFT; 

assign  tile_read_en = (x_in !=0); //only read memory if there's a incoming spike
assign  mult_en = tile_read_en && (w_in !=0);//active high when valid spike input used for zero skipping

//help quantizise into 4 bits and clamp interal 32 bit to 4 bit signed output 
//? checks conition if true consition before : is chosed if not then after 
assign v_mem_bit = ($signed(v_mem) >32'd7) ? 4'd7://upper clamp
                ($signed(v_mem) < -32'd7) ? -4'd8://lower clamp 
                v_mem[3:0]; //sliced 4 bit value
//procedural logic////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////
//sum loops for input products
always@(*) begin : sum_loop
    integer k; 
    sum_temp= 32'd0;
    for (k=0;k<num_inputs;k=k+1) begin
        sum_temp=sum_temp+products[k];
    end
end

//combonational pipeline for membrane pot 
always @(*) begin 
    //determine spike condition 
    if(($signed(v_mem) + $signed(total_sum[17:8])) >= $signed(`THREASHOLD))begin
        next_spike= 1'b1;
    end else begin 
        next_spike= 1'b0;
    end
    //calculate pot after reset 
    if (next_spike)begin 
        v_after_reset=(v_mem -$signed(`THREASHOLD));
    end
    else begin 
        v_after_reset= v_mem;
    end
    //compute next membrane pot 
    v_next =v_after_reset -(v_after_reset >>> `LEAK_SHIFT)+ $signed({8'b0, total_sum[17:8]}); 
end

always @(posedge clk or posedge reset) begin 
    //clock cycles//////////////////////////////////////////////////////
    if(reset)begin 
        v_mem <= 32'b0;   // clear mem pot and carry any left over spiked out of membrane to the next and clear
        spike_out <= 1'b0;
        ref_counter <=4'd0;
    end 
    else if(ref_counter > 0)begin //refractory clamping
        ref_counter <= ref_counter-1'b1;
        //clamp v_mem
        v_mem <=32'b0;//hold clamped during cool down
        spike_out <=1'b0;
    end
    else begin //non refractoring mode
        if (mult_en)begin 
            spike_out <= next_spike;
            //v_mem <= v_next;//normal mem integration
            if (next_spike)begin //|| v_next >= $signed(`THREASHOLD)
            // spike_out<= 1'b1;
                ref_counter <= refract_cycles; 
                v_mem <=v_next -$signed(`THREASHOLD);    // SOFT RESET
            end
            else if (v_next < 0)begin
                v_mem <=32'd0;//fix potential bottlenecks that synchronous systems tend to have while also changing out the multiplier to the new one to help 
            end 
            else begin 
                //spike_out<= 1'b0;
                v_mem <= v_next; // add input to prevent underflow
            end 
        end else begin 
            spike_out <=1'b0; //skip update on zero 
            v_mem <= v_next; //leaky membrane pot when mult_en is 0
        end
    end
end

endmodule