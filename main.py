#!/usr/bin/env python

import sys
import time
from datetime import datetime

from Queue import Queue
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
pg.setConfigOption('background', 'w')

import numpy as np

import filterLib as flib

REFRESH_RATE = 30.0
FITLER_TYPE = 'kalman_filter'

class Filter:

    def __init__(self, filter_type):
        self._mouse_pos = [0, 0]
        self._mouse_pos_noise_x_std = 50.0
        self._mouse_pos_noise_y_std = 50.0

        self._meas_hist_len = 3
        self._pred_hist_len = 7

        self._meas_Xx = Queue()
        self._meas_Xy = Queue()
        self._pred_Xx = Queue()
        self._pred_Xy = Queue()

        if filter_type == 'kalman_filter':
            self._filter = flib.KalmanFilter()

        else:
            print 'Filter type not found!'
            exit()

    def runFilter(self):
        
        self._filter.predict()
        self._filter.updateMeasurements(self._mouse_pos[0], self._mouse_pos[1], time.time())
        self._filter.update()

    def setMousePos(self, pos):
        self._mouse_pos = pos

    def setXNoiseStd(self, v):
        self._mouse_pos_noise_x_std = v
    
    def setYNoiseStd(self, v):
        self._mouse_pos_noise_y_std = v

    def setMousePos_Noise(self, pos):
        x_noise = np.random.normal(pos[0], self._mouse_pos_noise_x_std, 1)
        y_noise = np.random.normal(pos[1], self._mouse_pos_noise_y_std, 1)
        self._mouse_pos = [x_noise, y_noise]

    def setMeasHistLen(self, leng):
        leng = max(1, min(leng, 10))
        self._meas_hist_len = leng

    def setPredHistLen(self, leng):
        leng = max(1, min(leng, 10))
        self._pred_hist_len = leng

    def getMeasHistLen(self):
        return self._meas_hist_len

    def getPredHistLen(self):
        return self._pred_hist_len

    def getMeasuredStates(self):

        Y = self._filter.getMeasuredStates()

        self._meas_Xx.put(Y[0,0])
        self._meas_Xy.put(Y[1,0])
    
        while self._meas_Xx.qsize() > self._meas_hist_len:
            self._meas_Xx.get([0])
            self._meas_Xy.get([0])

        return list(self._meas_Xx.queue), list(self._meas_Xy.queue)

    def getPredictiedStates(self):
        
        X = self._filter.getPredictiedStates()

        self._pred_Xx.put(X[0,0])
        self._pred_Xy.put(X[1,0])

        while self._pred_Xx.qsize() > self._pred_hist_len:
            self._pred_Xx.get([0])
            self._pred_Xy.get([0])

        return list(self._pred_Xx.queue), list(self._pred_Xy.queue)

    def getFilterParams(self):
        return self._filter.getParams()

    def setFilterParams(self, n, val):
        self._filter.setParams(n, val)

class Plot:
    
    def __init__(self):
        self._p = pg.PlotWidget()

        self._t_Meas = pg.TextItem(text='Text', color='r', anchor=(0.0, 1.5))
        self._t_Pred = pg.TextItem(text='Text', color='b', anchor=(0.0, 1.0))
        font = QtGui.QFont('Monospace', 8)
        font.setStyleHint(QtGui.QFont.TypeWriter)
        self._t_Meas.setFont(font)
        self._t_Pred.setFont(font)
        self._p.addItem(self._t_Meas)
        self._p.addItem(self._t_Pred)

        self._p.setAspectLocked(True)
        self._p.setMinimumSize(300, 300)
        self._p.setMaximumSize(1000, 1000)
        
        self._p.setLimits(xMin=0, xMax=2000, yMin=0, yMax=2000)
        self._p.setXRange(0, 2000, padding=0.0, update=False)
        self._p.setYRange(0, 2000, padding=0.0, update=False)
        self._p.disableAutoRange()
        self._p.hideButtons()

        self._p.plotItem.setClipToView(True)
        self._p.plotItem.hideAxis('left')
        self._p.plotItem.hideAxis('bottom')
        self._p.plotItem.setAspectLocked()

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

    @property
    def MeasStatText(self):
        return self._t_Meas

    @property
    def PredStatText(self):
        return self._t_Pred

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

        self._t_Meas.setText('Measurement [X:{0:=8.2f}, Y:{1:=8.2f}]'.format(self._measX[-1], self._measY[-1]))
        self._t_Pred.setText('Prediction  [X:{0:=8.2f}, Y:{1:=8.2f}]'.format(self._predX[-1], self._predY[-1]))

        # positionStr = 'X: {0:6.2f} Y: {1:6.2f} Xp: {2:6.2f} Yp: {3:6.2f}'.format(self._measX[-1], self._measY[-1], self._predX[-1], self._predY[-1])
        # print positionStr,
        # print '\b' * (len(positionStr) + 2),
        # sys.stdout.flush()

