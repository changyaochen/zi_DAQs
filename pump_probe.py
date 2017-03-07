# -*- coding: utf-8 -*-
"""
Spyder Editor

This is for pump-probe measurement, with HF2LI

"""

from open_loop_sweep import open_loop_sweep
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
    handle = 'temp_pump_probe'
    
# create a folder for the results
if not os.path.exists(handle):
    os.makedirs(handle)
    os.chdir(dname + '/' + handle)
elif handle == 'temp_pump_probe':
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
pump_samplecount = 2000

pump_freq_gap = 400
# ========================================================================

# ================== probe settings ====================================
probe_out_ch = 2
probe_in_ch = 2
probe_in_demod = 4
probe_ac = 0.05
probe_freq_start = 31.8e3
probe_freq_stop = 31.9e3
probe_samplecount = 2000
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
data_pre_1['r'] = np.sqrt(data_pre_1['x']**2 + data_pre_1['y']**2)
data_pre_1.to_csv(handle + '_ch1_pre.txt', sep = '\t', index = False)

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


# start the pump probe
pump_freqs = np.linspace(pump_pre_freq_stop, pump_pre_freq_stop + pump_freq_gap,
                         pump_freq_gap+1)
# initilization for the mega file 
mega_file = pd.DataFrame()
# initialization for the fitted result
fitted_results =[]

for freq in pump_freqs:
    # set the pump freq
    print('Pump frequency is {:10.2f} Hz'.format(freq))
    exp_sigOutIn_setting = [[['/', device, '/oscs/',str(pump_out_ch-1),'/freq'], freq]]
    daq.set(exp_sigOutIn_setting)
    
    # probe
    result =  open_loop_sweep(device_id= 'dev267', demod_channel = probe_in_demod, 
                   out_channel = probe_out_ch, sigin_channel = probe_in_ch, 
                   amplitude = probe_ac, 
                    start_freq = probe_freq_start, stop_freq = probe_freq_stop,
                    out_range = 0.1, avg_sample = 5, avg_tc = 15,
                    samplecount = probe_samplecount,
                    do_plot = False)
    # save data
    # save the single probe data
    data_probe = pd.DataFrame.from_dict({x: result[0][0][x] for x in headers})
    data_probe['r'] = np.sqrt(data_probe['x']**2 + data_probe['y']**2)
    data_probe.to_csv(handle + '_probe_pump_at_'+str(round(freq,2))+'Hz.txt', 
                      sep = '\t', index = False)
    if inplace_fit:
        # fit the data to a Lorentz curve
        p_fit, p_err = zi_processing.fit_lorentz_sweeper(data_probe, showHTML = False, 
                                          figure_name = handle + '_probe_pump_at_'+str(round(freq,2))+'Hz',
                                          zoom_in_fit=False)        
        A, f0, Q, bkg = [x for x in p_fit]
        A_err, f0_err, Q_err, bkg_err = [x for x in p_err]
        fitted_results.append([freq, f0, f0_err, Q, Q_err])
    
    # save the mega file data
    data_probe['pump_freq(Hz)'] = freq
    if mega_file.size == 0:  # first time
        mega_file = data_probe
    else:
        mega_file = mega_file.append(data_probe, ignore_index = True)
        
    # save the mega file data
    mega_file.to_csv(handle + '_pump_probe_mega.txt', sep = '\t', 
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
# save the 'pre' data
headers = ['frequency', 'x', 'y']
data_post_1 = pd.DataFrame.from_dict({x: result_post[0][0][x] for x in headers})
data_post_1['r'] = np.sqrt(data_post_1['x']**2 + data_post_1['y']**2)
data_post_1.to_csv(handle + '_ch1_post.txt', sep = '\t', index = False)

# make plot
source = bkm.ColumnDataSource(data_post_1)
bkp.output_file(handle + '_ch1_post.html')
p = bkp.figure(plot_height = 600, plot_width = 800, 
               x_axis_label = 'Frequency (Hz)', y_axis_label = 'R_1 (V)',
               tools = 'pan, box_zoom, reset, save, hover')
p.circle('frequency', 'r', source=source, size = 5, alpha = 0.5)
hover = p.select(dict(type = bkm.HoverTool))
hover.tooltips = [('Frequency (Hz)','@frequency{0.00}'), ('r (V)', '@r')]
bkp.save(p)