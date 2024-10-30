# Copyright (c) 2013, 2017, 2020-2021 Arm Limited
# All rights reserved.
#
# The license below extends only to copyright in the software and shall
# not be construed as granting a license to any other intellectual
# property including but not limited to intellectual property relating
# to a hardware implementation of the functionality of the software
# licensed hereunder.  You may use the software subject to the license
# terms below provided that you ensure that this notice is replicated
# unmodified and in its entirety in all distributions of the software,
# modified or unmodified, in source code or in binary form.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from common import (
    HMC,
    ObjectList,
)

#import m5.objects
from m5.objects import *
from m5.util import *
import inspect
import sys


def create_mem_intf(intf, r, i, intlv_bits, intlv_size, xor_low_bit):
    """
    Helper function for creating a single memory controller from the given
    options.  This function is invoked multiple times in config_mem function
    to create an array of controllers.
    """

    import math

    intlv_low_bit = int(math.log(intlv_size, 2))

    # Use basic hashing for the channel selection, and preferably use
    # the lower tag bits from the last level cache. As we do not know
    # the details of the caches here, make an educated guess. 4 MByte
    # 4-way associative with 64 byte cache lines is 6 offset bits and
    # 14 index bits.
    if xor_low_bit:
        xor_high_bit = xor_low_bit + intlv_bits - 1
    else:
        xor_high_bit = 0

    # Create an instance so we can figure out the address
    # mapping and row-buffer size
    interface = intf()

    print(interface.addr_mapping.value)
    print(type(intf))

    # Only do this for DRAMs
    if issubclass(intf, m5.objects.DRAMInterface):
        # If the channel bits are appearing after the column
        # bits, we need to add the appropriate number of bits
        # for the row buffer size
        if interface.addr_mapping.value == "RoRaBaChCo":
            # This computation only really needs to happen
            # once, but as we rely on having an instance we
            # end up having to repeat it for each and every
            # one
            rowbuffer_size = (
                interface.device_rowbuffer_size.value
                * interface.devices_per_rank.value
            )

            intlv_low_bit = int(math.log(rowbuffer_size, 2))
        elif interface.addr_mapping.value == "RoRaChCoBaCo":
            # TODO: This has to be a function of how we want to split the pages among banks
            intlv_low_bit = 14

    # Also adjust interleaving bits for NVM attached as memory
    # Will have separate range defined with unique interleaving
    if issubclass(intf, m5.objects.NVMInterface):
        # If the channel bits are appearing after the low order
        # address bits (buffer bits), we need to add the appropriate
        # number of bits for the buffer size
        if interface.addr_mapping.value == "RoRaBaChCo":
            # This computation only really needs to happen
            # once, but as we rely on having an instance we
            # end up having to repeat it for each and every
            # one
            buffer_size = interface.per_bank_buffer_size.value

            intlv_low_bit = int(math.log(buffer_size, 2))

    print(f"r.start: {r.start}")
    print(f"r.size: {r.size}")
    print(f"intlv_low_bit: {intlv_low_bit}")
    print(f"intlv_bits: {intlv_bits}")
    print(f"xor_high_bit: {xor_high_bit}")
    print(f"i: {i}")

    # We got all we need to configure the appropriate address
    # range
    interface.range = m5.objects.AddrRange(
        r.start,
        size=r.size(),
        intlvHighBit=intlv_low_bit + intlv_bits - 1,
        xorHighBit=xor_high_bit,
        intlvBits=intlv_bits,
        intlvMatch=i,
    )
    return interface


