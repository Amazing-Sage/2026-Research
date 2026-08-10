module bw_partial_product(//this is the booth wallace multiplier
    input enable,
    input signed [3:0] A, //neuron multipliers
    input signed [2:0] op,//operation
    output reg signed [7:0] partial_prod
);
    reg signed [7:0] A_ext; //_ext is for extend

    always @(*)begin 
        A_ext= {{4{A[3]}},A};
        if(!enable)begin
            partial_prod =0; 
        end else begin 
            //booth operation 
            case(op)// this acts the same as a switch in software
                3'b000: partial_prod=8'd0;// both groups do nothing to multiplication
                3'b001: partial_prod=A_ext; //both groups do nothing to multiplication
                3'b010: partial_prod=A_ext <<1; //doubles in size
                3'b111: partial_prod=-A_ext;
                3'b110: partial_prod=-(A_ext <<<1);
                default: partial_prod=8'd0;

            endcase
        end

    end
endmodule