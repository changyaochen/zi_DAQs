# -*- coding: utf-8 -*-
"""
this is to do the open-loop sweep into IR
and with zi HF2LI's own zoomFFT module
to take the frequency spectrum
"""

import numpy as np
#import matplotlib.pyplot as plt
import zhinst.utils
#import zhinst.ziPython as zi
from zoomFFT import zoomfft
from open_loop_sweep import open_loop_sweep
import os
import pandas as pd
import bokeh.plotting as bkp

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# prompt to ask for path to save data
handle = input('saved file path/name: ')
if len(handle) == 0:
    handle = 'temp_freq_comb'
    
# create a folder for the results
if not os.path.exists(handle):
    os.makedirs(handle)
    os.chdir(dname + '/' + handle)
elif handle == 'temp_freq_comb':
    os.chdir(dname + '/' + handle)
else:
    raise Exception('Please input a valid file path/name!')

# to establish connection, the numbering is 0-indexed
# the default setting is: drive with sigout 1, whose freq is set by demod 3

# output data format, 3 columns
out_data = np.array([[],[],[]]).T
device_id = 'dev267'
(daq, device, props) = zhinst.utils.create_api_session(device_id, maximum_supported_apilevel = 1)

# ========== parameters setting ==========
freq_pre_start = 27e3
freq_pre_stop = 31.7e3
demod = 1
freq_IR_gap = 250
freq_d_num = 2
# ========== done setting ===========


# first need to bring the freq to right before IR
output_pre = open_loop_sweep(device_id= device_id, demod_channel = demod, 
                            out_channel = 1, amplitude = 1, 
                            start_freq = freq_pre_start, stop_freq = freq_pre_stop,
                            out_range = 1, avg_sample = 3, avg_tc = 3,
                            samplecount = 100,
                            do_plot = False)
# plot the pre_sweep result
# only to extract certain fields from the raw output
headers = ['frequency', 'x', 'y']
data_pre = pd.DataFrame.from_dict({x: output_pre[0][0][x] for x in headers})
data_pre['r'] = np.sqrt(data_pre['x']**2 + data_pre['x']**2)

# save the data
data_pre.to_csv(handle + '.txt', sep = '\t',
                   index = False)
# make plot
bkp.output_file(handle + '_pre.html')
p = bkp.figure(plot_height = 600, plot_width = 800, 
               x_axis_label = 'Frequency (Hz)', y_axis_label = 'R (V)',
               tools = 'pan, box_zoom, reset, hover, save')
p.circle(data_pre['frequency'], data_pre['r'], size = 3, alpha = 0.5)
bkp.save(p)

#assign the freqs!
freq_d_start = freq_pre_stop
freq_d_stop  = freq_pre_stop + freq_IR_gap

freq_ds = np.linspace(freq_d_start, freq_d_stop, freq_d_num+1)
for freq_d in freq_ds:
    print('progress: '+str(100.0*(freq_d - freq_d_start)/(freq_d_stop - freq_d_start))+'%')
    # set the frequency of oscillator 1
    setting_str = [[['/', device, '/oscs/0/freq'], freq_d]]  # default sigout is ch 1
    daq.set(setting_str)
    
    # do the actual FFT!
    freq, r = zoomfft(daq, device, demod_index = demod, timeout = float('inf'), 
            bits = 14,
            do_plot = False)
    temp_data = np.vstack((freq, r, freq_d * np.ones(freq.shape[0]))).T
    out_data = np.vstack((out_data, temp_data))
    # the data has 3 columns: (FFT_freq, FFT_r, drive_freq)
    np.savetxt(handle + '_FFTs.txt', out_data, newline = '\n')    # it will override any existing file
    

