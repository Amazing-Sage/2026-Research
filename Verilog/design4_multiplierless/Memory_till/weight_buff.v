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
    output reg signed [3:0] w_out_data //[(4*num_inputs)-1:0]
);
//memory array 4 bit signed weight
reg signed [3:0] memory [0:15];

//writing and reading 
integer k;
always @(posedge clk)begin 
    // $display("weight buffer: reset=%b write_en=%b read_en=%b write_addr=%0d read_addr=%0d data=%0d",
    //             reset, write_en, read_en, write_addr, read_addr, $signed(w_in_data));

    if(reset)begin 
        w_out_data <= 4'd0 ;
    end else begin 
        //check write en 
        if(write_en)begin 
            //save w_in data into memory array at write addr
            memory[write_addr] <= w_in_data; 
            //$display("write: addr=%0d data=%0d", write_addr, $signed(w_in_data));
        end 

        //read logic and check read_en 
        if(read_en)begin 
            //load from mem array at read addr into w_out_data 
            
            // for(k=0; k<num_inputs; k=k+1)begin 
            //     w_out_data [(4*k)+:4] <= memory[(read_addr*num_inputs)+k];
            //     $display("wb: addr=%0d weight=%0d", read_addr, $signed(memory[(read_addr*num_inputs)+k]));
            // end
            
            w_out_data <= memory[read_addr];
           // $display("wb: addr=%0d weight=%0d", read_addr, $signed(memory[read_addr]));
        end
    end
end
endmodule