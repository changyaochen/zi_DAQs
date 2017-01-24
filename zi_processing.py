#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 23 13:19:12 2017

@author: changyaochen
"""
import os
import numpy as np
import scipy as sp
import pandas as pd
import bokeh.plotting as bkp

def open_loop_zi(folder, fit_lorentz = False, showHTML = False):
  """
  This is to process the data obtained from sweeper 
  The default zi lock in is HF2LI
  There is only one input argument, which is the folder name
  In the folder, there should be all the required files
  saved by the zi software
  """
  
  os.chdir(folder)
  
  # get the header information from readme.txt, last line
  with open('readme.txt', 'r') as infile:
    file_header = infile.readlines()[-1].split(',')
    
  # name of the data file is Data.csv
  raw_data = pd.read_csv('Data.csv', names = file_header)
  
  # start plotting!
  p1 = bkp.figure(plot_width=800, plot_height=300, title = folder, 
                   tools='pan,box_zoom,reset,resize,save')
  p1_source = bkp.ColumnDataSource(raw_data)
  p1.circle(x = 'F(Hz)', y = 'R(Vrms)', source = p1_source, size = 10, 
            alpha = 0.5, legend = 'Data')

  p1.xaxis[0].axis_label = 'Frequency (Hz)'
  p1.yaxis[0].axis_label = 'Voltage (V)'
  
  if fit_lorentz:
    # fitting!
    def lorentz(p, x):
      A, f0, Q, bkg = p
      return A / np.sqrt((x**2 - f0**2)**2 + (x * f0 / Q)**2) + bkg
      # p[0] is Amplitude
      # p[1] is resonant frequency
      # p[2] is Q
      # p[3] is background
    
    def errorfunc(p, x, z):
          return lorentz(p,x) - z
        
    Q_guess = 200000
    Amp = raw_data['R(Vrms)']
    f0_guess = raw_data['F(Hz)'].ix[np.argmax(Amp)]
    bkg_guess = 0.00001
    p_guess = [max(Amp) * Q_guess, f0_guess, Q_guess, bkg_guess]
    solp, pcov, infodict, errmsg, success\
    = sp.optimize.leastsq(errorfunc, 
                    p_guess, 
                    args=(raw_data['F(Hz)'], Amp),
                    Dfun=None,
                    full_output=True,
                    ftol=1e-9,
                    xtol=1e-9,
                    maxfev=100000,
                    epsfcn=1e-10,
                    factor=0.1)
    p1.line(raw_data['F(Hz)'], lorentz(solp, raw_data['F(Hz)']), color = 'red', 
                   line_dash = 'dashed', line_width = 3, 
                   legend = 'Fitted, Q = ' + str(round(solp[2],3)))
    
    print('Q = ', round(solp[2],3))
    print('Ringdown time constant = ' + str(round(solp[2]/np.pi/solp[1], 3)) + 's')
  
  bkp.output_file(folder + '.html')
  if showHTML:
    bkp.show(p1)
  else:
    bkp.save(p1)
    
    
  # TODO: get the error bound
  
  
  
  