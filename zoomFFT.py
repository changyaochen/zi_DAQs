# -*- coding: utf-8 -*-
"""
Spyder Editor
"""
def zoomfft(daq, device, demod_index = 1, timeout = float('inf'), 
            bits = 14,
            do_plot = False):
    """
    This is a temporary script file.
    This is my first try to use zoomFFT function
    """
    import matplotlib.pyplot as plt
    import zhinst.utils
    import zhinst.ziPython as zi
    import scipy as sp
    import numpy as np
    import os
    import time, math
    
#    device_id = 'dev267'
#    demod_index = 4
#    api_level = 1
#    (daq, device, props) = zhinst.utils.create_api_session(device_id, api_level)  
    # the last arg with value of 1 indicates API level
    # for HF2LI, the only valid API level is 1
    # the daq is a zhinst.ziPython.ziDAQServer class object
    
    # initialize an zoomFFT instance
    zoomfft = daq.zoomFFT()
    
    # take a look at the structure and values
#    print(zoomfft.get('zoomFFT/*'))
    
    # set the device value 
    zoomfft.set('zoomFFT/device', device)
    
    # Disable overlap mode.
    zoomfft.set('zoomFFT/overlap', 0)
    
    # Use a Hann windowing function in the FFT:
    # 0=Rectangular, 1=Hann, 2=Hamming, 3=Blackman Harris.
    zoomfft.set('zoomFFT/window', 1)
    
    # Return absolute frequencies instead of relative to 0.
    zoomfft.set('zoomFFT/absolute', 0)
    
    # The number of lines is 2^bits.
    zoomfft.set('zoomFFT/bit', bits)
    
    # minimum wait time in factors of the time constant TC before taking a measurement
    zoomfft.set('zoomFFT/settling/tc', 3)
    
    # The number of zoomFFT's to perform.
    loopcount = 1
    zoomfft.set('zoomFFT/loopcount', loopcount)
    
    # Now subscribe to the nodes from which data will be recorded. Note, this is
    # not the subscribe from ziDAQServer; it is a Module subscribe. The Spectrum
    # Analyzer Module needs to subscribe to the nodes it will return data for.
    path = '/%s/demods/%d/sample' % (device, demod_index-1)
    zoomfft.subscribe(path)
    
    # execute the zoomFFT!
    zoomfft.execute()
    
    start = time.time()
#    timeout = float('inf')  # [s]
    print("Will perform", loopcount, "zoomFFTs.")
    while not zoomfft.finished():
        time.sleep(0.2)
        # Please note: progress() and finish() works for first zoomFFT, but
        # It's a known issue that it doesn't update for subsequent zoomFFTs
        progress = zoomfft.progress()
        old_progress = 0.0 
        if progress[0]*100%5.0 == 0.0 and round(progress[0], 2) != old_progress:
            print("Individuasl zoomFFT progress: {:.2%}.".format(progress[0]), end="\n")
            old_progress = round(progress[0], 2)
    
        # We could read intermediate data calculated by the Module using read()
        # data = zoomfft.read()...
        # and process it:
        # if device in data:
        # ...
        if (time.time() - start) > timeout:
            # If for some reason the zoomFFT is blocking, force the end of the
            # measurement.
            print("\nzoomFFT still not finished, forcing finish...")
            zoomfft.finish()
    print("zoomFFT done!")
    
    # Read the zoomFFT data. this command can also be executed whilst the
    # zoomFFT is still being calculated (before finished() is True), in this
    # case zoomFFT data up to that time point is returned. it's still
    # necessary to issue read() at the end to fetch the rest.
    return_flat_data_dict = True
    data = zoomfft.read(return_flat_data_dict)
    zoomfft.unsubscribe(path)
    
    # Stop the module's thread and clear the memory.
    zoomfft.clear()
    
    # Check that the dictionary returned is non-empty.
    assert data, "read() returned an empty data dictionary, did you subscribe to any paths?"
    # Note: data could be empty if no data arrived, e.g., if the demods were
    # disabled or had rate 0.
    assert path in data, "data dictionary has no key '%s'" % path
    samples = data[path]
    print("Returned zoomFFT data contains", len(samples), "FFTs.")
    assert len(samples) == loopcount, \
        "The zoomFFT returned an unexpected number of FFTs: `%d`. Expected: `%d`." % (len(samples), loopcount)
    print("Number of lines in the first zoomFFT: {:d}.".format(len(samples[0][0]['grid'])))
    
    plot_idx = 0
    frequencies = samples[plot_idx][0]['grid']
    r = samples[plot_idx][0]['r']
    filter_data = samples[plot_idx][0]['filter']

    if do_plot:
        print("Will plot result of the zoomFFT result {:d}.".format(plot_idx))        
        
        plt.clf()
        plt.subplot(211)
        plt.hold(True)
        plt.title('Spectrum Analyser Module Result')
        # Plot in dBV (=dBVRMS), r is in VRMS and and signal output amplitude is Vpp.
        plt.plot(frequencies, 20*np.log10(r*np.sqrt(2)))
        plt.grid(True)
        plt.xlabel('Frequency (kHz)')
        plt.ylabel('FFT(R) (a.u.)')
        plt.autoscale(True, 'both', True)
        plt.subplot(212)
        plt.hold(True)
        plt.plot(frequencies, 20*np.log10((r/filter_data)*np.sqrt(2)))
        plt.grid(True)
        plt.xlabel('Frequency (kHz)')
        plt.ylabel('FFT(R) (a.u.)\n with Demod Filter Compensation')
        plt.autoscale(True, 'both', True)
        plt.draw()
        plt.show()
        
    return frequencies, r/filter_data

if __name__ == '__main__':
    device_id = 'dev267'
    (daq, device, props) = zhinst.utils.create_api_session(device_id, maximum_supported_apilevel = 4)
    zoomfft(daq, device, demod_index = 1, timeout = float('inf'), 
            bits = 16,
            do_plot = True)
    
    

