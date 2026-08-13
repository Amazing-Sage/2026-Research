`timescale 1ns / 1ps //defines time unit and precision 

module half_adder_tb; 
    reg a; 
    reg b; 

    wire sum; 
    wire carry; 

    half_adder DUT(
        .a(a),
        .b(b),
        .sum(sum),
        .carry(carry)
    );

    initial begin 
        a=0; 
        b=0; 
        #10; 
        $display("a=%b b=%b sum=%b carry=%b",a,b,sum,carry);

        a=0; 
        b=1; 
        #10; 
        $display("a=%b b=%b sum=%b carry=%b",a,b,sum,carry);

        a=1; 
        b=0; 
        #10; 
        $display("a=%b b=%b sum=%b carry=%b",a,b,sum,carry);

        a=1; 
        b=1; 
        #10; 
        $display("a=%b b=%b sum=%b carry=%b",a,b,sum,carry);

        $finish;

    end
endmodule