//this file serves as our local memory tilling

module weight_buffer #(
    parameter num_inputs =4
    )(
    input wire clk, 
    input wire reset, 

    //loading weights 
    input wire write_en, 
    input wire [3:0]write_addr,
    input wire signed [3:0] w_in_data,

    //read interface (feed neuron) 
    input wire read_en,
    input wire [3:0] read_addr,
    output reg signed [(4*num_inputs)-1:0] w_out_data
);
//memory array 4 bit signed weight
reg signed [3:0] memory [0:15];

//writing and reading 
always @(posedge clk)begin 
    if(reset)begin 
        w_out_data <= 4'd0;
    end else begin 
        //check write en 
        if(write_en)begin 
            //save w_in data into memory array at write addr
            memory[write_addr] <= w_in_data; 
        end 

        //read logic and check read_en 
        if(read_en)begin 
            //load from mem array at read addr into w_out_data 
            w_out_data <= memory[read_addr];
        end

    end
end
endmodule