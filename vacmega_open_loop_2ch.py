# -*- coding: utf-8 -*-
"""
This is for multiple open loop sweep with different vac
the inputs are from both channels, therefore I am going to record
the results simultanetansouly from multiple demods
with the function open_loop_sweep_2ch()

@author: changyao chen
"""

from open_loop_sweep_2ch import open_loop_sweep_2ch
import os
import numpy as np
import pandas as pd
import zi_processing

# get the directories right
dname = os.path.dirname(os.path.abspath(__file__))
os.chdir(dname)
device_id= 'dev267'


# ===== global setting =======
_debug_ = True   
vac_list = np.linspace(0.01, 0.51, 2)
start_freq = 27.00e3
stop_freq = 40.00e3
samplecount = 13000
avg_sample= 3
if _debug_:
    vac_list = [0.1]; samplecount = 100  # for debug purpose
inplace_fit = False  # whether to do Lorentz fit for each sweep
# ==============================

# I will save the output into 2 types of files:
# for the first type, each vac has its own file
# for the second type is the usual megasweep format (single file)
# 
# with vac attached to the file name

# initilization for the type_II_ch1 and _ch2 data
type_II_ch1 = pd.DataFrame()
type_II_ch2 = pd.DataFrame()
# initialize output file
fitted_results_ch1 = []
fitted_results_ch2 = []

# only to extract certain fields from the raw output
headers = ['frequency', 'x', 'y']

# prompt to ask for path to save data
handle = input('saved file path/name: ')
if len(handle) == 0:
    handle = 'temp'
    
# create a folder for the results
if not os.path.exists(handle):
    os.makedirs(handle)
    os.chdir(dname + '/' + handle)
elif handle == 'temp':
    os.chdir(dname + '/' + handle)
else:
    raise Exception('Please input a valid file path/name!')
        
# I need to somehow save the experiment parameters...
parameters = { # default values
        'avg_sample': 10, 
        'avg_tc': 15,
        'samplecount': 1000,
        'tc': 0.005, 
        'rate': 2000
        }
# update the default values
parameters['samplecount'] = samplecount 
parameters['start_freq'] =  start_freq
parameters['stop_freq'] =  stop_freq
parameters['avg_sample'] =  avg_sample


for vac in vac_list:
    # run one open loop sweep
    # the return result is a list, and its [0][0] element is the dict
    # that is of interest
    result_1, result_2 = open_loop_sweep_2ch(device_id = 'dev267', 
                                             start_freq = start_freq, stop_freq = stop_freq,
                                             amplitude=vac, avg_sample= avg_sample,
                                             samplecount = samplecount)

    type_I_temp_ch1 = pd.DataFrame.from_dict({x: result_1[0][0][x] for x in headers})
    type_I_temp_ch1['vac'] = vac
    type_I_temp_ch2 = pd.DataFrame.from_dict({x: result_2[0][0][x] for x in headers})
    type_I_temp_ch2['vac'] = vac
               
    # save the type I data
    type_I_temp_ch1.to_csv(handle + '_ch1_' + str(vac) + '.txt', sep = '\t',
                       index = False)
    type_I_temp_ch2.to_csv(handle + '_ch2_' + str(vac) + '.txt', sep = '\t',
                       index = False)
    # do the fit if chosen
    if inplace_fit:
        # fit the data to a Lorentz curve, ch1
        p_fit, p_err = zi_processing.fit_lorentz_sweeper(type_I_temp_ch1, showHTML = False, 
                                          figure_name = handle + '_ch1_' + str(vac), 
                                          zoom_in_fit = False)
        A, f0, Q, bkg = [x for x in p_fit]
        A_err, f0_err, Q_err, bkg_err = [x for x in p_err]
        fitted_results_ch1.append([vac, f0, f0_err, Q, Q_err])
        
        # fit the data to a Lorentz curve, ch2
        p_fit, p_err = zi_processing.fit_lorentz_sweeper(type_I_temp_ch2, showHTML = False, 
                                          figure_name = handle + '_ch2_' + str(vac), 
                                          zoom_in_fit = False)
        A, f0, Q, bkg = [x for x in p_fit]
        A_err, f0_err, Q_err, bkg_err = [x for x in p_err]
        fitted_results_ch2.append([vac, f0, f0_err, Q, Q_err])
        
    if type_II_ch1.size == 0:  # first time
        type_II_ch1 = type_I_temp_ch1
        type_II_ch2 = type_I_temp_ch2
    else:
        type_II_ch1 = type_II_ch1.append(type_I_temp_ch1, ignore_index = True)
        type_II_ch2 = type_II_ch2.append(type_I_temp_ch2, ignore_index = True)
        
    # save the type_II_ch1 data
    type_II_ch1.to_csv(handle + '_ch1_vacmega.txt', sep = '\t', 
                   index = False, headers = False)
    # save the type_II_ch2 data
    type_II_ch2.to_csv(handle + '_ch2_vacmega.txt', sep = '\t', 
                   index = False, headers = False)

# save the fitted result
if inplace_fit:
    fitted_resulst_ch1 = pd.DataFrame(fitted_results_ch1, columns = ['vac(V)', 'f0(Hz)', 'f0_err(Hz)',
                                   'Q', 'Q_err'])
    fitted_results_ch1.to_csv(handle + '_ch1_fitted_results.txt', sep = '\t', 
                   index = False)
        
          
# save the parameter!
with open('sweep_parameters.txt','w') as f:
    for key in parameters:
        f.write('{:20} : {}\n'.format(key, parameters[key]))
    

# return to the parent folder
os.chdir('..')
