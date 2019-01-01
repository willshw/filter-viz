#!/usr/bin/env python

import sys
import time
from datetime import datetime

from Queue import Queue
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
pg.setConfigOption('background', 'w')

import kalman_filtered_mouse as kfm

REFRESH_RATE = 30.0
FITLER_TYPE = 'kalman_filter'

class Filter:

    def __init__(self, filter_type):
        self._mouse_pos = [0, 0]

        self._meas_hist_len = 3
        self._pred_hist_len = 7

        self._meas_Xx = Queue()
        self._meas_Xy = Queue()
        self._pred_Xx = Queue()
        self._pred_Xy = Queue()

        if filter_type == 'kalman_filter':
            self._filter = kfm.KalmanFilteredMouse()

        else:
            print 'Filter type not found!'
            exit()

    def runFilter(self):
        
        self._filter.predict()
        self._filter.updateMeasurements(self._mouse_pos[0], self._mouse_pos[1], time.time())
        self._filter.update()

    def setMousePos(self, pos):
        self._mouse_pos = pos

    def setMeasHistLen(self, leng):
        leng = max(1, min(leng, 10))
        self._meas_hist_len = leng

    def setPredHistLen(self, leng):
        leng = max(1, min(leng, 10))
        self._pred_hist_len = leng

    def getMeasuredStates(self):

        Y = self._filter.getMeasuredStates()

        self._meas_Xx.put(Y[0,0])
        self._meas_Xy.put(Y[1,0])
    
        if self._meas_Xx.qsize() > self._meas_hist_len:
            self._meas_Xx.get([0])
            self._meas_Xy.get([0])

        return list(self._meas_Xx.queue), list(self._meas_Xy.queue)

    def getPredictiedStates(self):
        
        X = self._filter.getPredictiedStates()

        self._pred_Xx.put(X[0,0])
        self._pred_Xy.put(X[1,0])

        if self._pred_Xx.qsize() > self._pred_hist_len:
            self._pred_Xx.get([0])
            self._pred_Xy.get([0])

        return list(self._pred_Xx.queue), list(self._pred_Xy.queue)

class Plot:
    
    def __init__(self):
        self._p = pg.PlotWidget()
        self._p.setAspectLocked()
        self._p.setLimits(xMin=0, xMax=2000, yMin=0, yMax=2000)
        self._p.setXRange(0, 2000, 0)
        self._p.setYRange(0, 2000, 0)
        self._p.hideButtons()
        
        self._plot_measure = []
        self._plot_predict = []
        self._mouse_pos = [0, 0]

        self._measX = [0]
        self._measY = [0]
        self._predX = [0]
        self._predY = [0]

        # update plot as fast as it can
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.updatePlot)
        self._timer.start(0)

    def getPlot(self):
        return self._p

    def getMousePos(self):
        return self._mouse_pos

    def mousePosUpdate(self, event):
        pos = event[0]  ## using signal proxy turns original arguments into a tuple
        if self._p.sceneBoundingRect().contains(pos):
            mousePoint = self._p.plotItem.vb.mapSceneToView(pos)
            self._mouse_pos = [mousePoint.x(), mousePoint.y()]

    def setMeasuredData(self, x, y):
        self._measX = x
        self._measY = y

    def setPredictedData(self, x, y):
        self._predX = x
        self._predY = y

    def plotMeasuredData(self, x, y):
        if(len(x) == len(self._plot_measure)):
            for i in range(len(x)):
                self._plot_measure[i].setData([x[i]], [y[i]])

        else:
            for p in self._plot_measure:
                p.clear()

            self._plot_measure = []
            for i in range(len(x)):
                measure_symbol_brush = pg.mkBrush((255, 25, 25, int((i+1)*255/len(x)) ))
                self._plot_measure.append(self._p.plot([x[i]], [y[i]], pen=None, symbol='o', symbolBrush=measure_symbol_brush))

    def plotPredictedData(self, x, y):
        if(len(x) == len(self._plot_predict)):
            for i in range(len(x)):
                self._plot_predict[i].setData([x[i]], [y[i]])

        else:
            for p in self._plot_predict:
                p.clear()

            self._plot_predict = []
            for i in range(len(x)):
                predict_symbol_brush = pg.mkBrush((25, 25, 255, int((i+1)*255/len(x)) ))
                self._plot_predict.append(self._p.plot([x[i]], [y[i]], pen=None, symbol='o', symbolBrush=predict_symbol_brush))

    def updatePlot(self):
        self.plotMeasuredData(self._measX, self._measY)
        self.plotPredictedData(self._predX, self._predY)

        positionStr = 'X: {0:6.2f} Y: {1:6.2f} Xp: {2:6.2f} Yp: {3:6.2f}'.format(self._measX[-1], self._measY[-1], self._predX[-1], self._predY[-1])
        print positionStr,
        print '\b' * (len(positionStr) + 2),
        sys.stdout.flush()

