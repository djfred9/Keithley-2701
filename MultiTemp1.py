#!/usr/bin/env python

from LogDisplay import TempDisplay
from os import system, path

logDirectory = 'C:/Users/E5/Desktop/Allan LABVIEW/E5 Logger/MultiTemp1'

probeNames = ('Channel 101',
                        '6 Way Cross',
                        'Down Viewport',
                        'Middle Nipple',
                        'NEG',
                        'Angle Valve',
                        'Bellows',
                        '4 Way Cross',
                        'Turbo',
                        'MOT Coils')

log = TempDisplay(logDirectory, 'Channel 1', columns=probeNames, title='Channel 1', resample=False)
if __name__ == "__main__":
    log.plot()
    log.loop()


def save_plot(stop=False, start=False, days=1):
    log.save_plot(stop, start, days)


def save_web_plot(dir, stop=False, start=False, days=1):
    filename = "%s.png" % log.name
    file = path.realpath(path.join(dir, filename))
    log.save_plot(stop, start, days, file=file, ylimbottom=None, ylimtop=None)
