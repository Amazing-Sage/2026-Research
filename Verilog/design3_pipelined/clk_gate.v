module clk_gate(
    input clk, 
    input enable, 
    input reset, 
    output gated_clk
); 
   //internal signals 
   reg latch_out; 
   wire clk_n = ~clk; 

    //combonational and gate 

    assign gated_clk= clk & latch_out; 
    //sequential d-latch(saplies enable on falling edge of clock)
    always @(clk_n or reset)begin 
        
        if(reset)begin 
            latch_out <=1'b0; //clear latch on reset 
        end
        else if(clk_n)begin 
            latch_out <=enable; //sanoke ebavke whe clk is low 
        end
    end

endmodule