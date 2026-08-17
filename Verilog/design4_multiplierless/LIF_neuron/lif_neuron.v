// This file is for the core neuron logic (v_mem and stuff)
`timescale 1ns / 1ps
// Paste shared parameters directly into the module namespace
`include "definitions.vh"
//`include "../Memory_till/weight_buff.v"

module lif_neuron #(
    parameter num_inputs =4)(
    input clk, 
    input reset, 
    input wire signed [15:0] x_in, //(16*num_inputs)-1:0 
    
    //neruon1
    output reg spike_out,
    output reg signed [7:0] v_mem,
    output wire signed [3:0] v_mem_bit,
    
    //neruon 2
    output reg spike_out_1,
    output reg signed [7:0] v_mem_1,
    output wire signed [3:0] v_mem_bit_1,

    //loading weights 
    input wire write_en, 
    input wire [3:0]write_addr,
    input wire signed [3:0] w_in_data,

    //read interface (feed neuron) 
    input wire read_en,
    input wire [3:0] read_addr
    
);
wire signed [3:0] w_out_data; //[0:num_inputs-1];
wire signed  [3:0] w_in; //
//sign-extend each 4-bit weight lane from the weight buffer into its 16-bit slot
//(was hardcoded to {num_inputs{4'b0010}}, which ignored the weight buffer entirely)

assign w_in=w_out_data;

reg signed [7:0] v_next_calc;
reg signed [7:0] v_next_calc_1;

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
//declared temp variables neruon 1
reg signed [7:0] v_after_reset;
reg next_spike;
reg signed [7:0] v_next;
reg signed [7:0] sum_temp;
reg signed [7:0] sum_pipeline_reg;
wire signed [7:0] total_sum; //signed keeps negitive numbers out
//scale sum_temp into 16 bits from 32 bits 
assign total_sum = sum_pipeline_reg; //>>> 16;

//declared temp variables neuron 2
reg signed [7:0] v_after_reset_1;
reg next_spike_1;
reg signed [7:0] v_next_1;
reg signed [7:0] sum_temp_1;
reg signed [7:0] sum_pipeline_reg_1;
wire signed [7:0] total_sum_1; //signed keeps negitive numbers out
//scale sum_temp into 16 bits from 32 bits 
assign total_sum_1 = sum_pipeline_reg_1; //>>> 16;

//define clock cycle parameters for refracoring cycles and global clock neuron 1
parameter refract_cycles=4; 
reg signed [3:0] ref_counter; 
reg neuron_update_en_reg;

wire is_refractor; 
wire neuron_update_en; 
wire tile_read_en;
wire mult_en;

assign is_refractor= (ref_counter>0);
//combine multiplier enable and refractory protection 
assign neuron_update_en= mult_en && !is_refractor;

//original wires signed logic is saved on personal notion
wire signed [7:0] bw_products ; // output of each bw multiplier 
//ire signed [7:0] products [0:num_inputs-1]; //expanded products that go into neuron summation 
wire signed [7:0] leak = v_mem >>> `LEAK_SHIFT; 

assign  tile_read_en = (x_in[3:0] !=4'b0000); //only read memory if there's a incoming spike
assign  mult_en = tile_read_en && (w_in !=0);//active high when valid spike input used for zero skipping
//help quantizise into 4 bits and clamp interal 32 bit to 4 bit signed output 
//? checks conition if true consition before : is chosed if not then after 
assign v_mem_bit = ($signed(v_mem) >8'd7) ? 4'd7://upper clamp
                ($signed(v_mem) < -8'd7) ? -4'd8://lower clamp 
                v_mem[3:0]; //sliced 4 bit value

//define clock cycle parameters for refracoring cycles and global clock neuron 2
wire signed [7:0] bw_products_1; // output of each bw multiplier 
reg neuron_update_en_reg_1;
reg signed [3:0] ref_counter_1; 
wire is_refractor_1; 
wire neuron_update_en_1; 
wire tile_read_en_1;
wire mult_en_1;

assign is_refractor_1= (ref_counter_1>0);
//combine multiplier enable and refractory protection 
assign  tile_read_en_1 = (x_in[3:0] !=4'b0000); //only read memory if there's a incoming spike
assign  mult_en_1 = tile_read_en_1 && (w_in !=0);//active high when valid spike input used for zero skipping
//help quantizise into 4 bits and clamp interal 32 bit to 4 bit signed output 
//? checks conition if true consition before : is chosed if not then after 
assign neuron_update_en_1= mult_en && !is_refractor_1;

//wire signed [7:0] products [0:num_inputs-1]; //expanded products that go into neuron summation 
wire signed [7:0] leak_1 = v_mem_1 >>> `LEAK_SHIFT; 

