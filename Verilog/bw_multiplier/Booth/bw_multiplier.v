//combines booth and wallace components all together to act as one whole multiplier
module bw_multiplier(
    input enable,
    input signed [3:0] A,
    input signed [3:0] B,

    // output signed [7:0] partial0,
    // output signed [7:0] partial1
    output signed [7:0] product
);
    //booth wiring groups
    wire [2:0] booth_group0;
    wire [2:0] booth_group1; 

    //booth encoder outputs
    wire signed [2:0] op0; 
    wire signed [2:0] op1;

    //partial prducts
    wire signed [7:0] shifted_partial1; 
    wire signed [7:0] partial0 
    wire signed [7:0] partial1
    assign shifted_partial1= partial1>>2; 

    //wallace tree outputs
    wire signed [7:0] w_sum; 
    wire signed [8:0] w_carry;

    //radix 4 booth grouping (4 bits)
    bw_gen gen(
        .B(B),
        .booth_group0(booth_group0),
        .booth_group1(booth_group1)
    );

    //initiate two encoders 
    bw_encoder enc0(
        .A(A),
        .bits(booth_group0),
        .op(op0),
        .partial_prod(partial0)
    );

    bw_encoder enc1(
        .B(B),
        .bits(booth_group1),
        .op(op1),
        .partial_prod(partial0)
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

    //wallace tree reduction 
    wallace_tree WT(
        .partial0(partial0),
        .partial1(partial1),
        .sum(wallace_sum),
        .carry(wallace_carry)
    );

    //carry propagate adder (CPA)
    CPA CPA_unit(
        .sum(wallace_sum),
        .carry(wallace_carry),
        .product(product)
    );

endmodule