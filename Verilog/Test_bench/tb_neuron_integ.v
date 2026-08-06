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
   reg signed [63:0] x_in;




   initial begin
       $display("-------------test bench------------");
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
       x_in = {16'd0,16'd0,16'd0,16'd0};


       //load weights: [-4, 2, -2, 3]
       #20; // wait after initzialiation


       //weight -4 address 0
       @(negedge clk);
       write_addr= 4'd0;
       w_in_data= 4'hC;
       write_en= 1'b1;
       $display("%0t TB: write_addr=%0d data=%0d", $time,write_addr, $signed(w_in_data));
       @(posedge clk);
     
       $display("%0t TB after edge", $time);


       //weight 2 address 1
       @(negedge clk);
       write_addr= 4'd1;
       w_in_data= 4'h2;
       write_en= 1'b1;
       $display("%0t TB: write_addr=%0d data=%0d", $time,write_addr, $signed(w_in_data));
       @(posedge clk);


       //weight -1 address 2
       @(negedge clk);
       write_addr= 4'd2;
       w_in_data= 4'hF;
       write_en= 1'b1;
       $display("%0t TB: write_addr=%0d data=%0d", $time,write_addr, $signed(w_in_data));
       @(posedge clk);


       //weight 3 address 3
       @(negedge clk);
       write_addr= 4'd3;
       w_in_data= 4'h3;
       write_en= 1'b1;
       $display("%0t TB: write_addr=%0d data=%0d", $time,write_addr, $signed(w_in_data));
       @(posedge clk);


       //stop writing
       @(negedge clk);
       write_en = 1'b0;


       //stumulus code
       #20; //wait after werights are loaded
       read_en= 1'b1;
       read_addr= 4'd3;
       x_in={16'd0,16'd0,16'd0,16'd1};
       $display("%0t TB: write_addr=%0d data=%0d", $time,write_addr, $signed(w_in_data));
      
       //neuron can't use newly read weight till after this edge
       @(posedge clk);
       #1;
       //keep applying input 1 while reading weight +3
       for(integer i=0; i<15;i=i+1) begin
           x_in={16'd0,16'd0,16'd0,16'd1};


           @(posedge clk);
           #1;

           //$display("cycle %0d: v_mem=%0d spike=%b",i,$signed(v_mem), spike_out);
           $display("cycle=%0d: x=%0d w=%0d product=%0d sum=%0d next=%0d v_mem=%0d spike=%0b",
                    i,$signed(x_in[3:0]), $signed(uut.w_in),$signed(uut.bw_products),$signed(uut.total_sum),
                    $signed(uut.v_next_calc), $signed(v_mem),spike_out);
       end


       @(negedge clk);
       read_en=1'b0;
       x_in=64'd0;
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
       $dumpvars(0, uut);
       #500;
       $finish;
   end
endmodule