assign v_mem_bit_1 = ($signed(v_mem_1) >8'd7) ? 4'd7://upper clamp
                ($signed(v_mem_1) < -8'd7) ? -4'd8://lower clamp 
                v_mem_1[3:0]; //sliced 4 bit value



bw_multiplier mult(
            .enable(mult_en),
            .A(x_in[3:0]),
            .B(w_in),
            .product(bw_products)
    );

bw_multiplier mult_1(
            .enable(mult_en_1),
            .A(x_in[7:4]),
            .B(w_in),
            .product(bw_products_1)
    );

//assign products= {{24{bw_products[7]}},bw_products};//x_in[(16*i)+:16]*w_in[(16*i)+:16];



//procedural logic////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////
//sum loops for input products neuron 1
always@(*) begin 
    //sum_temp={{8{bw_products[7]}}, bw_products};
    sum_temp=bw_products;
end
//sum loops for input products neuron 2
always@(*) begin 
    //sum_temp={{8{bw_products[7]}}, bw_products};
    sum_temp_1=bw_products_1;
end


//combonational pipeline for membrane pot 1
always @(*) begin 
    v_next_calc =$signed(v_mem) - ($signed(v_mem)>>>`LEAK_SHIFT) +$signed(total_sum);

    //determine spike condition 
    if($signed(v_next_calc) > $signed(`THREASHOLD))begin
        next_spike= 1'b1;
        
        //reset first 
        //v_after_reset=$signed(v_mem) -$signed(`THREASHOLD);

        //after that then leak +integrate
        v_next= $signed(v_next_calc) - $signed(`THREASHOLD);
    end else begin 
        next_spike= 1'b0;

        //v_after_reset=v_mem; 
        v_next= v_next_calc;
        //$signed(v_mem) - ($signed(v_mem) >>> `LEAK_SHIFT) + $signed(total_sum);

       // v_next_calc= v_next; 
    end

   end

//combonational pipeline for membrane pot 2
always @(*) begin 
    v_next_calc_1 =$signed(v_mem_1) - ($signed(v_mem_1)>>>`LEAK_SHIFT) +$signed(total_sum_1);

    //determine spike condition 
    if($signed(v_next_calc_1) > $signed(`THREASHOLD))begin
        next_spike_1= 1'b1;

        //reset first 
       // v_after_reset_1=$signed(v_mem_1) -$signed(`THREASHOLD);

        //after that then leak +integrate
        v_next_1=$signed(v_next_calc_1) - $signed(`THREASHOLD);

       // v_next_calc= v_next; 
    end else begin 
        next_spike_1= 1'b0;

        // v_after_reset_1=v_mem_1; 
        // v_next_1= $signed(v_mem_1) - ($signed(v_mem_1) >>> `LEAK_SHIFT) + $signed(total_sum_1);

        v_next_1= v_next_calc_1;
        //v_next_calc= v_next; 
    end
   end

//single stage pipeline registers after synapse neurons
always@(posedge clk or posedge reset)begin 
    if(reset)begin 
        //neruon 1
        sum_pipeline_reg <=8'd0;
        neuron_update_en_reg<=1'b0; 

        //neuron 2 
        sum_pipeline_reg_1 <= 8'd0;
        neuron_update_en_reg_1 <= 1'b0; 
    end
    else begin 
        //neuron 1
        sum_pipeline_reg <= sum_temp; 
        neuron_update_en_reg <= neuron_update_en;

        //neruon 2
        sum_pipeline_reg_1 <= sum_temp_1; 
        neuron_update_en_reg_1 <= neuron_update_en_1;
    end
