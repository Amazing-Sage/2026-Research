//this is the booth wallace mulitpliers test bench file 
`timescale 1ns / 1ps //defines time unit and precision 
//`include "bw_multiplier.v"
module bw_tb;
    reg enable;
    reg signed [3:0] A;
    reg signed [3:0] B;

    wire signed [7:0] product;

    integer i;
    integer j;

    integer correct; 
    integer total; 
    real accuracy; 
    
    reg signed [7:0] expected;

    //conect the multiplier 
    bw_multiplier DUT(
        .enable(enable),
        .A(A),
        .B(B),
        .product(product)
    );

    initial begin 
        ///waveform generatator
        $dumpfile("bw_multiplier.vcd");
        $dumpvars(0,bw_tb);
    end
    
    initial begin 
        enable=1; 
        correct=0; 
        total=0;

        for(i=0;i<8;i=i+1)begin 
            for(j=-8;j<8;j=j+1)begin 
                A=i;
                B=j;
                #10; 
                expected =$signed(A)*$signed(B); 
                total= total+1; 
               
                if(product === expected)begin
                    correct=correct+1;
                end else begin
                    $display("FAIL: A=%d B=%d PRODUCT=%d EXPECTED=%d",A,B,product,expected);
                    $display("------------------------------------------------");
                    $display("A: %03b",DUT.A);
                    $display("B: %03b",DUT.B);
                    $display("booth_group0: %03b",DUT.booth_group0);
                    $display("booth_group1: %03b",DUT.booth_group1);
                    $display("op0: %03b",DUT.op0);
                    $display("op1: %03b",DUT.op1);
                    $display("partial0: %03b",DUT.partial0);
                    $display("partial1: %03b",DUT.partial1);
                    $display("w_sum: %03b",DUT.w_sum);
                    $display("w_carry: %03b",DUT.w_carry);
                    $display("product: %03b",DUT. product);
                    $display("------------------------------------------------");
                end
            end
        end

        
        accuracy=(correct*100.0)/total; 
        $display("-----------------------------");
        $display("Testing complete");
        $display("Total test: %d", total);
        $display("Correct: %d", correct);
        $display("Wrong: %d",total-correct);
        $display("Accuracy: %0.2f%%",accuracy);
        $display("-----------------------------");

        $finish; 
        
    end 

    

endmodule