module bw_gen(
    input signed [3:0] B, 

    output wire [2:0] booth_group0,
    output wire [2:0] booth_group1
);

//rad-4 booth grouping 
assign booth_group0 ={B[1],B[0],1'b0};
assign booth_group1 ={B[3],B[2],B[1]};

endmodule