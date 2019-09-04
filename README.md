# Keithley-2701

This code is written to gather data from a Keithley 2701 Multimeter with a 20 Channel Differential Multiplexer.

Run "Logger" to log the data. You can change the desired channels you would like to sample and the logging frequency and the rest time between each loop.

You will have to change the file directories of course. The code was written on JUPYTER NOTEBOOK and it is meant to acquire the multimeter's data via an RS232 port located at the back of the device, ie Serial communication.

if you would like to plot the data, use the "Plotter" file.

There is an embedded alarm system using yagmail to warn you if there is any out-of-bounds values being recorded.

Contact me for more info.
