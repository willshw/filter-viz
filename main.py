#!/usr/bin/env python

import sys
from app import *

REFRESH_RATE = 30.0
FITLER_TYPE = 'KalmanFilter'

def main():
    # print 'Press Ctrl+C to quit.\n'
    app = QtGui.QApplication(sys.argv)
    fltr = Filter(FITLER_TYPE)
    plt = Plot()
    ex = App(plt, fltr, REFRESH_RATE)
    proxy = pg.SignalProxy(plt.getPlot().scene().sigMouseMoved, delay=0, rateLimit=1000.0, slot=plt.mousePosUpdate)
    sys.exit(app.exec_())

if __name__ == "__main__":
        main()