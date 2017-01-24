#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This file is to processing the ringdown data
taken by zi

@author: changyaochen
"""

import os
import pandas as pd
import bokeh.plotting as bkp
import bokeh.models as bkm
import numpy as np
import scipy as sp
import zi_processing

dname = os.path.dirname(os.path.abspath(__file__))
os.chdir(dname)

# get the information of how many VDCs are there
all_VDC_folders = os.listdir()
VDCs = []
for folder in all_VDC_folders:
  if folder[-1] == 'V' and 'ringdown' not in folder:
#    print(folder)
    VDCs.append(folder[:-1])
  
# process each VDC
for VDC in VDCs:
  os.chdir(dname)  # make sure I'm at the master folder
  os.chdir(VDC + 'V')
  folders_in_VDC = os.listdir()
  
  # there are multiple open loop data
  for folder in folders_in_VDC:  # make sure it's not '.DS..'
    folder_cache = os.path.curdir
    if folder[0] == '.':
      continue  # skip the '.DS_Store' folder
    print(folder)
    zi_processing.open_loop_zi(folder, fit_lorentz = True, showHTML = False)
    os.chdir('..')  # return to last folder
    
    

  