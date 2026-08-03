`timescale 1ns/1ps

module tb_neuron_integ(); 
    reg clk; 

    initial begin 
        clk=0; 
        forever #5 clk= ~clk; // 10ns per 100Mhz
    end

    //reset and enable signals 
    reg reset; 
    reg enable; 

    //output signals to monitor 
    wire spike_out; 
    wire signed [31:0] v_mem; 

    //loading weights 
    reg write_en;
    reg [3:0]write_addr;
    reg signed [3:0] w_in_data;

    //read interface (feed neuron) 
    reg read_en;
    reg [3:0] read_addr;
    reg signed [15:0] x_in;


    initial begin 
        reset =1; 
        enable=0; 
        #10; 
        reset=0; 
        #10; 
        enable=1; 
        //initialize all inputs 
        w_in_data= 4'b0; 
        write_addr= 4'b0; 
        write_en= 1'b0; 
        read_addr =4'b0; 
        read_en = 1'b0; 
        x_in = 16'b0; 

        //load weights: [-4, 2, -2, 3]
        #20; // wait after initzialiation 

        //weight -4
        write_addr= 4'd0; 
        w_in_data= 4'hC; 
        write_en= 1'b1; 
        @(posedge clk);

        //weight 2
        write_addr= 4'd1; 
        w_in_data= 4'h2; 
        write_en= 1'b1; 
        @(posedge clk);

        //weight -1
        write_addr= 4'd2; 
        w_in_data= 4'hF; 
        write_en= 1'b1; 
        @(posedge clk);

        //weight 3
        write_addr= 4'd3; 
        w_in_data= 4'h3; 
        write_en= 1'b1; 
        @(posedge clk);

        //stop writing 
        write_en = 1'b0;

        //stumulus code 
        #20; //wait after werights are loaded 
        read_en= 1'b1;
        x_in= 16'b0000_0000_0101; 
        @(posedge clk);
        $display ("cycle 0: v_mem= %d spike =%b", $signed(v_mem), spike_out);

        //cycle 1 
        x_in= 16'b0000_0000_1010; 
        @(posedge clk);
        $display ("cycle 1: v_mem= %d spike =%b", $signed(v_mem), spike_out);

        //cycle 2
        x_in= 16'b0000_0000_0011; 
        @(posedge clk);
        $display ("cycle 2: v_mem= %d spike =%b", $signed(v_mem), spike_out);

        //cycle 3
        x_in= 16'b0000_0000_1100; 
        @(posedge clk);
        $display ("cycle 3: v_mem= %d spike =%b", $signed(v_mem), spike_out);

        //cycle 4-9
        x_in= 16'b0; 
        
        repeat(6) begin 
            @(posedge clk);
            $display ("cycle 0: v_mem= %d spike =%b", $signed(v_mem), spike_out);
        end
        



    end
    lif_neuron #(
        .num_inputs(4)
    )uut (
        .clk(clk),
        .reset(reset),
        .x_in(x_in),
        //.w_out(w_out),
        .v_mem(v_mem),
        .spike_out(spike_out),
        .write_en(write_en),
        .write_addr(write_addr),
        .w_in_data(w_in_data),
        .read_en(read_en), 
        .read_addr(read_addr)
    );
    
    //GTK wave 
    initial begin
        $dumpfile("tb_neuron_integ.vcd");
        $dumpvars(0, tb_neuron_integ);
        #500;
        $finish;
    end
endmodule