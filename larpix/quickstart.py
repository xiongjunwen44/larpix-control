'''
Quickstart commands for test boards
'''

from __future__ import absolute_import
import larpix.larpix as larpix
from larpix.tasks import get_chip_ids


#List of LArPix test board configurations
board_info_list = [
    {'name':'unknown',
     'chip_list':[(chip_id,0) for chip_id in range(0,256)],},
    {'name':'pcb-5',
     'chip_list':[(246,0),(245,0),(252,0),(243,0)],},
    {'name':'pcb-4',
     'chip_list':[(207,0),(63,0),(250,0),(249,0)],},
]

#Create handy map by board name
board_info_map = dict([(elem['name'],elem) for elem in board_info_list])

# Guess default port name by platform
port_map = {
    'Default':['/dev/ttyUSB2',],     # Same as Linux
    'linux':['/dev/ttyUSB2',],       # Linux
    'Darwin':['/dev/tty.usbserial',
              '/dev/tty.usbserial-FTHC2IO2',
              '/dev/cu.usbserial-FTHC2IO2',
              '/dev/tty.usbserial-FT1CHRTN',], # OS X
}

def guess_port():
    '''Guess at correct port name based on platform'''
    import platform, os
    platform_default = 'Default'
    platform_name = platform.system()
    if platform_name not in port_map:
        platform_name = platform_default
    default_devs = port_map[platform_name]
    for default_dev in default_devs:
        try:
            if os.stat(default_dev):
                return default_dev
        except OSError:
            continue
    raise OSError('Cannot find serial device for platform: %s' % platform_name)

def create_controller():
    '''Create a default controller'''
    return larpix.Controller(port=guess_port())

def init_controller(controller, board='pcb-5'):
    '''Initialize controller'''
    if not board_info_map.has_key(board):
        board = 'unknown'
    board_info = board_info_map[board]
    for chip_info in board_info['chip_list']:
        controller.chips.append( larpix.Chip(chip_info[0],chip_info[1]) )
    controller.board_info = board_info
    return controller
        
def silence_chips(controller):
    '''Silence all chips in controller'''
    for chip in controller.chips:
        chip.config.global_threshold = 255
        controller.write_configuration(chip,32)
    return

def set_config_physics(controller):
    '''Set the chips for the default physics configuration'''
    #import time
    for chip in controller.chips:
        #chip.config.load("physics.json") # FIXME: doesn't exist in head
        #controller.write_configuration(chip)
        chip.config.internal_bypass = 1
        controller.write_configuration(chip,33)
        chip.config.periodic_reset = 1
        controller.write_configuration(chip,47)
        chip.config.global_threshold = 60
        controller.write_configuration(chip,32)
        #time.sleep(2)
        print('done chip %d' % chip.chip_id)
    return

def flush_stale_data(controller):
    '''Read and discard buffer contents'''
    controller.run(1,'flush_buffer')
    controller.reads = []
    return
    
def quickcontroller(board='pcb-5'):
    '''Quick jump through all controller creation and config steps'''
    cont = create_controller()
    init_controller(cont,board)
    silence_chips(cont)
    if cont.board_info['name'] == 'unknown':
        # Find and load chip info
        settings = {'controller':cont}
        cont.chips = get_chip_ids(**settings)
    set_config_physics(cont)
    flush_stale_data(cont)
    return cont

# Short-cut handle
qc = quickcontroller

