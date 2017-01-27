#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This is a test to get the fitting errors
from the Lorentz fit

@author: changyaochen
"""

import pandas as pd
import sys, os
sys.path.append('..')  # add the parent folder available for loading modules
import zi_processing

dname = os.path.dirname(os.path.abspath(__file__))
os.chdir(dname)

test_file = 'vacmega_B123_ARG_S13_3_cIII_vac-60dB_Vg_7V_FEMTO_1uAV_0.1.txt'
test_data_df = pd.read_csv(test_file, sep='\t')

# get the fitted result
p, p_err = zi_processing.fit_lorentz_sweeper(test_data_df, showHTML = False, 
                                          figure_name = 'temp')

# unpack the fitted result
A, f0, Q, bkg = [x for x in p]
A_err, f0_err, Q_err, bkg_err = [x for x in p_err]

