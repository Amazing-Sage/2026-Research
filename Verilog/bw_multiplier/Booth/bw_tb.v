//this is the booth wallace mulitpliers test bench file 
`timescale 1ns / 1ps //defines time unit and precision 
//`include "bw_multiplier.v"
module bw_tb;
    reg enable;
    reg signed [3:0] A;
    reg signed [3:0] B;

    reg signed [7:0] partial0;
    reg signed [7:0] partial1;

    //conect the multiplier 
    bw_multiplier DUT(
        .enable(enable),
        .A(A),
        .B(B),
        .partial0(partial0),
        .partial1(partial1)
    );

    initial begin 
        //enable multiplier 
        enable=1; 

        //test case
        A=4'd3;
        B=4'd2;

        #10;

        $display("A=%d",A);
        $display("B=%d",B);
        $display("partial0=%d", partial0);
        $display("partial1=%d", partial1);

        $finish;

    end


endmodule