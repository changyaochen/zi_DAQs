# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
This is my first try to do a open loop sweep
"""

def open_loop_sweep(device_id= 'dev267', demod_channel = 1, 
                    out_channel = 1, sigin_channel = 1, amplitude = 0.05, 
                    start_freq = 10e3, stop_freq = 11e3,
                    out_range = 0.1, avg_sample = 10, avg_tc = 15,
                    samplecount = 1000,
                    do_plot = False):
    import matplotlib.pyplot as plt
    import zhinst.utils
    import numpy as np
    import time
    
    ## ===== for debugging purpose ======
    #device_id= 'dev267'; demod_channel = 1; 
    #out_channel = 1; amplitude = 0.1; 
    #start_freq = 60.62e3; stop_freq = 60.64e3;
    #out_range = 0.1;
    #avg_sample = 10; avg_tc = 10;
    #samplecount = 1000;
    #do_plot = True
    ## ==================================
    
    api_level = 1
    (daq, device, props) = zhinst.utils.create_api_session(device_id, api_level);  
    # the last arg with value of 1 indicates API level
    # for HF2LI, the only valid API level is 1
    # the daq is a zhinst.ziPython.ziDAQServer class object
    
    
    out_mixer_channel = zhinst.utils.default_output_mixer_channel(props)
    rate=2000  # streaming sampling rate
    tc=0.005  # equil. to LPF BW
    c=str(demod_channel-1)
    o_c = str(out_channel-1)
    i_c = str(sigin_channel-1)
    general_setting = [
        [['/', device, '/demods/0/trigger'], 0],
        [['/', device, '/demods/1/trigger'], 0],
        [['/', device, '/demods/2/trigger'], 0],
        [['/', device, '/demods/3/trigger'], 0],
        [['/', device, '/demods/4/trigger'], 0],
        [['/', device, '/demods/5/trigger'], 0],  # continuous triggering
        [['/', device, '/sigouts/', o_c,'/enables/*'], 1]
            ]
    daq.set(general_setting)
    
    # I need to get the output Vpk range, to find out what it is among the values
    # of [0.01, 0.1, 1, 10]
    
    # Set test settings
    exp_sigOutIn_setting = [
            # input (demods) settings
       [['/', device, '/sigins/',i_c,'/diff'], 1],  # diff input on
       [['/', device, '/sigins/',i_c,'/imp50'], 1],  # 50 Ohm input impedance
       [['/', device, '/sigins/',i_c,'/ac'], 1],  # input ac coupling
       [['/', device, '/plls/', i_c,'/enable'], 0],  # set osc ref to internal
    #       [['/', device, '/sigins/',c,'/range'], 1],  # I will set the range manually
       [['/', device, '/demods/',c,'/order'], 8],
       [['/', device, '/demods/',c,'/timeconstant'], tc],  # equil. to LPF BW
       [['/', device, '/demods/',c,'/rate'], rate],  # streaming rate
       [['/', device, '/demods/',c,'/adcselect'], demod_channel-1],  # adc select
       [['/', device, '/demods/',c,'/oscselect'], demod_channel-1],  # osc select
       [['/', device, '/demods/',c,'/harmonic'], 1],  # demods order
       # output settings
       [['/', device, '/sigouts/',o_c,'/add'], 0],  # output, no add
       [['/', device, '/sigouts/',o_c,'/on'], 0],  # turn output off first
    #           [['/', device, '/sigouts/',c,'/enables/',c], 1],  
       [['/', device, '/sigouts/',o_c,'/range'], 2*amplitude]  # I will set the range manually
                              ]
    # pass the setting in
    daq.set(exp_sigOutIn_setting)
    
    # need to correct for the amplitude
    output_range = list(daq.get('/'+device+'/sigouts/'+o_c+'/range', True).values())[0][0]  
    exp_sigOutIn_setting.extend([
            # set output amplitude
            [['/', device, '/sigouts/',o_c,'/amplitudes/',str(out_channel - 1 + 6)], 
              amplitude/output_range],  
            [['/', device, '/sigouts/',o_c,'/on'], 1]  # turn output on
                                ])                    
    daq.set(exp_sigOutIn_setting)
    # wait 1s to get a settled lowpass filter
    time.sleep(1)
    #clean queue
    daq.flush()
    
                                 
    timeout_milliseconds = 500
    sweeper = daq.sweep(timeout_milliseconds)
    sweeper.set('sweep/device', device)
    
    daq.sync()
    # Start the Sweeper's thread.
    #demod_index = 3
    #osc_index = 1
    #demod_rate = 1e3
    #time_constant = 0.01
    start_time = time.time()
    timeout = 1e6  # [s]
    # set start frequency
    sweeper.set('sweep/gridnode', 'oscs/'+o_c+'/freq')
    sweeper.set('sweep/start', float(start_freq))
    sweeper.set('sweep/stop', float(stop_freq))
    
    path = '/%s/demods/%s/sample' % (device, c)
    # Specify the number of sweeps to perform back-to-back.
    loopcount = 1
    sweeper.set('sweep/loopcount', loopcount)
    
    # Set the number of points to use for the sweep, the number of gridnode
    # setting values will use in the interval (`start`, `stop`).
    sweeper.set('sweep/samplecount', samplecount)
    
    # Specify logarithmic spacing for the values in the sweep interval.
    sweeper.set('sweep/xmapping', 1)
    
    # Automatically control the demodulator bandwidth/time constants used.
    # 0=manual, 1=fixed, 2=auto
    # Note: to use manual and fixed, sweep/bandwidth has to be set to a value > 0.
    sweeper.set('sweep/bandwidthcontrol', 0)
    
    # Sets the bandwidth overlap mode (default 0). If enabled, the bandwidth of
    # a sweep point may overlap with the frequency of neighboring sweep
    # points. The effective bandwidth is only limited by the maximal bandwidth
    # setting and omega suppression. As a result, the bandwidth is independent
    # of the number of sweep points. For frequency response analysis bandwidth
    # overlap should be enabled to achieve maximal sweep speed (default: 0). 0 =
    # Disable, 1 = Enable.
    sweeper.set('sweep/bandwidthoverlap', 0)
    
    # We don't require a fixed sweep/settling/time since there is no DUT
    # involved in this example's setup (only a simple feedback cable), so we set
    # this to zero. We need only wait for the filter response to settle,
    # specified via sweep/settling/inaccuracy.
    sweeper.set('sweep/settling/time', 0)
    
    # The sweep/settling/inaccuracy' parameter defines the settling time the
    # sweeper should wait before changing a sweep parameter and recording the next
    # sweep data point. The settling time is calculated from the specified
    # proportion of a step response function that should remain. The value
    # provided here, 0.001, is appropriate for fast and reasonably accurate
    # amplitude measurements. For precise noise measurements it should be set to
    # ~100n.
    # Note: The actual time the sweeper waits before recording data is the maximum
    # time specified by sweep/settling/time and defined by
    # sweep/settling/inaccuracy.
    sweeper.set('sweep/settling/inaccuracy', 0.001)
    
    # Set the minimum time to record and average data to 10 demodulator
    # filter time constants.
    sweeper.set('sweep/averaging/tc', avg_tc)
    
    # Minimal number of samples that we want to record and average is 100. Note,
    # the number of samples used for averaging will be the maximum number of
    # samples specified by either sweep/averaging/tc or sweep/averaging/sample.
    sweeper.set('sweep/averaging/sample', avg_sample)
    
    sweeper.subscribe(path)
    print("Will perform", loopcount, "sweeps...")
    sweeper.execute()
    while not sweeper.finished():  # Wait until the sweep is complete, with timeout.
        time.sleep(0.2)
        progress = sweeper.progress()
        if 100*progress[0]%5.0 == 0.0:
            print("Individual sweep progress: {:.2%}.".format(progress[0]))
        # Here we could read intermediate data via:
        # data = sweeper.read(True)...
        # and process it while the sweep is completing.
        # if device in data:
        # ...
        if (time.time() - start_time) > timeout:
            # If for some reason the sweep is blocking, force the end of the
            # measurement.
            print("\nSweep still not finished, forcing finish...")
            sweeper.finish()
    print("")
    
    # Read the sweep data. This command can also be executed whilst sweeping
    # (before finished() is True), in this case sweep data up to that time point
    # is returned. It's still necessary still need to issue read() at the end to
    # fetch the rest.
    return_flat_dict = True
    data1 = sweeper.read(return_flat_dict)
    sweeper.unsubscribe(path)
    
    # Stop the sweeper thread and clear the memory.
    sweeper.clear()
    
    # Check the dictionary returned is non-empty.
    assert data1, "read() returned an empty data dictionary, did you subscribe to any paths?"
    # Note: data could be empty if no data arrived, e.g., if the demods were
    # disabled or had rate 0.
    assert path in data1, "No sweep data in data dictionary: it has no key '%s'" % path
    samples = data1[path]
    print("Returned sweeper data contains", len(samples), "sweeps.")
    assert len(samples) == loopcount, \
        "The sweeper returned an unexpected number of sweeps: `%d`. Expected: `%d`." % (len(samples), loopcount)
        
    if do_plot:
        plt.clf()
        for i in range(0, len(samples)):
            frequency = samples[i][0]['frequency']
            R = np.abs(samples[i][0]['x'] + 1j*samples[i][0]['y'])
            phi = np.angle(samples[i][0]['x'] + 1j*samples[i][0]['y'])
            plt.subplot(2, 1, 1)
            plt.plot(frequency, R)
            plt.subplot(2, 1, 2)
            plt.plot(frequency, phi)
        plt.subplot(2, 1, 1)
        plt.title('Results of %d sweeps.' % len(samples))
        plt.grid(True)
        plt.ylabel(r'Demodulator R ($V_\mathrm{RMS}$)')
        plt.subplot(2, 1, 2)
        plt.grid(True)
        plt.xlabel('Frequency ($Hz$)')
        plt.ylabel(r'Demodulator Phi (radians)')
        plt.autoscale()
        plt.draw()
        plt.show()
        
    return samples
    

if __name__ == '__main__':
   open_loop_sweep(device_id= 'dev267', demod_channel = 4, 
                   out_channel = 2, sigin_channel = 2, amplitude = 0.03, 
                    start_freq = 31.8e3, stop_freq = 31.9e3,
                    out_range = 0.1, avg_sample = 5, avg_tc = 15,
                    samplecount = 1000,
                    do_plot =True)
    

