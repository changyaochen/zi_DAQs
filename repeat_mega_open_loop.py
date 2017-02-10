# -*- coding: utf-8 -*-
"""
This is for multiple open loop sweep with excat same settings
The purpose is to see the drift of the system with time

@author: changyao chen
"""

from open_loop_sweep import *
import os
import numpy as np
import pandas as pd
import zi_processing

# get the directories right
dname = os.path.dirname(os.path.abspath(__file__))
os.chdir(dname)
device_id= 'dev267'


# ===== global setting =======
take_list = np.linspace(1, 50, 50)
samplecount = 1000
vac = 0.03
#vac_list = [0.1]; samplecount = 100  # for debug purpose
inplace_fit = True  # whether to do Lorentz fit for each sweep
# ==============================

# I will save the output into 2 types of files:
# for the first type, each vac has its own file
# for the second type is the usual megasweep format (single file)
# 
# with vac attached to the file name

# initilization for the type_II data
type_II = pd.DataFrame()
# initialization for the fitted result
fitted_results =[]


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
        

for take in take_list:
    # run one open loop sweep
    # the return result is a list, and its [0][0] element is the dict
    # that is of interest
    result = open_loop_sweep(device_id = 'dev267', 
                             start_freq = 27.62e3, stop_freq = 27.70e3,
                             amplitude=vac, avg_sample=3, avg_tc=5,
                             samplecount = samplecount)

    type_I_temp = pd.DataFrame.from_dict({x: result[0][0][x] for x in headers})
    type_I_temp['take'] = take
               
    # save the type I data
    type_I_temp.to_csv(handle + '_take_' + str(take) + '.txt', sep = '\t',
                       index = False)
    # do the fit if chosen
    if inplace_fit:
        # fit the data to a Lorentz curve
        p_fit, p_err = zi_processing.fit_lorentz_sweeper(type_I_temp, showHTML = False, 
                                          figure_name = handle + '_take_' + str(take),
                                          zoom_in_fit=False)        
        A, f0, Q, bkg = [x for x in p_fit]
        A_err, f0_err, Q_err, bkg_err = [x for x in p_err]
        fitted_results.append([take, f0, f0_err, Q, Q_err])
        
    if type_II.size == 0:  # first time
        type_II = type_I_temp
    else:
        type_II = type_II.append(type_I_temp, ignore_index = True)
        
# save the type_II data
type_II.to_csv(handle + '_repeat_mega.txt', sep = '\t', 
               index = False, headers = False)
# save the fitted result
fitted_results = pd.DataFrame(fitted_results, columns = ['vac(V)', 'f0(Hz)', 'f0_err(Hz)',
                                   'Q', 'Q_err'])
fitted_results.to_csv(handle + '_fitted_results.txt', sep = '\t', 
               index = False)
        

# return to the parent folder
os.chdir('..')
