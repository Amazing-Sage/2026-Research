//this if file is used to test the memory till 
`timescale 1ns / 1ps
`include "weight_buff.v"

module tb_weight_buff;
    reg clk;
    reg reset;

    //loading weights 
    reg write_en; 
    reg  [3:0]write_addr;
    reg  [3:0] w_in_data;

    //read interface (feed neuron) 
    reg  read_en;
    reg  [3:0] read_addr;
    wire signed [3:0] w_out_data;

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

    always #5 clk = ~clk; //generate clock signal every 5ns

    //test sequence
    initial begin
        clk =0; 
        reset =1; 
        write_en =0;
        read_en=0; 
        write_addr =0; 
        read_addr =0; 
        w_in_data =0; 
        #20 ;
        reset=0; // relese reset 

        //write a weight 
        write_en = 1'b1;
        write_addr= 4'd0; //adress 0 
        w_in_data = 4'd5; //value 5 
        #10;
        write_en = 1'b0; //turn write enable off
        #20 ;

        //step b read the weight 
        read_en = 1'b1;
        read_addr= 4'b0; 
        #10;
        $display("value read from address 0 = %d", w_out_data);
        read_en = 1'b0;
        
        $finish; 
    end
endmodule