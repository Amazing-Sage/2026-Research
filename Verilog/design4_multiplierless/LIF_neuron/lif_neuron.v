// This file is for the core neuron logic (v_mem and stuff)
`timescale 1ns / 1ps
// Paste shared parameters directly into the module namespace
`include "definitions.vh"
//`include "../Memory_till/weight_buff.v"

module lif_neuron #(
    parameter num_inputs =4)(
    input clk, 
    input reset, 
    input wire signed [(16*num_inputs)-1:0] x_in, 
    
    output reg spike_out,//neuron 0
    output reg signed [7:0] v_mem,// neuron 0
    output wire signed [3:0] v_mem_bit,

    //second neurons 
    output reg signed [7:0] v_mem_1,
    output reg spike_out_1,

    //loading weights 
    input wire write_en, 
    input wire [3:0]write_addr,
    input wire signed [3:0] w_in_data,

    //read interface (feed neuron) 
    input wire read_en,
    input wire [3:0] read_addr
    
);
//second neuron 

reg neuron_sel;//selects wether or not working on neuron 0 or 1 
wire signed [7:0] v_mem_sel; 
assign v_mem_sel = neuron_sel_pipe ? v_mem_1 :v_mem; // connect neurons to mem state only
//allows one shared arithmitic datapath to recive either neurons mem pot 

wire signed [3:0] w_out_data; //[0:num_inputs-1];
wire signed  [3:0] w_in; //
//sign-extend each 4-bit weight lane from the weight buffer into its 16-bit slot
//(was hardcoded to {num_inputs{4'b0010}}, which ignored the weight buffer entirely)
assign w_in=w_out_data;
reg signed [7:0] v_next_calc;


//intantiation of weight buffers for memory tilling 
weight_buffer #(
    .num_inputs(num_inputs)
    )uut(
    .clk(clk),
    .reset(reset),
    .write_en(write_en),
    .write_addr(write_addr),
    .w_in_data(w_in_data),
    .read_en(read_en), 
    .read_addr(read_addr),
    .w_out_data(w_out_data)

    );

//inputs into internal wires (for bw multiplier)///////////////////////////////////////////////
//declared temp variables
reg signed [7:0] v_after_reset;
reg next_spike;
reg signed [7:0] v_next;
reg signed [7:0] sum_temp;
wire signed [7:0] total_sum; //signed keeps negitive numbers out
//scale sum_temp into 16 bits from 32 bits 
assign total_sum = sum_temp; //>>> 16;

//define clock cycle parameters for refracoring cycles and global clock
parameter refract_cycles=4; 
reg signed [3:0] ref_counter; 
reg signed [3:0] ref_counter_1; 

wire is_refractor; 
wire neuron_update_en; 
wire tile_read_en;
wire mult_en;
//shared neurons refractory 
wire signed [3:0] ref_counter_sel; 
assign ref_counter_sel= neuron_sel_pipe ?ref_counter_1:ref_counter;

//assign regesters for breaking up crit path
reg signed [7:0] total_sum_pipe; 
reg mult_en_pipe;
reg neuron_sel_pipe;
// reg is_refractor_pipe;
// reg neuron_sel_mem_pipe;

assign is_refractor= (ref_counter_sel>0);
//combine multiplier enable and refractory protection 
assign neuron_update_en= mult_en_pipe && !is_refractor;