class FilterUpdater(QtCore.QObject):
    def __init__(self, plot, fltr):
        super(FilterUpdater, self).__init__()
        self._fltr = fltr
        self._plot = plot
        self._isRunning = True
    
    @QtCore.pyqtSlot()
    def update(self):
        while self._isRunning:

            # self._fltr.setMousePos(self._plot.getMousePos())
            self._fltr.setMousePos_Noise(self._plot.getMousePos())
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
        self._filter = fltr
        self._title = 'Filter Test'
        self._left = 0
        self._top = 0
        self._width = 500
        self._height = 500
        self.initUI()

        self._filter_updater = FilterUpdater(plot, fltr)
        self._thread = QtCore.QThread(self)
        self._filter_updater.moveToThread(self._thread)
        self._thread.started.connect(self._filter_updater.update)
        self._thread.start()

    def initUI(self):
        # configure window
        self.setWindowTitle(self._title)
        self.setGeometry(self._left, self._top, self._width, self._height)

        # configure widgets

        '''
        Update Button and Cancel Button
        '''

        # Update Button
        self._PushButton_update = QtGui.QPushButton('Update Parameters', self)
        self._PushButton_update.setToolTip('Update parameters')
        self._PushButton_update.clicked.connect(self.updateParams)

        # Quit Button
        self._PushButton_quit = QtGui.QPushButton('Quit', self)
        self._PushButton_quit.setToolTip('Quit this application')
        self._PushButton_quit.clicked.connect(self.quitApp)

        # Layout for Update and Quit Button
        self._UpdateCancelButtonLayout = QtGui.QVBoxLayout()
        self._UpdateCancelButtonLayout.addWidget(self._PushButton_update)
        self._UpdateCancelButtonLayout.addWidget(self._PushButton_quit)

        '''
        Spin Box for Adjusting Measurement and Prediction History Display Length
        '''

        # Spin Box for Measurement History Length
        self._Label_measHistLen = QtGui.QLabel('Measurement History Length')
        self._Label_measHistLen.setAlignment(QtCore.Qt.AlignCenter)

        self._SpinBox_measHistLen = QtGui.QSpinBox()
        self._SpinBox_measHistLen.setRange(1, 10)
        self._SpinBox_measHistLen.setSingleStep(1)
        self._SpinBox_measHistLen.setValue(self._filter.getMeasHistLen())
        self._SpinBox_measHistLen.valueChanged.connect(self.updateMeasHistLen)

        # Spin Box for Prediction History Length
        self._Label_predHistLen = QtGui.QLabel('Prediction History Length')
        self._Label_predHistLen.setAlignment(QtCore.Qt.AlignCenter)

        self._SpinBox_predHistLen = QtGui.QSpinBox()
        self._SpinBox_predHistLen.setRange(1, 10)
        self._SpinBox_predHistLen.setSingleStep(1)
        self._SpinBox_predHistLen.setValue(self._filter.getPredHistLen())
        self._SpinBox_predHistLen.valueChanged.connect(self.updatePredHistLen)

        # Layout for Prediction History Control
        self._HistCtrlLayout = QtGui.QVBoxLayout()
        self._HistCtrlLayout.addWidget(self._Label_measHistLen)
        self._HistCtrlLayout.addWidget(self._SpinBox_measHistLen)
        self._HistCtrlLayout.addWidget(self._Label_predHistLen)
        self._HistCtrlLayout.addWidget(self._SpinBox_predHistLen)

        '''
        Slider Bar for Adjusting Mouse X and Y Position Noise Std
        '''

        # Spin Box for X Noise
        self._Label_xNoise = QtGui.QLabel('X Noise Std')
        self._Label_xNoise.setAlignment(QtCore.Qt.AlignCenter)

        self._Label_xNoiseVal = QtGui.QLabel(str(50.0))
        self._Label_xNoiseVal.setAlignment(QtCore.Qt.AlignCenter)

        self._Slider_xNoise = QtGui.QSlider(QtCore.Qt.Horizontal)
        self._Slider_xNoise.setMinimum(0.0)
        self._Slider_xNoise.setMaximum(150.0)
        self._Slider_xNoise.setValue(50.0)
        self._Slider_xNoise.setTickInterval(1.0)
        self._Slider_xNoise.valueChanged.connect(self.updateXNoiseStd)
        self._filter.setXNoiseStd(50.0)

        # Spin Box for Y Noise
        self._Label_yNoise = QtGui.QLabel('Y Noise Std')
        self._Label_yNoise.setAlignment(QtCore.Qt.AlignCenter)

        self._Label_yNoiseVal = QtGui.QLabel(str(50.0))
        self._Label_yNoiseVal.setAlignment(QtCore.Qt.AlignCenter)

        self._Slider_yNoise = QtGui.QSlider(QtCore.Qt.Horizontal)
        self._Slider_yNoise.setMinimum(0.0)
        self._Slider_yNoise.setMaximum(150.0)
        self._Slider_yNoise.setValue(50.0)
        self._Slider_yNoise.setTickInterval(1.0)
        self._Slider_yNoise.valueChanged.connect(self.updateYNoiseStd)
        self._filter.setYNoiseStd(50.0)

        # Layout for Noise
        self._NoiseCtrlLayout = QtGui.QVBoxLayout()
        self._NoiseCtrlLayout.addWidget(self._Label_xNoise)
        self._NoiseCtrlLayout.addWidget(self._Label_xNoiseVal)
        self._NoiseCtrlLayout.addWidget(self._Slider_xNoise)
        self._NoiseCtrlLayout.addWidget(self._Label_yNoise)
        self._NoiseCtrlLayout.addWidget(self._Label_yNoiseVal)
        self._NoiseCtrlLayout.addWidget(self._Slider_yNoise)

        '''
        Parameters
        '''

        self._Label_Params = {}
        self._Grid_Params = {}
        self._Edit_Params = {}
        self._Layout_Params = {}
        self._Layout_AllParams = QtGui.QHBoxLayout()
        self._Layout_AllParams.setSpacing(20)

        for p_key, p_val in self._filter.getFilterParams().iteritems():
            
            self._Label_Params[p_key] = QtGui.QLabel('{0:s} ({1:s})'.format(p_key, p_val.doc))
            self._Label_Params[p_key].setAlignment(QtCore.Qt.AlignCenter)

            self._Grid_Params[p_key] = QtGui.QGridLayout()
            self._Grid_Params[p_key].setHorizontalSpacing(0)
            self._Grid_Params[p_key].setVerticalSpacing(0)
            self._Edit_Params[p_key] = self.createMatrix4x4InputGUI(self._Grid_Params[p_key], p_val.data)
            
            self._Layout_Params[p_key] = QtGui.QVBoxLayout()
            self._Layout_Params[p_key].setSpacing(2)
            self._Layout_Params[p_key].addWidget(self._Label_Params[p_key])
            self._Layout_Params[p_key].addLayout(self._Grid_Params[p_key])

            self._Layout_AllParams.addLayout(self._Layout_Params[p_key])

        '''
        Live Update
        '''

        '''
        Main Layout
        '''

        # Layout
        self._ParamLayout = QtGui.QVBoxLayout()
        self._ParamLayout.addLayout(self._HistCtrlLayout)
        self._ParamLayout.addLayout(self._NoiseCtrlLayout)
        self._ParamLayout.addLayout(self._UpdateCancelButtonLayout)

        self._Layout = QtGui.QHBoxLayout()
        self._Layout.addWidget(self._plt.getPlot())
        self._Layout.addLayout(self._ParamLayout)

        self._LayoutMain = QtGui.QVBoxLayout()
        self._LayoutMain.addLayout(self._Layout)
        self._LayoutMain.addLayout(self._Layout_AllParams)

        self.setLayout(self._LayoutMain)

        # Show widget
        self.show()
    
    def createMatrix4x4InputGUI(self, GridLayout, ParamData):
        paramCellEdit = {}
        for i in range(4):
            for j in range(4):
                paramCellEdit[(i, j)] = QtGui.QLineEdit()
                paramCellEdit[(i, j)].setValidator(QtGui.QDoubleValidator())
                paramCellEdit[(i, j)].setText(str(ParamData[i, j]))
                GridLayout.addWidget(paramCellEdit[(i, j)], i, j)

        return paramCellEdit

    def stopThread(self):
        self._filter_updater.stop()
        self._thread.quit()
        self._thread.wait()

    def updateParams(self):
        print '{:50s}\n'.format(datetime.now().strftime('%m/%d/%y %I:%M:%S%p') + ' Updated Paramters')

        for p_key, p_val in self._Edit_Params.iteritems():
            for 
            
            self._filter.setFilterParams()

    def quitApp(self):
        print '{:50s}\n'.format(datetime.now().strftime('%m/%d/%y %I:%M:%S%p') + ' Exit application')
        self.stopThread()
        QtCore.QCoreApplication.instance().quit()

    def updateMeasHistLen(self):
        print '{:50s}\n'.format(datetime.now().strftime('%m/%d/%y %I:%M:%S%p') + ' Updated Measurement History Length to {0:d}'.format(self._SpinBox_measHistLen.value()))
        self._filter.setMeasHistLen(self._SpinBox_measHistLen.value())

    def updatePredHistLen(self):
        print '{:50s}\n'.format(datetime.now().strftime('%m/%d/%y %I:%M:%S%p') + ' Updated Prediction History Length to {0}'.format(self._SpinBox_predHistLen.value()))
        self._filter.setPredHistLen(self._SpinBox_predHistLen.value())

    def updateXNoiseStd(self):
        print '{:50s}\n'.format(datetime.now().strftime('%m/%d/%y %I:%M:%S%p') + ' Updated X Noise Std to {0}'.format(self._Slider_xNoise.value()))
        self._Label_xNoiseVal.setText('{:.1f}'.format(self._Slider_xNoise.value()))
        self._filter.setXNoiseStd(self._Slider_xNoise.value())

    def updateYNoiseStd(self):
        print '{:50s}\n'.format(datetime.now().strftime('%m/%d/%y %I:%M:%S%p') + ' Updated Y Noise Std to {0}'.format(self._Slider_yNoise.value()))
        self._Label_yNoiseVal.setText('{:.1f}'.format(self._Slider_yNoise.value()))
        self._filter.setYNoiseStd(self._Slider_yNoise.value())

def main():

    print 'Press Ctrl+C to quit.\n'
    
    print 'Red is the real mouse pointer positions.'
    print 'Blue is the Kalman filter predicted mouse pointer positions.\n'

    app = QtGui.QApplication(sys.argv)
    fltr = Filter(FITLER_TYPE)
    plt = Plot()
    ex = App(plt, fltr)

    proxy = pg.SignalProxy(plt.getPlot().scene().sigMouseMoved, delay=0, rateLimit=1000.0, slot=plt.mousePosUpdate)

    sys.exit(app.exec_())

if __name__ == "__main__":
        main()