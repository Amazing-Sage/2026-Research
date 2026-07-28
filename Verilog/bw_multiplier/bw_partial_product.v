module bw_partial_product(//this is the booth wallace multiplier
    input enable,
    input signed [3:0] A, //neuron multipliers
    input signed [2:0] op,//operation
    output reg signed [7:0] partial_prod
);

    always @(*)begin 
        if(!enable)begin
            partial_prod =0; 
        end else begin 
            //booth operation 
            case(op)// 
                3'd0: partial_prod=0;// both groups do nothing to multiplication
                3'd1: partial_prod=A; //both groups do nothing to multiplication
                3'd2: partial_prod=A <<1; //doubles in size
                3'b111: partial_prod=-A;
                3'b110: partial_prod=-(A <<1);
                default: partial_prod=0;

            endcase
        end

    end
endmodule