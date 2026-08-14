//this file is the test bench of the lif_neuron file
//using cocotb to test lif which is a bridge between python and verilog, this is the verilog bridge
`timescale 1ns / 1ps //defines time unit and precision 
//`include "lif_neuron.v"

module tb_lif_neuron;

    //declare signals to connect the neurons 
    reg clk; 
    reg reset;
    reg [63:0] x_in;
    reg [63:0] w_out;
    wire signed [7:0] v_mem; 
    wire spike_out; 
    reg mult_en;
    reg refract_cycles;


    //loading weights 
    reg write_en; 
    reg  [3:0]write_addr;
    reg  [3:0] w_in_data;

    //read interface (feed neuron) 
    reg  read_en;
    reg  [3:0] read_addr;
    wire signed [3:0] w_out_data;
     
    // wire [3:0] ref_counter_debug; 
    // assign ref_counter_debug= dut.ref_counter;
    
    // plug in the neuron device under test (DUT) 
    lif_neuron dut(
        .clk(clk),
        .reset(reset),
        .x_in(x_in),
        //.w_out(w_out),
        .v_mem(v_mem),
        .spike_out(spike_out),
        //.mult_en(mult_en),
        //.refract_cycles(refract_cycles),

        .write_en(write_en),
        .write_addr(write_addr),
        .w_in_data(w_in_data),
        .read_en(read_en), 
        .read_addr(read_addr)
        //.w_out_data(w_out_data) 
    );

    assign w_in ={60'b0, w_out_data};

    //simulation logic 
    always #10 clk = ~clk;

    always @(posedge clk)begin 
        if(!reset)begin
            $display("MONITOR time=%0t v_mem=%0d spike=%0d ref_counter=%0d",
                    $time, v_mem, spike_out, dut.ref_counter);
        end
    end


    initial begin 
        clk =0;
        // $monitor("Time=%0t | reset=%b | read_en=%b | x_in=%d | v_mem=%d | spike=%b | is_refractor=%b | ref_counter_debug=%b", 
        //             $time, reset, read_en, x_in, v_mem, spike_out, dut.is_refractor, ref_counter_debug);
        // //apply x input 
        reset =1'b1;
        write_en=1'b0;
        read_en= 1'b0; 
        write_addr= 4'd0; 
        read_addr= 4'd0;
        w_in_data= 4'd0; 
        x_in =4'd0; 
        mult_en = 1'b1;
        //refract_cycles = 4'd0;
        #20;

        //hold and relese reset 
        reset =1'b0; 
        #10; 

        // turn on read en to read weight 0 
        write_en = 1'b1;
        write_addr= 4'd0; //adress 0 
        w_in_data = 4'd5; //value 5 
        #10;
        write_en = 1'b0; //turn write enable off
        #10 ;

        //read weight back to feed neuron
        read_en = 1'b1;
        read_addr= 4'b0; 
        #10;

        //apply input current 
        x_in=4'd5;
        
        //to see refractory behavior we use @(posedge clk);
        @(posedge clk);
        $display("1st value read from v_mem = %d spike=%b", v_mem,spike_out);
        @(posedge clk);
        $display("2nd value read from v_mem = %d spike=%b", v_mem,spike_out);
        @(posedge clk);
        $display("3rd value read from v_mem = %d spike=%b", v_mem,spike_out);
        @(posedge clk);
        $display("4th value read from v_mem = %d spike=%b", v_mem,spike_out);
        @(posedge clk);
        $display("5th value read from v_mem = %d spike=%b", v_mem,spike_out);
        @(posedge clk);
        $display("6th value read from v_mem = %d spike=%b", v_mem,spike_out);
        @(posedge clk);
        $display("7th value read from v_mem = %d spike=%b", v_mem,spike_out);
        @(posedge clk);
        $display("8th value read from v_mem = %d spike=%b", v_mem,spike_out);
        @(posedge clk);
        $display("9th value read from v_mem = %d spike=%b", v_mem,spike_out);
        @(posedge clk);
        $display("10th value read from v_mem = %d spike=%b", v_mem,spike_out);
        @(posedge clk);
        $display("11th value read from v_mem = %d spike=%b", v_mem,spike_out);
        @(posedge clk);
        $display("12th value read from v_mem = %d spike=%b", v_mem,spike_out);



        //end simulation 
        #10;
        $finish;
    end


endmodule
