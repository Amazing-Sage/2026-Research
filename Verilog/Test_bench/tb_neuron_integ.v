`timescale 1ns/1ps

module tb_neuron_integ(); 
    reg clk; 

    initial begin 
        clk=0; 
        forever #5 clk= ~clk;
    end

    reg reset; 
    reg enable; 

    wire spike_out; 
    wire signed [31:0] v_mem; 

    reg write_en;
    reg [3:0]write_addr;
    reg signed [3:0] w_in_data;

    reg read_en;
    reg [3:0] read_addr;
    reg signed [63:0] x_in;

    integer i;
    initial begin 
        reset =1'b1; 
        enable=1'b0; 
        #10; 
        reset=1'b0; 
        #10; 
        enable=1'b1; 
        w_in_data= 4'b0; 
        write_addr= 4'b0; 
        write_en= 1'b0; 
        read_addr =4'b0; 
        read_en = 1'b0; 
        x_in = 64'd0;

        #20;

        read_addr= 4'd1; 
        write_addr= 4'd0; 
        w_in_data= 4'hC; 
        write_en= 1'b1; 
        @(posedge clk);

        read_addr= 4'd2; 
        write_addr= 4'd1; 
        w_in_data= 4'h2; 
        write_en= 1'b1; 
        @(posedge clk);

        read_addr= 4'd3; 
        write_addr= 4'd2; 
        w_in_data= 4'hF; 
        write_en= 1'b1; 
        @(posedge clk);

        write_addr= 4'd3; 
        w_in_data= 4'h3; 
        write_en= 1'b1; 
        @(posedge clk);

        write_en = 1'b0;

        #20;
        read_en= 1'b1;
        read_addr=4'd0;
        x_in={16'd0,16'd0,16'd0,16'd1};
        @(posedge clk);
        $display ("cycle 0: v_mem=%d spike =%b", $signed(v_mem), spike_out);

        read_en= 1'b1;
        read_addr=4'd1;
        x_in={16'd0,16'd0,16'd0,16'd1};
        @(posedge clk);
        $display ("cycle 1: v_mem=%d spike =%b", $signed(v_mem), spike_out);

        read_en= 1'b1;
        read_addr=4'd2;
        x_in={16'd0,16'd0,16'd0,16'd1};
        @(posedge clk);
        $display ("cycle 2: v_mem=%d spike =%b", $signed(v_mem), spike_out);

        read_en= 1'b1;
        read_addr=4'd3;
        x_in={16'd0,16'd0,16'd0,16'd1};
        @(posedge clk);
        $display ("cycle 3: v_mem=%d spike =%b", $signed(v_mem), spike_out);

        
        for(i=4; i<10; i=i+1)begin 
            read_en= 1'b1;
            read_addr=4'd3;//reading weight +3 from address 3
            x_in={16'd0,16'd0,16'd0,16'd1};
            
            @(posedge clk);
            $display ("cycle %0d: v_mem=%d spike =%b",i, $signed(v_mem), spike_out);
        end
        
    end

    lif_neuron #(
        .num_inputs(4)
    )uut (
        .clk(clk),
        .reset(reset),
        .x_in(x_in),
        .v_mem(v_mem),
        .spike_out(spike_out),
        .write_en(write_en),
        .write_addr(write_addr),
        .w_in_data(w_in_data),
        .read_en(read_en), 
        .read_addr(read_addr)
    );
    
    initial begin
        $dumpfile("tb_neuron_integ.vcd");
        $dumpvars(0, tb_neuron_integ);
        #500;
        $finish;
    end
endmodule