def config_mem(options, system):
    """
    Create the memory controllers based on the options and attach them.

    If requested, we make a multi-channel configuration of the
    selected memory controller class by creating multiple instances of
    the specific class. The individual controllers have their
    parameters set such that the address range is interleaved between
    them.
    """

    # Mandatory options
    opt_mem_channels = options.mem_channels

    # Semi-optional options
    # Must have either mem_type or nvm_type or both
    opt_mem_type = getattr(options, "mem_type", None)
    opt_nvm_type = getattr(options, "nvm_type", None)
    if not opt_mem_type and not opt_nvm_type:
        fatal("Must have option for either mem-type or nvm-type, or both")

    # Optional options
    opt_tlm_memory = getattr(options, "tlm_memory", None)
    opt_external_memory_system = getattr(
        options, "external_memory_system", None
    )
    opt_elastic_trace_en = getattr(options, "elastic_trace_en", False)
    opt_mem_ranks = getattr(options, "mem_ranks", None)
    opt_nvm_ranks = getattr(options, "nvm_ranks", None)
    opt_hybrid_channel = getattr(options, "hybrid_channel", False)
    opt_dram_powerdown = getattr(options, "enable_dram_powerdown", None)
    opt_mem_channels_intlv = getattr(options, "mem_channels_intlv", 128)
    opt_xor_low_bit = getattr(options, "xor_low_bit", 0)

    print(f"opt_mem_type:{opt_mem_type}")
    print(f"opt_nvm_type:{opt_nvm_type}")
    print(f"opt_tlm_memory:{opt_tlm_memory}")
    print(f"opt_external_memory_system:{opt_external_memory_system}")
    print(f"opt_elastic_trace_en:{opt_elastic_trace_en}")
    print(f"opt_mem_channels:{opt_mem_channels}")
    print(f"opt_mem_ranks:{opt_mem_ranks}")
    print(f"opt_nvm_ranks:{opt_nvm_ranks}")
    print(f"opt_hybrid_channel:{opt_hybrid_channel}")
    print(f"opt_dram_powerdown:{opt_dram_powerdown}")
    print(f"opt_mem_channels_intlv:{opt_mem_channels_intlv}")
    print(f"opt_xor_low_bit:{opt_xor_low_bit}")


    if opt_mem_type == "HMC_2500_1x32":
        HMChost = HMC.config_hmc_host_ctrl(options, system)
        HMC.config_hmc_dev(options, system, HMChost.hmc_host)
        subsystem = system.hmc_dev
        xbar = system.hmc_dev.xbar
    else:
        subsystem = system
        xbar = system.membus

    if opt_tlm_memory:
        system.external_memory = m5.objects.ExternalSlave(
            port_type="tlm_slave",
            port_data=opt_tlm_memory,
            port=system.membus.mem_side_ports,
            addr_ranges=system.mem_ranges,
        )
        system.workload.addr_check = False
        return

    if opt_external_memory_system:
        subsystem.external_memory = m5.objects.ExternalSlave(
            port_type=opt_external_memory_system,
            port_data="init_mem0",
            port=xbar.mem_side_ports,
            addr_ranges=system.mem_ranges,
        )
        subsystem.workload.addr_check = False
        return

    nbr_mem_ctrls = opt_mem_channels

    import math

    from m5.util import fatal

    intlv_bits = int(math.log(nbr_mem_ctrls, 2))
    if 2**intlv_bits != nbr_mem_ctrls:
        fatal("Number of memory channels must be a power of 2")

    if opt_mem_type:
        intf = ObjectList.mem_list.get(opt_mem_type)
    if opt_nvm_type:
        n_intf = ObjectList.mem_list.get(opt_nvm_type)

    nvm_intfs = []
    mem_ctrls = []

    if opt_elastic_trace_en and not issubclass(intf, m5.objects.SimpleMemory):
        fatal(
            "When elastic trace is enabled, configure mem-type as "
            "simple-mem."
        )

    # The default behaviour is to interleave memory channels on 128
    # byte granularity, or cache line granularity if larger than 128
    # byte. This value is based on the locality seen across a large
    # range of workloads.
    intlv_size = max(opt_mem_channels_intlv, system.cache_line_size.value)

    # For every range (most systems will only have one), create an
    # array of memory interfaces and set their parameters to match
    # their address mapping in the case of a DRAM
    range_iter = 0
    for r in system.mem_ranges:
        # As the loops iterates across ranges, assign them alternatively
        # to DRAM and NVM if both configured, starting with DRAM
        range_iter += 1

        for i in range(nbr_mem_ctrls):
            if opt_mem_type and (not opt_nvm_type or range_iter % 2 != 0):
                # Create the DRAM interface
                dram_intf = create_mem_intf(
                    intf, r, i, intlv_bits, intlv_size, opt_xor_low_bit
                )

                # Set the number of ranks based on the command-line
                # options if it was explicitly set
                if (
                    issubclass(intf, m5.objects.DRAMInterface)
                    and opt_mem_ranks
                ):
                    dram_intf.ranks_per_channel = opt_mem_ranks

                # Enable low-power DRAM states if option is set
                if issubclass(intf, m5.objects.DRAMInterface):
                    dram_intf.enable_dram_powerdown = opt_dram_powerdown

                if opt_elastic_trace_en:
                    dram_intf.latency = "1ns"
                    print(
                        "For elastic trace, over-riding Simple Memory "
                        "latency to 1ns."
                    )
                
                # Create the controller that will drive the interface
                mem_ctrl = dram_intf.controller()

                # @PIM
                # TODO
                #if hasattr(options,'enable_pim') and options.enable_pim:
                #    mem_ctrl.cpu_type = options.cpu_type
                #    mem_ctrl.coherence_granularity=options.coherence_granularity

                mem_ctrls.append(mem_ctrl)

            elif opt_nvm_type and (not opt_mem_type or range_iter % 2 == 0):
                nvm_intf = create_mem_intf(
                    n_intf, r, i, intlv_bits, intlv_size, opt_xor_low_bit
                )

                # Set the number of ranks based on the command-line
                # options if it was explicitly set
                if (
                    issubclass(n_intf, m5.objects.NVMInterface)
                    and opt_nvm_ranks
                ):
                    nvm_intf.ranks_per_channel = opt_nvm_ranks

                # Create a controller if not sharing a channel with DRAM
                # in which case the controller has already been created
                if not opt_hybrid_channel:
                    mem_ctrl = m5.objects.HeteroMemCtrl()
                    mem_ctrl.nvm = nvm_intf

                    mem_ctrls.append(mem_ctrl)
                else:
                    nvm_intfs.append(nvm_intf)

    # hook up NVM interface when channel is shared with DRAM + NVM
    for i in range(len(nvm_intfs)):
        mem_ctrls[i].nvm = nvm_intfs[i]

    # Connect the controller to the xbar port
    for i in range(len(mem_ctrls)):
        if opt_mem_type == "HMC_2500_1x32":
            # Connect the controllers to the membus
            mem_ctrls[i].port = xbar[i // 4].mem_side_ports
            # Set memory device size. There is an independent controller
            # for each vault. All vaults are same size.
            mem_ctrls[i].dram.device_size = options.hmc_dev_vault_size
        else:
            # Connect the controllers to the membus
            mem_ctrls[i].port = xbar.mem_side_ports

    subsystem.mem_ctrls = mem_ctrls
    
    if hasattr(options,'enable_pim') and options.enable_pim:
        print ("Enable PIM simulation in the system.")

        pim_type = options.pim_type
        num_processors = options.num_pim_processors
        num_pim_logic = num_processors

        if num_pim_logic <= 0:
            fatal ("The num of PIM logic/processors cannot be zero while enabling PIM.")
        if options.mem_type.startswith("HMC"):
            if num_kernels>0:
                num_kernels=16
                num_processors=0
            else:
                num_processors=16
                num_kernels=0
        system.pim_type = pim_type
        #for cpu in system.cpu:
        #    # let host-side processors know the address of PIM logic
        #    cpu.pim_base_addr = addr_base

        # memory contains kernels
        #if pim_type != "cpu" and num_kernels > 0:
        #    pim_kernerls = []
    
        #    print ("Creating PIM kernels...")
        #    for pid in range(num_kernels):
        #        if(options.kernel_type=="adder"):
        #            _kernel = PIMAdder()
        #        else:
        #            if(options.kernel_type=="multiplier"):
        #                _kernel = PIMMultiplier()
        #            else:
        #                if(options.kernel_type=="divider"):
        #                    _kernel = PIMDivider()
        #                else:
        #                    fatal("no pim kernel type specified.")
        #        
        #        vd = VoltageDomain(voltage="1.0V")
        #        _kernel.clk_domain = SrcClockDomain(clock="1GHz", voltage_domain=vd)
        #        _kernel.id = pid

        #        # Currently, we use only one bit for accessing a PIM kernel.
        #        # Detailed PIM information is defined inside the packet
        #        # at mem/pactet.hh(cc)
        #        # TODO: 
        #        # 1. pass a different base address for each thread
        #        # 2. pass a addr_end such that we allocate 1 or N page/arbitrary range 
        #        _kernel.addr_ranges = AddrRange(addr_base + pid, addr_base + pid)
        #        print ("addr_base:", hex(addr_base))
        #        print ("pid:", hex(pid))
        #        print(_kernel.addr_ranges.__str__())
        #        #print(_kernel.addr_ranges.begin())
        #        #print(_kernel.addr_ranges.end())
        #        _kernel.addr_base = addr_base

        #        if options.mem_type.startswith("DDR"):
        #            # connect to the memory bus if the memory is DRAM
        #            _kernel.port = xbar.slave
        #            _kernel.mem_port = xbar.master
        #        if options.mem_type.startswith("HMC"):
        #            _kernel.port = system.membus.slave
        #            _kernel.mem_port = system.membus.master
        #        pim_kernerls.append(_kernel)
        #    system.pim_kernerls = pim_kernerls

        # memory contains processors

        if pim_type != "kernel" and num_processors > 0:

            pim_vd = VoltageDomain(voltage="1.0V")
            pim_cpus = []
            print ("Creating PIM processors...")
            for i in range(num_processors):
                #system.pim_cpu = TimingSimpleCPU( is_pim =True, total_host_cpu = options.num_cpus, switched_out =True) 
                pim_cpu = TimingSimpleCPU(cpu_id=i, is_pim =True, switched_out =True) 
                pim_cpu.clk_domain = SrcClockDomain(clock = '1GHz', voltage_domain = pim_vd)
                pim_cpu.icache_port = system.membus.cpu_side_ports
                pim_cpu.dcache_port = system.membus.cpu_side_ports
                pim_cpu.workload = system.cpu[i].workload[0]
                pim_cpu.isa = system.cpu[i].isa #[ default_isa_class()]
                pim_cpu.createThreads()
                pim_cpus.append(pim_cpu)

            system.pim_cpu = pim_cpus

            #system.pim_cpu.icache_port = system.membus.cpu_side_ports
            #system.pim_cpu.dcache_port = system.membus.cpu_side_ports
            #system.pim_cpu.workload = system.cpu[0].workload[0]

            #system.pim_cpu.isa = system.cpu[0].isa #[ default_isa_class()]


        #if pim_type == "hybrid":
        #    if (num_kernels >0 and num_processors > 0) == False:
        #        fatal ("PIM logic is set to hybrid without configured")
