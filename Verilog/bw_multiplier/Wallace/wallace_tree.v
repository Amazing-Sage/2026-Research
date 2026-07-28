module wallace_tree(
    input signed [7:0] partial0,
    input signed [7:0] partial1,

    output signed[7:0] sum, 
    output signed[8:0] carry
);

    wire [7:0] reduced_sum; 
    wire [7:0] reduced_carry;

assign carry[0] = 1'b0;

    half_adder ha0(
        .a(partial0[0]),
        .b(partial1[0]),
        .sum(sum[0]),
        .carry(carry[1])
    );

    genvar i;
    generate 
        for(i=1; i<8;i=i+1)begin: full_adder_stage
            full_adder fa(
            .a(partial0[i]),
            .b(partial1[i]),
            .cin(carry[i]),
            .sum(sum[i]),
            .cout(carry[i+1])
            );
        end 
    endgenerate

endmodule