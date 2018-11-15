#!/usr/bin/env python

import sys
import time
import pyautogui
import kalman_mouse as km

def main():
    mouse_predictor = km.KalmanMouse()

    try:
        while True:
            x, y = pyautogui.position()

            mouse_predictor.predict()
            mouse_predictor.updateMeasurement()
            mouse_predictor.update()
            
            X = mouse_predictor.getPredictiedState()
            Y = mouse_predictor.getMeasuredStates()

            print "Measurement: ", Y
            print "Current:", X
            # print mouse_predictor.X_pred
            # print mouse_predictor.X_prev
            # print mouse_predictor.K

            # positionStr = 'X: ' + str(x).rjust(4) + ' Y: ' + str(y).rjust(4)
            # positionKalmanStr = ' X_km: ' + str(X[0,0]).rjust(4) + ' Y_km: ' + str(X[1,0]).rjust(4)
            # print positionStr+positionKalmanStr
            # print '\b' * (len(positionStr+positionKalmanStr) + 2),
            # sys.stdout.flush()
            
            time.sleep(1.0/30.0)
    except KeyboardInterrupt:
        print '\n'

if __name__ == "__main__":
    main()
