import os
import re
from six import iteritems

from .yellow_block import YellowBlock

class axi_dma(YellowBlock):
  # scatter/gather engine not yet built out here


  attr_map = {
    'addr_width':               {'param': 'c_addr_width',               'fmt': "{{:d}}"},
    'dlytmr_resolution':        {'param': 'c_dlytmr_resolution',        'fmt': "{{:d}}"},#
    'enable_multi_channel':     {'param': 'c_enable_multi_channel',     'fmt': "{{:d}}"},
    'enable_read':              {'param': 'c_include_mm2s',             'fmt': "{{:d}}"},
    'en_rd_unaligned_transfer': {'param': 'c_include_mm2s_dre',         'fmt': "{{:d}}"},#
    'enable_read_sf':           {'param': 'c_include_mm2s_sf',          'fmt': "{{:d}}"},#
    'enable_write':             {'param': 'c_include_s2mm',             'fmt': "{{:d}}"},
    'en_wr_unaligned_transfer': {'param': 'c_include_s2mm_dre',         'fmt': "{{:d}}"},#
    'enable_write_sf':          {'param': 'c_include_s2mm_sf',          'fmt': "{{:d}}"},#
    'include_sg':               {'param': 'c_include_sg',               'fmt': "{{:d}}"},
    'increased_throughput':     {'param': 'c_increased_throughput',     'fmt': "{{:d}}"},
    'm_axi_mm2s_data_width':    {'param': 'c_m_axi_mm2s_data_width',    'fmt': "{{:d}}"},
    'm_axi_s2mm_data_width':    {'param': 'c_m_axi_s2mm_data_width',    'fmt': "{{:d}}"},
    'mm2s_tdata_width':         {'param': 'c_m_axis_mm2s_tdata_width',  'fmt': "{{:d}}"},
    'enable_micro_dma':         {'param': 'c_micro_dma',                'fmt': "{{:d}}"},
    'mm2s_burst_size':          {'param': 'c_mm2s_burst_size',          'fmt': "{{:d}}"},
    'num_mm2s_channels':        {'param': 'c_num_mm2s_channels',        'fmt': "{{:d}}"},
    'num_s2mm_channels':        {'param': 'c_num_s2mm_channels',        'fmt': "{{:d}}"},
    'prmry_is_aclk_async':      {'param': 'c_prmry_is_aclk_async',      'fmt': "{{:d}}"},#
    's2mm_burst_size':          {'param': 'c_s2mm_burst_size',          'fmt': "{{:d}}"},
    's_axis_s2mm_tdata_width':  {'param': 'c_s_axis_s2mm_tdata_width',  'fmt': "{{:d}}"},
    'sg_include_stscntrl_strm': {'param': 'c_sg_include_stscntrl_strm', 'fmt': "{{:d}}"},#
    'sg_length_width':          {'param': 'c_sg_length_width',          'fmt': "{{:d}}"},
    'sg_use_stsapp_length':     {'param': 'c_sg_use_stsapp_length',     'fmt': "{{:d}}"},#
    'single_interface':         {'param': 'c_single_interface',         'fmt': "{{:d}}"}#
  }


  default_attr_map = {
    'addr_width':               32,
    'dlytmr_resolution':        125,
    'enable_multi_channel':     0,
    'enable_read':              1,
    'en_rd_unaligned_transfer': 0,
    'enable_read_sf':           1,
    'enable_write':             1,
    'en_wr_unaligned_transfer': 0,
    'enable_write_sf':          1,
    'include_sg':               0,
    'increased_throughput':     0,
    'm_axi_mm2s_data_width':    32,
    'm_axi_s2mm_data_width':    32,
    'm_axis_mm2s_tdata_width':  32,
    'enable_micro_dma':         0,
    'mm2s_burst_size':          16,
    'num_mm2s_channels':        1,
    'num_s2mm_channels':        1,
    'prmry_is_aclk_async':      0,
    's2mm_burst_size':          16,
    's_axis_s2mm_tdata_width':  32,
    'sg_include_stscntrl_strm': 0,
    'sg_length_width':          14,
    'sg_use_stsapp_length':     0,
    'single_interface':         0
}

  def initialize(self):
    # deserialize block from its parameter attribute map
    for attr, _ in iteritems(self.attr_map):
      setattr(self, attr, self.blk[attr])

    self.s2mm = {}
    self.mm2s = {}
    self.axis_s2mm = {} 
    self.axis_mm2s = {}

    # axi lite interface 
    self.saxi_lite = self.blk['saxi_intf']

    # axi mm/streaming interfaces
    maxi_intf  = self.blk['maxi_intf']
    if self.enable_write:
      for m in maxi_intf:
        if m['name'] == 'M_AXI_S2MM':
          self.s2mm = m
          self.axis_s2mm = self.blk['saxis_intf']

    if self.enable_read:
      for m in maxi_intf:
        if m['name'] == 'M_AXI_MM2S':
          self.mm2s = m
          self.axis_mm2s = self.blk['maxis_intf']

  # needs to have requires


  def modify_top(self, top):
    blkdesign = '{:s}_bd'.format(self.platform.conf['name'])
    bd_inst = top.get_instance(blkdesign, '{:s}_inst'.format(blkdesign))

    if self.enable_write:
      if len(self.axis_s2mm['dest'].split('/')) == 1:
        top_intf_prefix = self.axis_s2mm['dest'].lower()
        bd_intf_prefix = self.axis_s2mm['dest']
        bd_inst.add_port('{:s}_tdata'.format(top_intf_prefix), '{:s}_tdata'.format(bd_intf_prefix), width=self.mm2s_tdata_width)
        bd_inst.add_port('{:s}_tkeep'.format(top_intf_prefix), '{:s}_tkeep'.format(bd_intf_prefix), width=self.mm2s_tdata_width//4)
        bd_inst.add_port('{:s}_tlast'.format(top_intf_prefix), '{:s}_tlast'.format(bd_intf_prefix))
        bd_inst.add_port('{:s}_tready'.format(top_intf_prefix), '{:s}_tready'.format(bd_intf_prefix))
        bd_inst.add_port('{:s}_tvalid'.format(top_intf_prefix), '{:s}_tvalid'.format(bd_intf_prefix))

      # if the path for the connection is not in the current block design a port
      # must be made and the top module must expose it
      if len(self.s2mm['dest'].split('/')) == 1:
        top_intf_prefix = self.s2mm['dest'].lower()
        bd_intf_prefix = self.s2mm['dest']
        bd_inst.add_port('{:s}_awaddr'.format(top_intf_prefix), '{:s}_awaddr'.format(bd_intf_prefix),  width=40)
        bd_inst.add_port('{:s}_awprot'.format(top_intf_prefix), '{:s}_awprot'.format(bd_intf_prefix),  width=3)
        bd_inst.add_port('{:s}_awvalid'.format(top_intf_prefix), '{:s}_awvalid'.format(bd_intf_prefix))
        bd_inst.add_port('{:s}_awready'.format(top_intf_prefix), '{:s}_awready'.format(bd_intf_prefix))
        bd_inst.add_port('{:s}_wdata'.format(top_intf_prefix), '{:s}_wdata'.format(bd_intf_prefix),  width=32)
        bd_inst.add_port('{:s}_wstrb'.format(top_intf_prefix), '{:s}_wstrb'.format(bd_intf_prefix),  width=4)
        bd_inst.add_port('{:s}_wvalid'.format(top_intf_prefix), '{:s}_wvalid'.format(bd_intf_prefix))
        bd_inst.add_port('{:s}_wready'.format(top_intf_prefix), '{:s}_wready'.format(bd_intf_prefix))
        bd_inst.add_port('{:s}_bresp'.format(top_intf_prefix), '{:s}_bresp'.format(bd_intf_prefix),  width=2)
        bd_inst.add_port('{:s}_bvalid'.format(top_intf_prefix), '{:s}_bvalid'.format(bd_intf_prefix))
        bd_inst.add_port('{:s}_bready'.format(top_intf_prefix), '{:s}_bready'.format(bd_intf_prefix))
        bd_inst.add_port('{:s}_araddr'.format(top_intf_prefix), '{:s}_araddr'.format(bd_intf_prefix),  width=40)
        bd_inst.add_port('{:s}_arprot'.format(top_intf_prefix), '{:s}_arprot'.format(bd_intf_prefix),  width=3)
        bd_inst.add_port('{:s}_arvalid'.format(top_intf_prefix), '{:s}_arvalid'.format(bd_intf_prefix))
        bd_inst.add_port('{:s}_arready'.format(top_intf_prefix), '{:s}_arready'.format(bd_intf_prefix))
        bd_inst.add_port('{:s}_rdata'.format(top_intf_prefix), '{:s}_rdata'.format(bd_intf_prefix),  width=32)
        bd_inst.add_port('{:s}_rresp'.format(top_intf_prefix), '{:s}_rresp'.format(bd_intf_prefix),  width=2)
        bd_inst.add_port('{:s}_rvalid'.format(top_intf_prefix), '{:s}_rvalid'.format(bd_intf_prefix))
        bd_inst.add_port('{:s}_rready'.format(top_intf_prefix), '{:s}_rready'.format(bd_intf_prefix))


  def modify_bd(self, bd):
    bd.create_cell(self.blocktype, self.name)

    # apply configurations
    bd.add_raw_cmd('set_property -dict [list \\')
    bd.build_config_cmd(self, self.attr_map, None)
    bd.add_raw_cmd('] [get_bd_cells {:s}]'.format(self.name))

    # connect axi clocks
    bd.connect_net('pl_sys_clk', '{:s}/{:s}'.format(self.name, 's_axi_lite_aclk'))
    if self.enable_read:
      bd.connect_net('user_clk', '{:s}/{:s}'.format(self.name, 'm_axi_mm2s_aclk'))
      # TODO what are these resets?
      #bd.connect_net('axil_arst_n', '{:s}/{:s}'.format(self.name, 'mm2s_prmry_reset_out_n'))

    if self.enable_write:
      bd.create_net('m_axi_s2mm_aclk')
      bd.connect_net('m_axi_s2mm_aclk', '{:s}/{:s}'.format(self.name, 'm_axi_s2mm_aclk'))
      bd.connect_port('m_axi_s2mm_aclk', 'user_clk')
      # TODO what are these resets?
      #bd.connect_net('axil_arst_n', '{:s}/{:s}'.format(self.name, 's2mm_prmry_reset_out_n'))

    bd.connect_net('axil_arst_n', '{:s}/{:s}'.format(self.name, 'axi_resetn'))

    # connect interfaces
    bd.connect_intf_net(self.saxi_lite['dest'], '{:s}/{:s}'.format(self.name, 'S_AXI_LITE'))

    if self.enable_read:
      # if 'M_AXI_MM2S is to be external send it out, otherwise slave must make conection
      if len(self.mm2s['dest'].split('/')) == 1: # assumption used to know when to make pins external to bd
        intf_pin_name = '{:s}/{:s}'.format(self.name, 'M_AXI_MM2S')
        ext_intf_name = self.mm2s['dest']

        bd.create_intf_port(ext_intf_name, 'Master', 'axi4')

        bd.add_raw_cmd('set_property -dict [list \\')
        bd.add_raw_cmd('CONFIG.PROTOCOL [get_property CONFIG.PROTOCOL [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.ADDR_WIDTH [get_property CONFIG.ADDR_WIDTH [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.DATA_WIDTH [get_property CONFIG.DATA_WIDTH [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.HAS_BURST [get_property CONFIG.HAS_BURST [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.HAS_LOCK [get_property CONFIG.HAS_LOCK [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.HAS_PROT [get_property CONFIG.HAS_PROT [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.HAS_CACHE [get_property CONFIG.HAS_CACHE [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.HAS_QOS [get_property CONFIG.HAS_QOS [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.HAS_REGION [get_property CONFIG.HAS_REGION [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.SUPPORTS_NARROW_BURST [get_property CONFIG.SUPPORTS_NARROW_BURST [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.MAX_BURST_LENGTH [get_property CONFIG.MAX_BURST_LENGTH [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        # there is a bug, ideally this would have worked, but the parameter propagation has not happened for the clock field
        #bd.add_raw_cmd('CONFIG.FREQ_HZ [get_property CONFIG.FREQ_HZ [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name)))
        bd.add_raw_cmd('CONFIG.FREQ_HZ $ps_freq_hz \\') # TODO ASSUMES $ps_freq_hz is defined
        bd.add_raw_cmd('] [get_bd_intf_ports {:s}]'.format(ext_intf_name))

        bd.connect_intf_net('{:s}'.format(intf_pin_name), ext_intf_name)

      if len(self.axis_mm2s['dest'].split('/')) == 1:
        intf_pin_name = '{:s}/{:s}'.format(self.name, 'M_AXIS_MM2S')
        ext_intf_name = self.axis_mm2s['dest']

        bd.create_int_port(ext_intf_name, 'Master', 'axis')
        # TODO anything to do to config AXIS ports like an AXI4/Lite interface?
        bd.connect_intf_net('{:s}'.format(intf_pin_name), ext_intf_name)


    if self.enable_write:
      # if we are going out to the user design we need a port here or need to go
      # to an axi streaming data switch

      if len(self.axis_s2mm['dest'].split('/')) == 1: # assumption used to know when to make pins external to bd
        intf_pin_name = '{:s}/{:s}'.format(self.name, 'S_AXIS_S2MM')
        ext_intf_name = self.axis_s2mm['dest']

        bd.create_intf_port(ext_intf_name, 'Slave', 'axis')
        # TODO anything to do to config AXIS ports like AXI4/LITE interface?
        bd.connect_intf_net('{:s}'.format(intf_pin_name), ext_intf_name)

      # if 'M_AXI_S2MM is to be external send it out, otherwise slave must make conection
      if len(self.s2mm['dest'].split('/')) == 1: # assumption used to know when to make pins external to bd
        intf_pin_name = '{:s}/{:s}'.format(self.name, 'M_AXI_S2MM')
        ext_intf_name = self.s2mm['dest']

        bd.create_intf_port(ext_intf_name, 'Master', 'axi4')

        bd.add_raw_cmd('set_property -dict [list \\')
        bd.add_raw_cmd('CONFIG.PROTOCOL [get_property CONFIG.PROTOCOL [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.ADDR_WIDTH [get_property CONFIG.ADDR_WIDTH [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.DATA_WIDTH [get_property CONFIG.DATA_WIDTH [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.HAS_BURST [get_property CONFIG.HAS_BURST [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.HAS_LOCK [get_property CONFIG.HAS_LOCK [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.HAS_PROT [get_property CONFIG.HAS_PROT [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.HAS_CACHE [get_property CONFIG.HAS_CACHE [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.HAS_QOS [get_property CONFIG.HAS_QOS [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.HAS_REGION [get_property CONFIG.HAS_REGION [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.SUPPORTS_NARROW_BURST [get_property CONFIG.SUPPORTS_NARROW_BURST [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        bd.add_raw_cmd('CONFIG.MAX_BURST_LENGTH [get_property CONFIG.MAX_BURST_LENGTH [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name))
        # there is a bug, ideally this would have worked, but the parameter propagation has not happened for the clock field
        #bd.add_raw_cmd('CONFIG.FREQ_HZ [get_property CONFIG.FREQ_HZ [get_bd_intf_pins {:s}]] \\'.format(intf_pin_name)))
        bd.add_raw_cmd('CONFIG.FREQ_HZ $ps_freq_hz \\') # TODO ASSUMES $ps_freq_hz is defined
        bd.add_raw_cmd('] [get_bd_intf_ports {:s}]'.format(ext_intf_name))

        bd.connect_intf_net('{:s}'.format(intf_pin_name), ext_intf_name)

  def gen_children(self):
    children = []
    return children


  def gen_constraints(self):
    cons = []
    return cons


  def gen_tcl_cmds(self):
    tcl_cmds = {}
    tcl_cmds['init'] = []
    tcl_cmds['create_bd'] = []
    tcl_cmds['pre_synth'] = []
    return tcl_cmds