//original wires signed logic is saved on personal notion
wire signed [7:0] bw_products ; // output of each bw multiplier 
//ire signed [7:0] products [0:num_inputs-1]; //expanded products that go into neuron summation 
wire signed [7:0] leak = v_mem_sel >>> `LEAK_SHIFT; 

assign  tile_read_en = (x_in[0]); //only read memory if there's a incoming spike
assign  mult_en = tile_read_en && (w_in !=0);//active high when valid spike input used for zero skipping
//help quantizise into 4 bits and clamp interal 32 bit to 4 bit signed output 
//? checks conition if true consition before : is chosed if not then after 
assign v_mem_bit = ($signed(v_mem) >8'd7) ? 4'd7://upper clamp
                ($signed(v_mem) < -8'd7) ? -4'd8://lower clamp 
                v_mem[3:0]; //sliced 4 bit value


// bw_multiplier mult(
//             .enable(mult_en),
//             .A(x_in[3:0]),
//             .B(w_in),
//             .product(bw_products)
//     );

assign bw_products= x_in[0]? {{4{w_in[3]}},w_in} :8'd0;
//assign bw_products= mult_en? {{4{w_in[3]}},w_in} :8'd0;


//procedural logic////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////
//sum loops for input products
always@(*) begin 
    //sum_temp={{8{bw_products[7]}}, bw_products};
    sum_temp=bw_products;
end
// always@(posedge clk or posedge reset)begin 
//     if(reset)begin
//         sum_temp <=32'd0;
//     end 
//     else if(mult_en) begin 
//         sum_temp <= sum_temp+{{24{bw_products[7]}},bw_products};
//     end
// end

// register to break crit path (refracory)
always @(posedge clk or posedge reset)begin 
    if(reset)begin
        total_sum_pipe <=8'd0;
        mult_en_pipe <=1'b0; 
        neuron_sel_pipe <= 1'b0;
        //neuron_sel_mem_pipe <=1'b0; 
    end 
    else begin
        total_sum_pipe <=total_sum;
        mult_en_pipe <=mult_en;
        neuron_sel_pipe <= neuron_sel;
        //neuron_sel_mem_pipe <= neuron_sel;
        //is_refractor_pipe <= (neuron_sel ? (ref_counter_1>0) :(ref_counter>0));
    end
end
//combonational pipeline for membrane pot 
always @(*) begin 
    //v_next_calc =$signed(v_mem) - $signed(leak) +$signed(total_sum);

    //determine spike condition 
    if(($signed(v_mem_sel)+ $signed(total_sum_pipe)) > $signed(`THREASHOLD))begin
        next_spike= 1'b1;

        //reset first 
        v_after_reset=$signed(v_mem_sel) + $signed(total_sum_pipe) -$signed(`THREASHOLD);

        //after that then leak +integrate
        v_next= $signed(v_after_reset) - ($signed(v_after_reset) >>> `LEAK_SHIFT);// + $signed(total_sum);

        v_next_calc= v_next; 

    end else begin 
        next_spike= 1'b0;

        v_after_reset=v_mem_sel; 
        v_next= $signed(v_mem_sel) - ($signed(v_mem_sel) >>> `LEAK_SHIFT) + $signed(total_sum_pipe);

        v_next_calc= v_next; 

    end
    $display("v_mem=%d total_sum=%d v_next=%d next_spike=%b",$signed(v_mem),$signed(total_sum_pipe),$signed(`THREASHOLD),$signed(v_after_reset),$signed(v_next), next_spike);
end

always @(posedge clk or posedge reset) begin 
    // $display("clk=%0t x_in=%0d mult_en=%b refractory=%b update=%b total_sum=%0d v_mem=%0d"
    //             ,$time,x_in,mult_en,is_refractor,neuron_update_en,total_sum,v_mem);
    //clock cycles//////////////////////////////////////////////////////
    if(reset)begin 
        //reset either neuron 0 or 1
        v_mem <= 8'b0;
        v_mem_1 <= 8'b0;   // clear mem pot and carry any left over spiked out of membrane to the next and clear
        spike_out <= 1'b0;
        spike_out_1 <= 1'b0;
        ref_counter <=4'd0;
        ref_counter_1 <=4'd0;

        //start with neuron 0 selected
        neuron_sel <=1'b0;
        
    end 
    
    else begin //non refractoring mode
        //default to spiking low
        spike_out <= 1'b0;
        spike_out_1 <=1'b0;
        if(neuron_sel_pipe == 1'b0)begin //refractory clamping
            //neuron 0
            if(ref_counter >0)begin
                ref_counter <= ref_counter -1'b1;
                v_mem <= 8'd0; 
            end else if (neuron_update_en) begin
                spike_out <= next_spike;

                if(next_spike) begin
                    ref_counter <=refract_cycles;
                    v_mem <= v_next;
                end
                else if(v_next <0)begin 
                    v_mem <= 8'd0;
                end
                else begin 
                    v_mem <= v_next;
                end
            end
            else begin 
                if(v_next <0)begin
                    v_mem <=8'd0; 
                end 
                else begin 
                    v_mem <= v_next;
                end
            end
        end
        else begin
            //neuron 1
            if(ref_counter_1 >0)begin
                ref_counter_1 <= ref_counter_1 -1'b1;
                v_mem <= 8'd0; 
            end else if (neuron_update_en) begin
                spike_out_1 <= next_spike;

                if(next_spike) begin
                    ref_counter_1 <=refract_cycles;
                    v_mem_1 <= v_next;
                end
                else if(v_next <0)begin 
                    v_mem_1 <= 8'd0;
                end
                else begin 
                    v_mem_1 <= v_next;
                end
            end
            else begin 
                if(v_next <0)begin
                    v_mem_1 <=8'd0; 
                end 
                else begin 
                    v_mem_1 <= v_next;
                end
            end
        end
        
        neuron_sel <=~neuron_sel;// this is the selector toggle inn clocked logic
    end
end
// always@(v_mem)begin
//     $display("v_mem updated = %d at time%0t", v_mem,$time);
// end
endmodule
