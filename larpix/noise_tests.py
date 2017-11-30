'''
Run basic noise tests for chips
  Note: Reset chips before each test.
'''

from __future__ import absolute_import
from larpix.quickstart import quickcontroller
import time


def scan_threshold(board='pcb-5', chip_idx=0, channel_list=[0,],
                   threshold_min_coarse=30, threshold_max_coarse=35,
                   threshold_step_coarse=1):
    '''Scan the signal rate versus channel threshold'''
    # Create controller and initialize chips to appropriate state
    controller = quickcontroller(board)
    print('created controller')
    # Get chip under test
    chip = controller.chips[chip_idx]
    results = {}
    for channel in channel_list:
        print('testing channel',channel)
        # Configure chip for one channel operation
        chip.config.channel_mask = [1,]*32
        chip.config.channel_mask[channel] = 0
        print('writing config')
        controller.write_configuration(chip,[52,53,54,55])
        print('reading config')
        controller.read_configuration(chip)
        print('set mask')
        # Scan thresholds
        thresholds = range(threshold_min_coarse,
                           threshold_max_coarse,
                           threshold_step_coarse)
        # Scan from high to low
        thresholds.reverse()
        # Prepare to scan
        n_packets = []
        adc_means = []
        adc_rmss = []
        for threshold in thresholds:
            # Set global coarse threshold
            chip.config.global_threshold = threshold
            controller.write_configuration(chip,32)
            print('set threshold')
            if threshold == thresholds[0]:
                # Flush buffer for first cycle
                print('clearing buffer')
                controller.run(1,'clear buffer')
                time.sleep(1)
            controller.reads = []
            # Collect data
            print('reading')
            controller.run(1,'scan threshold')
            print('done reading')
            # Process data
            packets = controller.reads[-1]
            adc_mean = 0
            adc_rms = 0
            if len(packets)>0:
                print('processing packets',len(packets))
                adcs = [p.dataword for p in packets]
                adc_mean = sum(adcs)/float(len(adcs))
                adc_rms = (sum([abs(adc-adc_mean) for adc in adcs])
                           / float(len(adcs)))
            n_packets.append(len(packets))
            adc_means.append(adc_mean)
            adc_rmss.append(adc_rms)
            print('%d %d %0.2f %0.4f' % (threshold, len(packets),
                                         adc_mean, adc_rms))
        results[channel] = [thresholds[:], n_packets[:],
                            adc_means[:], adc_rmss[:]] 
    return results
    

def pixel_trim_scan(coarse_scan, board='pcb-5', chip_idx=0,
        channel_list=[0]):
    '''Scan through the pixel trim DACs near the threshold for each
    channel, given the results of the coarse scan (scan_threshold).

    '''
    #TODO channel_list might contain channels not in coarse_scan
    controller = quickcontroller(board)
    chip = controller.chips[chip_idx]
    results = {}
    for channel, values in coarse_scan.items():
        if channel not in channel_list:
            continue
        chip.config.disable_channels()
        chip.config.enable_channels([channel])
        # Find the noise threshold
        global_thresholds = values[0]
        npackets = values[1]
        for i, npacket in enumerate(npackets):
            if npacket > 0:
                last_good_threshold = global_thresholds[i - 1]
                break
        chip.config.global_threshold = last_good_threshold
        controller.write_configuration(chip)
        # Scan the trim dac below the "initial" value to explore how the
        # noise changes
        initial_trim_dac = chip.config.pixel_trim_thresholds[channel]
        extra_dacs = 5
        n_packets = []
        adc_means = []
        adc_rmss = []
        for trim_dac in range(initial_trim_dac + extra_dacs):
            chip.config.pixel_trim_thresholds[channel] = trim_dac
            controller.write_configuration(chip, channel)
            if trim_dac == 0:
                # Flush buffer for first cycle
                print('clearing buffer')
                controller.run(1,'clear buffer')
                time.sleep(1)
            controller.reads = []
            # Collect data
            print('reading')
            controller.run(1,'scan threshold')
            print('done reading')
            # Process data
            packets = controller.reads[-1]
            adc_mean = 0
            adc_rms = 0
            if len(packets)>0:
                print('processing packets',len(packets))
                adcs = [p.dataword for p in packets]
                adc_mean = sum(adcs)/float(len(adcs))
                adc_rms = (sum([abs(adc-adc_mean) for adc in adcs])
                           / float(len(adcs)))
            n_packets.append(len(packets))
            adc_means.append(adc_mean)
            adc_rmss.append(adc_rms)
        results[channel] = [list(range(initial_trim_dac)), n_packets[:],
                            adc_means[:], adc_rmss[:]]
    return results


def pulse_chip_channel(controller, chip, channel):
    '''Issue one pulse to specific chip, channel'''
    chip.config.csa_testpulse_enable[channel] = 0 # Connect
    controller.write_configuration(chip,[42,43,44,45])
    chip.config.csa_testpulse_enable[channel] = 1 # Disconnect
    controller.write_configuration(chip,[42,43,44,45],write_read=0.1)
    return

def noise_test_internal_pulser(board='pcb-5', chip_idx=0, n_pulses=1000,
                               pulse_channel=0, pulse_dac=200, threshold=100):
    '''Use cross-trigger from one channel to evaluate noise on other channels'''
    # Create controller and initialize chips to appropriate state
    controller = quickcontroller(board)
    # Get chip under test
    chip = controller.chips[chip_idx]
    # Configure chip for pulsing one channel, and issuing cross-triggers
    chip.config.global_threshold = threshold
    chip.config.csa_testpulse_dac_amplitude = pulse_dac
    chip.config.cross_trigger_mode = 1
    controller.write_configuration(chip,[32,46,47])
    # Pulse chip n times
    for pulse_idx in range(n_pulses):
        pulse_chip_channel(controller, chip, pulse_channel)
    # Keep a handle to chip data, and return
    result = controller.reads
    return result

if '__main__' == __name__:
    # Run test
    result1 = scan_threshold()
    # result2 = noise_test_internal_pulser()
