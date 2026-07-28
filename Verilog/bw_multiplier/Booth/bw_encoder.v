module bw_encoder(//this is the booth wallace multiplier
    input [2:0] bits, 
    output reg signed [2:0] op

    // output signed [7:0] partial0,
    // output signed [7:0] partial1
);
    
    //booth encodeer 0
     always @(*) begin 
        case(bits)// this is simular to the switch function in software
        //+a +2a -a -2a is how the math works adds up to 2a untill 011 
        //then starts going down the other way starting at 011

        3'b000: op=0;
        3'b001: op=1;
        3'b010: op=1;
        3'b011: op=2;
        3'b100: op=-2;
        3'b101: op=-1;
        3'b110: op=-1;
        3'b111: op=0;

        default: op=0;
        endcase
    end

    // //booth encodeer 1
    // always @(*) begin 
    //     case(bits)// this is simular to the switch function in software
    //     //+a +2a -a -2a is how the math works adds up to 2a untill 011 
    //     //then starts going down the other way starting at 011

    //     3'b000: op1=0;
    //     3'b001: op1=1;
    //     3'b010: op1=1;
    //     3'b011: op1=2;
    //     3'b100: op1=-2;
    //     3'b101: op1=-1;
    //     3'b110: op1=-1;
    //     3'b111: op1=0;

    //     default: op=0;
    //     endcase
    // end

    

endmodule