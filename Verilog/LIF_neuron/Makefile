SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Add your Verilog source files
VERILOG_SOURCES += $(shell pwd)/lif_neuron.v

# Top-level module name inside your Verilog
TOPLEVEL = lif_neuron

# Name of the python test file (without .py)
MODULE = test_lif_neuron

# Enable Cocotb's native automatic waveform dumping (creates dump.vcd)
WAVES = 1

# Waveform setup parameters
COCOTB_HDL_TIMEUNIT = 1ns
COCOTB_HDL_TIMEPRECISION = 1ps

ifeq ($(SIM), icarus)
    # Compile with SystemVerilog features enabled
    COMPILE_ARGS += -g2012
    # Search the local directory first
    COMPILE_ARGS += -I$(shell pwd)
    # Search the parent directory (Verilog/) as a fallback
    COMPILE_ARGS += -I$(shell pwd)/..
endif

# Include cocotb makefile rules
include $(shell cocotb-config --makefiles)/Makefile.sim