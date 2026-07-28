module CPA(
    input signed [7:0] sum, 
    input signed [8:0] carry, 

    output signed[7:0] product
);

    assign product = sum+(carry <<1);
endmodule