class FilterUpdater(QtCore.QObject):
    def __init__(self, plot, fltr):
        super(FilterUpdater, self).__init__()
        self._fltr = fltr
        self._plot = plot
        self._isRunning = True
    
    @QtCore.pyqtSlot()
    def update(self):
        while self._isRunning:

            self._fltr.setMousePos(self._plot.getMousePos())
            self._fltr.runFilter()

            measX, measY = self._fltr.getMeasuredStates()
            predX, predY = self._fltr.getPredictiedStates()

            self._plot.setMeasuredData(measX, measY)
            self._plot.setPredictedData(predX, predY)

            time.sleep(1.0/REFRESH_RATE)

    def stop(self):
        self._isRunning = False

class App(QtGui.QWidget):
    
    def __init__(self, plot, fltr):
        super(App, self).__init__()
        self._QUIT = False
        self._plt = plot
        self._title = 'Filtering Test'
        self._left = 0
        self._top = 0
        self._width = 1000
        self._height = 1000
        self._initUI()

        self._filter_updater = FilterUpdater(plot, fltr)
        self._thread = QtCore.QThread(self)
        self._filter_updater.moveToThread(self._thread)
        self._thread.started.connect(self._filter_updater.update)
        self._thread.start()

    def stopThread(self):
        self._filter_updater.stop()
        self._thread.quit()
        self._thread.wait()

    def _initUI(self):
        # configure window
        self.setWindowTitle(self._title)
        self.setGeometry(self._left, self._top, self._width, self._height)

        # configure widgets

        # Update Button
        self._PushButton_update = QtGui.QPushButton('Update', self)
        # self.PushButton_update.resize(80, 30)
        # self.PushButton_update.move(30, 0)
        self._PushButton_update.setToolTip('Update parameters')
        self._PushButton_update.clicked.connect(self._updateParam)

        # Quit Button
        self._PushButton_quit = QtGui.QPushButton('Quit', self)
        # self.PushButton_quit.resize(80, 30)
        # self.PushButton_quit.move(100, 0)
        self._PushButton_quit.setToolTip('Quit this application')
        self._PushButton_quit.clicked.connect(self._quitApp)

        # Layout
        self._GridLayout = QtGui.QGridLayout()
        self._GridLayout.setSpacing(10)
        self.setLayout(self._GridLayout)

        self._GridLayout.addWidget(self._plt.getPlot(), 0, 0)
        self._GridLayout.addWidget(self._PushButton_update, 0, 1)
        self._GridLayout.addWidget(self._PushButton_quit, 0, 2)

        # Show widget
        self.show()

    def _updateParam(self):
        print '{:50s}'.format(datetime.now().time().strftime('%m/%d/%y %I:%M:%S %p') + ' Updated Paramters')

    def _quitApp(self):
        print '{:50s}'.format('Exit application')
        self.stopThread()
        QtCore.QCoreApplication.instance().quit()

def main():

    print 'Press Ctrl+C to quit.\n'
    
    print 'Red is the real mouse pointer positions.'
    print 'Blue is the Kalman filter predicted mouse pointer positions.\n'

    app = QtGui.QApplication(sys.argv)
    fltr = Filter(FITLER_TYPE)
    plt = Plot()
    ex = App(plt, fltr)

    proxy = pg.SignalProxy(plt.getPlot().scene().sigMouseMoved, delay=0, rateLimit=REFRESH_RATE, slot=plt.mousePosUpdate)

    sys.exit(app.exec_())

if __name__ == "__main__":
        main()