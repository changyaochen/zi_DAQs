# -*- coding: utf-8 -*-
"""
Spyder Editor

Developed from from pump_probe_v2.py
Difference: after probe, I will take the FFT of the pump channel

This is for pump-probe measurement, with HF2LI
In this version, while I am probing (e.g. from channel 2),
I will also record the signal from the pumping channel (e.g. channel 1)
Therefore, later I can reconstruct the "pump" response



"""

from open_loop_sweep import open_loop_sweep
from open_loop_sweep_2ch import open_loop_sweep_2ch
from zoomFFT import zoomfft
import os
import numpy as np
import pandas as pd
import zhinst.utils
import bokeh.plotting as bkp
import bokeh.models as bkm
import zi_processing

# get the directories right
dname = os.path.dirname(os.path.abspath(__file__))
os.chdir(dname)

# prompt to ask for path to save data
handle = input('saved file path/name: ')
if len(handle) == 0:
    handle = 'temp_pump_probe_FFT'
    
# create a folder for the results
if not os.path.exists(handle):
    os.makedirs(handle)
    os.chdir(dname + '/' + handle)
elif handle == 'temp_pump_probe_FFT':
    os.chdir(dname + '/' + handle)
else:
    raise Exception('Please input a valid file path/name!')

device_id= 'dev267'
api_level = 1
(daq, device, props) = zhinst.utils.create_api_session(device_id, api_level); 
# ================== pump settings ====================================
pump_out_ch = 1
pump_in_ch = 1
pump_in_demod = 1
pump_ac = 1
pump_pre_freq_start = 27e3
pump_pre_freq_stop = 31.6e3
pump_samplecount = 3000

pump_freq_gap = 300
# ========================================================================

# ================== probe settings ====================================
probe_out_ch = 2
probe_in_ch = 2
probe_in_demod = 4
probe_ac = 0.1
probe_freq_start = 31.83e3
probe_freq_stop = 31.89e3
probe_samplecount = 1500
inplace_fit = True
# ========================================================================

# ===== start ======

# first bring the pump condition right before IR
result_pre = open_loop_sweep(device_id= 'dev267', demod_channel = pump_in_demod, 
                   out_channel = pump_out_ch, sigin_channel = pump_in_ch, 
                   amplitude = pump_ac, 
                    start_freq = pump_pre_freq_start, stop_freq = pump_pre_freq_stop,
                    out_range = 1, avg_sample = 5, avg_tc = 15,
                    samplecount = pump_samplecount)
# save the 'pre' data
headers = ['frequency', 'x', 'y']
data_pre_1 = pd.DataFrame.from_dict({x: result_pre[0][0][x] for x in headers})
data_pre_1['r'] = np.sqrt(data_pre_1['x']**2 + data_pre_1['x']**2)
data_pre_1.to_csv(handle + '_ch1_pre.txt', sep = '\t', index = False)

# make plot
source = bkm.ColumnDataSource(data_pre_1)
bkp.output_file(handle + '_ch1_pre.html')
p = bkp.figure(plot_height = 600, plot_width = 800, 
               x_axis_label = 'Frequency (Hz)', y_axis_label = 'R_1 (V)',
               tools = 'pan, box_zoom, reset, resize, save, hover')
p.circle('frequency', 'r', source=source, size = 5, alpha = 0.5)
hover = p.select(dict(type = bkm.HoverTool))
hover.tooltips = [('Frequency (Hz)','@frequency{0.00}'), ('r (V)', '@r')]
bkp.save(p)


# start the pump probe
pump_freqs = np.linspace(pump_pre_freq_stop, pump_pre_freq_stop + pump_freq_gap,
                         pump_freq_gap+1)
# initilization for the mega file 
mega_file = pd.DataFrame()
mega_file_pump = pd.DataFrame()

# initialization for the fitted result
fitted_results =[]
# output data format for FFT (megafile), 3 columns
out_data = np.array([[],[],[]]).T

