#!/usr/bin/env python

import sys
import time
import pyautogui

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

import kalman_filtered_mouse as kfm

REFRESH_RATE = 1.0/30.0
FITLER_TYPE = 'kalman_filter'

class Filter:
    def __init__(self, filter_type):

        if filter_type == 'kalman_filter':
            self._filter = kfm.KalmanFilteredMouse()

        else:
            print 'Filter type not found!'
            exit()

    def runFilter(self):
        
        self._filter.predict()
        x, y = pyautogui.position()
        self._filter.updateMeasurements(x, y)
        self._filter.update()

    def getMeasuredStates(self):

        return self._filter.getMeasuredStates()

    def getPredictiedStates(self):

        return self._filter.getPredictiedStates()


def main():

    print 'Press Ctrl+C to quit.'
    
    kf = Filter(FITLER_TYPE) 

    try:
        while True:
            kf.runFilter()

            Y = kf.getMeasuredStates()
            X = kf.getPredictiedStates()

            positionStr = 'X: {0:d} Y: {1:d} Xp: {2:.2f} Yp: {3:.2f}'.format(int(Y[0,0]), int(Y[1,0]), X[0,0], X[1,0])
            print positionStr,
            print '\b' * (len(positionStr) + 2),
            sys.stdout.flush()
            
            time.sleep(REFRESH_RATE)

    except KeyboardInterrupt:
        print '\n'

if __name__ == "__main__":
    main()