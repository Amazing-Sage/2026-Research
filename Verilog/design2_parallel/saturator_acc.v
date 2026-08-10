module saturator_acc (
    input clk,
    input reset,
    input enable,
    input [7:0] data_in,
    output reg [3:0] sat_out,
    output reg overflow
);

//internal registers 
reg signed [9:0] acc_reg; 

//sequntial logic on accumulation on clock 
always @(posedge clk or posedge reset) begin
    if(reset)begin 
        //clear accumulator 
        acc_reg<= 10'b0; 

    end 
    else if (enable)begin 
        //add data in to acc reg 
        acc_reg <= acc_reg + data_in; 
    end 
    else begin
        //hold current value or do nothing 

    end
end

//combonation logic saturation and overflow
always @(*) begin 
    if(acc_reg >$signed(10'd7))begin 
        //saturato to seven and set overflow 
        sat_out = 4'b0111;
        overflow = 1'b1;
    end 
    else if (acc_reg < $signed(-10'd8))begin 
        //saturate to negitive 8 and set overflow 
        sat_out = 4'b1000;
        overflow = 1'b1;
    end
    else begin 
        // saturation not needed 
        sat_out = acc_reg[3:0]; //take lower 4 bits
        overflow = 1'b0;
    end
end 


endmodule
