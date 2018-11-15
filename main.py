#!/usr/bin/env python

import sys
import time
import pyautogui
from Queue import Queue
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
pg.setConfigOption('background', 'w')

import kalman_filtered_mouse as kfm

REFRESH_RATE = 30.0
FITLER_TYPE = 'kalman_filter'

class Filter:

    def __init__(self, filter_type):
        self.mouse_pos = [0, 0]

        self.meas_Xx = Queue()
        self.meas_Xy = Queue()
        self.pred_Xx = Queue()
        self.pred_Xy = Queue()

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

        Y = self._filter.getMeasuredStates()

        self.meas_Xx.put(Y[0,0])
        self.meas_Xy.put(Y[1,0])
    
        if self.meas_Xx.qsize() > 10:
            self.meas_Xx.get([0])
            self.meas_Xy.get([0])

        return list(self.meas_Xx.queue), list(self.meas_Xy.queue)

    def getPredictiedStates(self):
        
        X = self._filter.getPredictiedStates()

        self.pred_Xx.put(X[0,0])
        self.pred_Xy.put(X[1,0])

        if self.pred_Xx.qsize() > 10:
            self.pred_Xx.get([0])
            self.pred_Xy.get([0])

        return list(self.pred_Xx.queue), list(self.pred_Xy.queue)

class Plot:
    
    def __init__(self):
        self._window = pg.GraphicsWindow(title='Filter')
        self._p = self._window.addPlot()
        self._p.enableAutoRange("xy", False)
        self._p.hideButtons()
        self._p.setXRange(0, 2000, 0)
        self._p.setYRange(0, 2000, 0)
        # self._p.getViewBox().invertY(True)
        
        self._plot_measure = []
        self._plot_predict = []
        for i in range(0,10,1):
            measure_symbol_brush = pg.mkBrush((255, 25, 25, i*10))
            predict_symbol_brush = pg.mkBrush((25, 25, 255, i*10))
            self._plot_measure.append(self._p.plot([], [], pen=None, symbol='o', symbolBrush=measure_symbol_brush))
            self._plot_predict.append(self._p.plot([], [], pen=None, symbol='o', symbolBrush=predict_symbol_brush))

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
        for i in range(len(x)):
            self._plot_measure[i].setData([x[i]], [y[i]])
    
    def setPredictData(self, x, y):
        for i in range(len(x)):
            self._plot_predict[i].setData([x[i]], [y[i]])

def main():

    print 'Press Ctrl+C to quit.'
    
    kf = Filter(FITLER_TYPE)
    plt = Plot()
    proxy = pg.SignalProxy(plt.getPlot().scene().sigMouseMoved, delay=0, rateLimit=REFRESH_RATE, slot=plt.mousePosUpdate)

    try:
        while True:

            kf.setMousePos(plt.getMousePos())
            kf.runFilter()

            Yx, Yy = kf.getMeasuredStates()
            Xx, Xy = kf.getPredictiedStates()

            plt.setMeasureData(Yx, Yy)
            plt.setPredictData(Xx, Xy)

            QtGui.QApplication.processEvents()

            positionStr = 'X: {0:.2f} Y: {1:.2f} Xp: {2:.2f} Yp: {3:.2f}'.format(Yx[-1], Yy[-1], Xx[-1], Xy[-1])
            print positionStr,
            print '\b' * (len(positionStr) + 2),
            sys.stdout.flush()
            
            time.sleep(1.0/REFRESH_RATE)

    except KeyboardInterrupt:
        plt.close_window()
        print '\n'

if __name__ == "__main__":
        main()