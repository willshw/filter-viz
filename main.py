#!/usr/bin/env python

import sys
import time
import pyautogui

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
# pg.setConfigOption('background', 'w')

import kalman_filtered_mouse as kfm

REFRESH_RATE = 30.0
FITLER_TYPE = 'kalman_filter'

class Filter:

    def __init__(self, filter_type):
        self.mouse_pos = [0, 0]

        if filter_type == 'kalman_filter':
            self._filter = kfm.KalmanFilteredMouse()

        else:
            print 'Filter type not found!'
            exit()

    def runFilter(self):
        
        self._filter.predict()
        self._filter.updateMeasurements(self.mouse_pos[0], self.mouse_pos[1])
        self._filter.update()

    def setMousePos(self, pos):
        self.mouse_pos = pos

    def getMeasuredStates(self):

        return self._filter.getMeasuredStates()

    def getPredictiedStates(self):

        return self._filter.getPredictiedStates()

class Plot:
    
    def __init__(self):
        self._window = pg.GraphicsWindow(title='Filter')
        self._p = self._window.addPlot()
        self._p.enableAutoRange("xy", False)
        self._p.hideButtons()
        self._p.setXRange(0, 1920)
        self._p.setYRange(0, 1080)
        self._p.getViewBox().invertY(True)

        self._plot_measure = self._p.plot([], [], pen=None, symbol='o', symbolBrush=(255, 50, 50, 100))
        self._plot_predict = self._p.plot([], [], pen=None, symbol='o', symbolBrush=(50, 50, 255, 100))

        self.mouse_pos = [0, 0]

    def close_window(self):
        self._window.close()

    def getPlot(self):
        return self._p

    def mousePosUpdate(self, event):
        pos = event[0]  ## using signal proxy turns original arguments into a tuple
        if self._p.sceneBoundingRect().contains(pos):
            mousePoint = self._p.vb.mapSceneToView(pos)
            self.mouse_pos = [mousePoint.x(), mousePoint.y()]
    
    def getMousePos(self):
        return self.mouse_pos

    def setMeasureData(self, x, y):
        self._plot_measure.setData(x, y)
    
    def setPredictData(self, x, y):
        self._plot_predict.setData(x, y)

def main():

    print 'Press Ctrl+C to quit.'
    
    kf = Filter(FITLER_TYPE)
    plt = Plot()
    proxy = pg.SignalProxy(plt.getPlot().scene().sigMouseMoved, delay=0, rateLimit=REFRESH_RATE, slot=plt.mousePosUpdate)

    try:
        while True:

            kf.setMousePos(plt.getMousePos())
            kf.runFilter()

            Y = kf.getMeasuredStates()
            X = kf.getPredictiedStates()

            plt.setMeasureData([int(Y[0,0])], [int(Y[1,0])])
            plt.setPredictData([X[0,0]], [X[1,0]])
            QtGui.QApplication.processEvents()

            positionStr = 'X: {0:d} Y: {1:d} Xp: {2:.2f} Yp: {3:.2f}'.format(int(Y[0,0]), int(Y[1,0]), X[0,0], X[1,0])
            print positionStr,
            print '\b' * (len(positionStr) + 2),
            sys.stdout.flush()
            
            time.sleep(1.0/REFRESH_RATE)

    except KeyboardInterrupt:
        plt.close_window()
        print '\n'

if __name__ == "__main__":
        main()