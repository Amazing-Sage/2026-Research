module bw_multiplier(
    input enable,
    input signed [3:0] A,
    input signed [3:0] B,

    output signed [7:0] partial0,
    output signed [7:0] partial1
);
    wire [2:0] booth_group0;
    wire [2:0] booth_group1; 

    wire signed [2:0] op0; 
    wire signed [2:0] op1;

    wire signed [7:0] shifted_partial1; 
    assign shifted_partial1= partial1>>2; 

    //initiate two encoders 
    bw_encoder enc0(
        .bits(booth_group0),
        .op(op0)
    );

    bw_encoder enc1(
        .bits(booth_group1),
        .op(op1)
    );

    //create booth groups 
    bw_gen gen(
        .B(B),
        .booth_group0(booth_group0),
        .booth_group1(booth_group1)
    );
    //gernarte partial products
    bw_partial_product pp0(
        .enable(enable),
        .A(A),
        .op(op0),
        .partial_prod(partial0)
    );

    wire signed [7:0] raw_partial1;
    bw_partial_product pp1(
        .enable(enable),
        .A(A),
        .op(op1),
        .partial_prod(raw_partial1)
    );
    assign partial1= raw_partial1 <<2;

endmodule