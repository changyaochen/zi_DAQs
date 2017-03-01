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
from open_loop_sweep_2ch import open_loop_sweep_2ch
import os
import pandas as pd
import bokeh.plotting as bkp
import bokeh.models as bkm

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

# ==================== parameters setting ====================
freq_pre_start = 27e3
freq_pre_stop = 31.7e3
demod = 1
freq_IR_gap = 250
freq_d_num = 1
vac = 0.71
# ==================== done setting =====================


# first need to bring the freq to right before IR
output_pre_1, output_pre_2 = open_loop_sweep_2ch(                               
                                device_id= 'dev267', 
                                demod_channel_1 = demod, out_channel_1 = 1, 
                                demod_channel_2 = demod+3, out_channel_2 = 2,
                                amplitude = vac, 
                                start_freq = freq_pre_start, stop_freq = freq_pre_stop + 500,
                                out_range = 1, avg_sample = 3, avg_tc = 3,
                                samplecount = 5*(freq_pre_stop + 500 - freq_pre_start),
                                tc = 0.005, rate = 2000, 
                                do_plot = False)
# plot the pre_sweep result
# only to extract certain fields from the raw output
headers = ['frequency', 'x', 'y']
data_pre_1 = pd.DataFrame.from_dict({x: output_pre_1[0][0][x] for x in headers})
data_pre_1['r'] = np.sqrt(data_pre_1['x']**2 + data_pre_1['x']**2)
data_pre_2 = pd.DataFrame.from_dict({x: output_pre_2[0][0][x] for x in headers})
data_pre_2['r'] = np.sqrt(data_pre_2['x']**2 + data_pre_2['x']**2)

# save the data
data_pre_1.to_csv(handle + '_ch1.txt', sep = '\t', index = False)
data_pre_2.to_csv(handle + '_ch2.txt', sep = '\t', index = False)

# make plot
source = bkm.ColumnDataSource(data_pre_1)
bkp.output_file(handle + '_ch1_pre.html')
p = bkp.figure(plot_height = 600, plot_width = 800, 
               x_axis_label = 'Frequency (Hz)', y_axis_label = 'R_1 (V)',
               tools = 'pan, box_zoom, reset, save, hover')
p.circle('frequency', 'r', source=source, size = 5, alpha = 0.5)
hover = p.select(dict(type = bkm.HoverTool))
hover.tooltips = [('Frequency (Hz)','@frequency{0.00}'), ('r (V)', '@r')]
bkp.save(p)


source = bkm.ColumnDataSource(data_pre_2)
bkp.output_file(handle + '_ch2_pre.html')
p = bkp.figure(plot_height = 600, plot_width = 800, 
               x_axis_label = 'Frequency (Hz)', y_axis_label = 'R_2 (V)',
               tools = 'pan, box_zoom, reset, save, hover')
p.circle('frequency', 'r', source=source, size = 5, alpha = 0.5)
hover = p.select(dict(type = bkm.HoverTool))
hover.tooltips = [('Frequency (Hz)','@frequency{0.00}'), ('r (V)', '@r')]
bkp.save(p)


# Now let's start taking the frequency comb measurement!
# let's come back where we were, but don't save the data
open_loop_sweep_2ch(                               
                    device_id= 'dev267', 
                    demod_channel_1 = demod, out_channel_1 = 1, 
                    demod_channel_2 = demod+3, out_channel_2 = 2,
                    amplitude = vac, 
                    start_freq = freq_pre_start, stop_freq = freq_pre_stop,
                    out_range = 1, avg_sample = 3, avg_tc = 3,
                    samplecount = 5*(freq_pre_stop - freq_pre_start),
                    tc = 0.005, rate = 2000, 
                    do_plot = False)
# first I need to increase the LPF BW
LPF_BW = 500  # unit Hz
tc = 1/2/np.pi/LPF_BW/3.3  
rate = 5000  # data transfer rate
exp_sigOutIn_setting = [
            # input (demods) settings
       [['/', device, '/demods/',str(demod-1),'/timeconstant'], tc],  # equil. to LPF BW
       [['/', device, '/demods/',str(demod-1),'/rate'], rate],  # streaming rate
                              ]
# pass the setting in
daq.set(exp_sigOutIn_setting)

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
    

