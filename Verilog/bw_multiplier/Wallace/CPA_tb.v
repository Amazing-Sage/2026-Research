`timescale 1ns / 1ps //defines time unit and precision 
module CPA_tb;
    reg signed [7:0] sum;
    reg signed [8:0] carry; 

    wire signed[7:0] product;

    CPA DUT(
        .sum(sum),
        .carry(carry),
        .product(product)
    );

    initial begin
        sum= 8'b00000000;
        carry= 9'b00000100;

        #10; 

        $display("sum=%b", sum);
        $display("carry=%b", carry);
        $display("product=%b", product);

        $finish;
    end 
endmodule
