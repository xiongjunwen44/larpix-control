import json
import numpy as np
import matplotlib.pyplot as plt

def dict_keys_to_int(x):
    '''
    Return a dict identical to the input dict but whose keys are
    ints.

    '''
    new_dict = {}
    for key in x.keys():
        new_dict[int(key)] = x[key]
    return new_dict

def threshold(global_threshold, trim_threshold, temp_K=293, vdda_V=1.5,
        bias_uA=2.16, units='V'):
    '''
    Compute the threshold voltage according to the LArPix Datasheet.

    '''
    global_threshold_V = vdda_V * global_threshold/256
    temp_term = -0.18 * np.log(temp_K) + 1.14
    trim_term = 0.0012 * trim_threshold * bias_uA/2.16
    threshold_V =  global_threshold_V + temp_term + trim_term
    if units == 'V':
        return threshold_V
    elif units == 'mV':
        return threshold_V * 1000
    else:
        raise ValueError('Bad units: %s' % units)

def main():
    coarse_scan_files = ['coarse_scan.json']
    fine_scan_up_files = ['fine_scan.json',
            'fine_scan_2.json']
    fine_scan_down_files = ['fine_scan_down.json',
            'fine_scan_down2.json']
    coarse_scan_data = []
    fine_scan_up_data = []
    fine_scan_down_data = []
    for name in coarse_scan_files:
        with open(name, 'r') as fin:
            coarse_scan_data.append(json.load(fin,
                object_hook=dict_keys_to_int))
    for name in fine_scan_up_files:
        with open(name, 'r') as fin:
            fine_scan_up_data.append(json.load(fin,
                object_hook=dict_keys_to_int))
    for name in fine_scan_down_files:
        with open(name, 'r') as fin:
            fine_scan_down_data.append(json.load(fin,
                object_hook=dict_keys_to_int))

    fine_scan_up_trims = list(range(21))
    fine_scan_down_trims = list(range(21, -1, -1))

    for channel in range(32):
        coarse_values = [d[channel] for d in coarse_scan_data][0]
        fine_scan_up_values = [d[channel] for d in fine_scan_up_data]
        fine_scan_down_values = [d[channel] for d in fine_scan_down_data]
        global_thresholds = coarse_values[0]
        npackets = coarse_values[1]
        for i, npacket in enumerate(npackets):
            if npacket > 0:
                last_good_threshold = global_thresholds[i-1]
                break
        fine_scan_up_npackets = [x[1] for x in fine_scan_up_values]
        fine_scan_down_npackets = [x[1] for x in fine_scan_down_values]

        fine_scan_up_voltages = [threshold(last_good_threshold, trim,
            vdda_V=1.38, units='mV') for trim in fine_scan_up_trims]
        fine_scan_down_voltages = [threshold(last_good_threshold, trim,
            vdda_V=1.38, units='mV') for trim in fine_scan_down_trims]


        plt.figure(figsize=(14, 10))
        for npackets in fine_scan_up_npackets:
            plt.plot(fine_scan_up_voltages, npackets)
        for npackets in fine_scan_down_npackets:
            plt.plot(fine_scan_down_voltages, npackets)

        yscale = 'log'
        if yscale == 'log':
            plt.ylim([0.5, 20000])
            plt.yscale('log')
        plt.xlim([261, 338])
        plt.xticks(fontsize=18)
        plt.yticks(fontsize=18)
        plt.title('Threshold scans for channel %d' % channel,
                fontsize=24)
        plt.xlabel('Threshold voltage (calculated) [mV]', fontsize=18)
        plt.ylabel('Number of packets received in 1 second', fontsize=18)
        plt.savefig('thresholds_ch%d_%s.pdf' % (channel, yscale))
        if channel % 8 == 0:
            plt.show()
        plt.close()


main()