for freq in pump_freqs:
    # set the pump freq
    print('Pump frequency is {:10.2f} Hz'.format(freq))
    exp_sigOutIn_setting = [[['/', device, '/oscs/',str(pump_out_ch-1),'/freq'], freq]]
    daq.set(exp_sigOutIn_setting)
    
    # probe
    result, result_pump =  open_loop_sweep_2ch(
                        device_id= 'dev267', 
                        demod_channel_1 = probe_in_demod, 
                        out_channel_1 = probe_out_ch, 
                        in_channel_1 = probe_in_ch, 
                        demod_channel_2 = pump_in_demod, 
                        out_channel_2 = pump_out_ch, 
                        in_channel_2 = pump_in_ch,
                        amplitude = probe_ac, 
                        start_freq = probe_freq_start, stop_freq = probe_freq_stop,
                        out_range = 0.1, avg_sample = 4, avg_tc = 15,
                        samplecount = probe_samplecount,
                            )
    # take zoomFFT of pump channel
    # first I need to increase the LPF BW
    LPF_BW = 500  # unit Hz
    tc = 1/2/np.pi/LPF_BW/3.3  
    rate = 5000  # data transfer rate
    exp_sigOutIn_setting = [
            # input (demods) settings
       [['/', device, '/demods/',str(pump_in_demod-1),'/timeconstant'], tc],  # equil. to LPF BW
       [['/', device, '/demods/',str(pump_in_demod-1),'/rate'], rate],  # streaming rate
                              ]
    # pass the setting in
    daq.set(exp_sigOutIn_setting)
    
    # do the actual FFT
    FFT_freq, r = zoomfft(daq, device, demod_index = pump_in_demod, timeout = float('inf'), 
            bits = 14,
            do_plot = False)
    temp_data = np.vstack((FFT_freq, r, freq * np.ones(FFT_freq.shape[0]))).T
    out_data = np.vstack((out_data, temp_data))
    # the data has 3 columns: (FFT_freq, FFT_r, drive_freq)
    # save the single FFT data - this is the megasweep-type file
    np.savetxt(handle + '_probe_pump_at_'+str(round(freq,2)) + '_FFTs.txt', 
               temp_data, newline = '\n')    # this is single zoomFFT data
    np.savetxt(handle + '_mega_FFTs.txt', 
               out_data, newline = '\n')    # it will override any existing file

    # save data
    # save the single probe data
    data_probe = pd.DataFrame.from_dict({x: result[0][0][x] for x in headers})
    data_probe['r'] = np.sqrt(data_probe['x']**2 + data_probe['y']**2)
    data_probe.to_csv(handle + '_probe_pump_at_'+str(round(freq,2))+'Hz.txt', 
                      sep = '\t', index = False)
    
    # save the single pump data
    data_pump = pd.DataFrame.from_dict({x: result_pump[0][0][x] for x in headers})
    data_pump['r'] = np.sqrt(data_pump['x']**2 + data_pump['y']**2)
    data_pump.to_csv(handle + '_pump_pump_at_'+str(round(freq,2))+'Hz.txt', 
                      sep = '\t', index = False)
    
    if inplace_fit:
        # fit the data to a Lorentz curve
        p_fit, p_err = zi_processing.fit_lorentz_sweeper(data_probe, showHTML = False, 
                                          figure_name = handle + '_probe_pump_at_'+str(round(freq,2))+'Hz',
                                          zoom_in_fit=False)        
        A, f0, Q, bkg = [x for x in p_fit]
        A_err, f0_err, Q_err, bkg_err = [x for x in p_err]
        fitted_results.append([freq, f0, f0_err, Q, Q_err])
        
    # make plot for the 'pump' data
    source = bkm.ColumnDataSource(data_pump)
    bkp.output_file(handle + '_pump_when_probed_at_'+str(round(freq,2))+'Hz.html')
    p = bkp.figure(plot_height = 600, plot_width = 800, 
                   x_axis_label = 'Pump Frequency (Hz)', y_axis_label = 'R_1 (V)',
                   tools = 'pan, box_zoom, reset, resize, save, hover')
    p.circle('frequency', 'r', source=source, size = 5, alpha = 0.5)
    hover = p.select(dict(type = bkm.HoverTool))
    hover.tooltips = [('Frequency (Hz)','@frequency{0.00}'), ('r (V)', '@r')]
    bkp.save(p)
    
    # save the mega file data
    data_probe['pump_freq(Hz)'] = freq
    data_pump['pump_freq(Hz)'] = freq
    if mega_file.size == 0:  # first time
        mega_file = data_probe
        mega_file_pump = data_pump
    else:
        mega_file = mega_file.append(data_probe, ignore_index = True)
        mega_file_pump = mega_file_pump.append(data_pump, ignore_index = True)
        
    # save the mega file data
    mega_file.to_csv(handle + '_pump_probe_mega.txt', sep = '\t', 
                   index = False, headers = False)
    mega_file_pump.to_csv(handle + '_pump_pump_mega.txt', sep = '\t', 
                   index = False, headers = False)
    # save the fitted result
    fitted_results_df = pd.DataFrame(fitted_results, columns = ['pump_freq(Hz)', 'f0(Hz)', 'f0_err(Hz)',
                                       'Q', 'Q_err'])
    fitted_results_df.to_csv(handle + '_fitted_results.txt', sep = '\t', 
               index = False)
    
# post sweep, to go over IR
result_post = open_loop_sweep(device_id= 'dev267', demod_channel = pump_in_demod, 
                   out_channel = pump_out_ch, sigin_channel = pump_in_ch, 
                   amplitude = pump_ac, 
                    start_freq = pump_pre_freq_start, 
                    stop_freq = pump_pre_freq_stop + pump_freq_gap,
                    out_range = 1, avg_sample = 5, avg_tc = 15,
                    samplecount = pump_samplecount + \
                    int(pump_freq_gap/(pump_pre_freq_stop - pump_pre_freq_start))
                    )
# save the 'post' data
headers = ['frequency', 'x', 'y']
data_post_1 = pd.DataFrame.from_dict({x: result_post[0][0][x] for x in headers})
data_post_1['r'] = np.sqrt(data_post_1['x']**2 + data_post_1['y']**2)
data_post_1.to_csv(handle + '_ch1_post.txt', sep = '\t', index = False)

# make plot
source = bkm.ColumnDataSource(data_post_1)
bkp.output_file(handle + '_ch1_post.html')
p = bkp.figure(plot_height = 600, plot_width = 800, 
               x_axis_label = 'Frequency (Hz)', y_axis_label = 'R_1 (V)',
               tools = 'pan, box_zoom, reset, resize, save, hover')
p.circle('frequency', 'r', source=source, size = 5, alpha = 0.5)
hover = p.select(dict(type = bkm.HoverTool))
hover.tooltips = [('Frequency (Hz)','@frequency{0.00}'), ('r (V)', '@r')]
bkp.save(p)