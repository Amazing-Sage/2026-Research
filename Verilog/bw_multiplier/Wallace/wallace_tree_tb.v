`timescale 1ns / 1ps //defines time unit and precision 

module wallace_tree_tb;
    reg signed[7:0] partial0;
    reg signed[7:0] partial1;

    wire signed[7:0] sum; 
    wire signed[8:0] carry; 

    wallace_tree DUT(
        .partial0(partial0),
        .partial1(partial1),
        .sum(sum),
        .carry(carry)
    );

    initial begin 
        partial0 = 8'b00000111;
        partial1= 8'b00000001;

        #10;

        $display("partial0=%b", partial0);
        $display("partial1=%b", partial1);
        $display("sum=%b", sum);
        $display("carry=%b", carry);

        $finish; 
    end
endmodule