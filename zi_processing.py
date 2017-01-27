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

def lorentz(p, x):
      A, f0, Q, bkg = p
      return A / np.sqrt((x**2 - f0**2)**2 + (x * f0 / Q)**2) + bkg
      # p[0] is Amplitude
      # p[1] is resonant frequency
      # p[2] is Q
      # p[3] is background
    
def errorfunc(p, x, z):
      return lorentz(p,x) - z

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
    
  
def fit_lorentz_sweeper(df_in, showHTML = False, 
                        figure_name = 'temp', native_zi = False):
    """
    This is to fit the data obtained by sweeper
    The input is a dataframe, which needs to have
    'frequency', 'x', 'y' columns
    
    return fitted parameter, <list> solp
    [A, f0, Q, bkg]
    
    if native_zi == True, which meaning the data is taken
    directly from zi's web-based sweeper tag
    then the columns will be
    'F(Hz)', and 'R(Vrms)'
   
    """
    # make a copy!
    df = df_in.copy()
    
    assert isinstance(df, pd.DataFrame), 'Input type must be pd.DataFrame!'
    if native_zi:
      columns = ['F(Hz)', 'R(Vrms)']
      for elem in columns:
        assert elem in df.columns, 'No %s column!' % elem
      freq_header, r_header = 'F(Hz)', 'R(Vrms)'
    else:
      columns = ['x', 'y', 'frequency']
      for elem in columns:
        assert elem in df.columns, 'No %s column!' % elem
      Amp = np.sqrt(df['x']**2 + df['y']**2)
      df['r'] = Amp
      freq_header, r_header = 'frequency', 'r'
    
        
    
    Q_guess = 200000    
    Amp = df[r_header]
    f0_guess = df[freq_header].ix[np.argmax(Amp)]
    # let's just focus on the section arounding this area
    f_bound = 15*f0_guess / Q_guess
    mask = (df[freq_header] < f0_guess + f_bound) \
           & ((df[freq_header] > f0_guess - f_bound))
#    print(sum(mask))
    df2 = df[mask]
    bkg_guess = 0.00001
    p_guess = [max(Amp) * Q_guess, f0_guess, Q_guess, bkg_guess]
    p_fit, pcov, infodict, errmsg, success\
    = sp.optimize.leastsq(errorfunc, # errorfunc (p, x, y_data)
                    p_guess, 
                    args=(df2[freq_header], df2[r_header]),
                    Dfun=None,
                    full_output=True,
                    ftol=1e-9,
                    xtol=1e-9,
                    maxfev=100000,
                    epsfcn=1e-10,
                    factor=0.1)
    
    # ========== get the error bound ==========
    # following the info from this link:
    # http://stackoverflow.com/questions/14581358/getting-standard-errors-on-fitted-parameters-using-the-optimize-leastsq-method-i
    # I will also assume the  # of data points is larger than the # of fitting
    # parameters
    
    # first calculate the residual variance s_sq
    if pcov is not None:
      s_sq = (errorfunc(p_fit, df2[freq_header], df2[r_header])**2).sum()\
                      /(len(df2[r_header]) - len(p_fit))
#      print('residual variance is: ', s_sq)

      # update the pcov
      pcov = pcov * s_sq
    else:
      pcov = np.inf
    
    # calculate the sqrt of the diagonal component of pcov
    p_err = []
    for i in range(len(p_fit)):
      try:
        p_err.append(np.sqrt(np.absolute(pcov[i][i])))
      except:
        p_err.append(0.0)
    
    # convert to ndarray, for consistency    
    p_err = np.array(p_err)
    
    #========== end ==========
    
    bkp.output_file(figure_name + '.html')
    # start plotting!
    p1 = bkp.figure(plot_width=800, plot_height=300, title = figure_name, 
                   tools='pan,box_zoom,reset,resize,save')
    p1_source = bkp.ColumnDataSource(df)
    p1.circle(x = freq_header, y = r_header, source = p1_source, size = 10, 
            alpha = 0.5, legend = 'Data')
    p1.line(df2[freq_header], lorentz(p_fit, df2[freq_header]), color = 'red', 
                   line_dash = 'dashed', line_width = 3, 
                   legend = 'Fitted, Q = ' + str(round(p_fit[2],3)))

    p1.xaxis[0].axis_label = 'Frequency (Hz)'
    p1.yaxis[0].axis_label = 'Voltage (V)'
    if showHTML:
        bkp.show(p1)
    else:
        bkp.save(p1)
    
    return p_fit, p_err
    
  
  