end

//neruon 1
always @(posedge clk or posedge reset) begin 
    // $display("clk=%0t x_in=%0d mult_en=%b refractory=%b update=%b total_sum=%0d v_mem=%0d"
    //             ,$time,x_in,mult_en,is_refractor,neuron_update_en,total_sum,v_mem);
    //clock cycles//////////////////////////////////////////////////////
    if(reset)begin 
        v_mem <= 8'b0;   // clear mem pot and carry any left over spiked out of membrane to the next and clear
        spike_out <= 1'b0;
        ref_counter <=4'd0;
    end 
    else if(ref_counter > 0)begin //refractory clamping
        ref_counter <= ref_counter-1'b1;
        //clamp v_mem
        v_mem <=8'b0;//hold clamped during cool down
        spike_out <=1'b0;
    end
    else begin //non refractoring mode
        if (neuron_update_en_reg)begin 
            spike_out <= next_spike;
            //v_mem <= v_next;//normal mem integration

            if (next_spike)begin //|| v_next >= $signed(`THREASHOLD)
            // spike_out<= 1'b1;
                ref_counter <= refract_cycles; 
                v_mem <=v_next;    // SOFT RESET
            end

            else if (v_next < 0)begin
                v_mem <=8'd0;//fix potential bottlenecks that synchronous systems tend to have while also changing out the multiplier to the new one to help 
            end 

            else begin 
                //spike_out<= 1'b0;
                v_mem <= v_next; // add input to prevent underflow
            end 

        end else begin 
            spike_out <=1'b0; //skip update on zero 
            if(v_next < 0)begin 
                v_mem <=8'd0;
            end else begin
            v_mem <= v_next; //leaky membrane pot when mult_en is 0
            end
        end
    end
end

//neruon 2
always @(posedge clk or posedge reset) begin 
    // $display("clk=%0t x_in=%0d mult_en=%b refractory=%b update=%b total_sum=%0d v_mem=%0d"
    //             ,$time,x_in,mult_en,is_refractor,neuron_update_en,total_sum,v_mem);
    //clock cycles//////////////////////////////////////////////////////
    if(reset)begin 
        v_mem_1 <= 8'b0;   // clear mem pot and carry any left over spiked out of membrane to the next and clear
        spike_out_1 <= 1'b0;
        ref_counter_1 <=4'd0;
    end 
    else if(ref_counter_1 > 0)begin //refractory clamping
        ref_counter_1 <= ref_counter_1-1'b1;
        //clamp v_mem
        v_mem_1 <=8'b0;//hold clamped during cool down
        spike_out_1 <=1'b0;
    end
    else begin //non refractoring mode
        if (neuron_update_en_reg_1)begin 
            spike_out_1 <= next_spike_1;
            //v_mem <= v_next;//normal mem integration

            if (next_spike_1)begin //|| v_next >= $signed(`THREASHOLD)
            // spike_out<= 1'b1;
                ref_counter_1 <= refract_cycles; 
                v_mem_1 <=v_next_1;    // SOFT RESET
            end

            else if (v_next_1 < 0)begin
                v_mem_1 <=8'd0;//fix potential bottlenecks that synchronous systems tend to have while also changing out the multiplier to the new one to help 
            end 

            else begin 
                //spike_out<= 1'b0;
                v_mem_1 <= v_next_1; // add input to prevent underflow
            end 

        end else begin 
            spike_out_1 <=1'b0; //skip update on zero 
            if(v_next_1 < 0)begin 
                v_mem_1 <=8'd0;
            end else begin
            v_mem_1 <= v_next_1; //leaky membrane pot when mult_en is 0
            end
        end
    end
end

endmodule
