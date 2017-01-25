# -*- coding: utf-8 -*-
"""
This is for multiple open loop sweep with different vac
The purpose is to see how the vac will affect the 
lineshape of the resonance, as well as the 
extracted Q

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
vac_list = np.linspace(0.01, 0.21, 21)
samplecount = 2000
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
fitted_result =[]
# TODO: collect errors in the fitted results

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
        

for vac in vac_list:
    # run one open loop sweep
    # the return result is a list, and its [0][0] element is the dict
    # that is of interest
    result = open_loop_sweep(device_id = 'dev267', 
                             start_freq = 60.61e3, stop_freq = 60.66e3,
                             amplitude=vac,
                             samplecount = samplecount)

    type_I_temp = pd.DataFrame.from_dict({x: result[0][0][x] for x in headers})
    type_I_temp['vac'] = vac
               
    # save the type I data
    type_I_temp.to_csv(handle + '_' + str(vac) + '.txt', sep = '\t',
                       index = False)
    # do the fit if chosen
    if inplace_fit:
        # fit the data to a Lorentz curve
        A, f0, Q, bkg = zi_processing.fit_lorentz_sweeper(type_I_temp, showHTML = False, 
                                          figure_name = handle + '_' + str(vac))
        fitted_result.append([vac, f0, Q])
        
    if type_II.size == 0:  # first time
        type_II = type_I_temp
    else:
        type_II = type_II.append(type_I_temp, ignore_index = True)
        
# save the type_II data
type_II.to_csv(handle + '_vacmega.txt', sep = '\t', 
               index = False, headers = False)
# save the fitted result
fitted_result = pd.DataFrame(fitted_result, columns = ['vac(Vpp)', 'f0(Hz)', 'Q'])
fitted_result.to_csv(handle + '_fitted_results.txt', sep = '\t', 
               index = False)
        

# return to the parent folder
os.chdir('..')
