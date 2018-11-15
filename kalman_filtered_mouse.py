import time
import pyautogui
import numpy as np

# KalmanFilter class handles all the calculation in the kalman filter
class KalmanFilteredMouse:

    def __init__(self):
        """
        states of mouse pointer: [x, y, dx, dy]
        
        State Transition Matrix:
        A = [[1, 0, 0.25, 0],
             [0, 1, 0, 0.25],
             [0, 0, 1, 0],
             [0, 0, 0, 1]]

        Control Matrix:
        B = indentity(4)

        Measurement Matrix:
        C = [[1, 0, 0, 0],
             [0, 1, 0, 0],
             [0, 0, 1, 0],
             [0, 0, 0, 1]]

        Action Uncertainty Matrix:
        Q = [[0, 0, 0, 0],
             [0, 0, 0, 0],
             [0, 0, 0.1, 0],
             [0, 0, 0, 0.1]]

        Sensor Noise Matrix:
        R = [[0.1, 0, 0, 0],
             [0, 0.1, 0, 0],
             [0, 0, 0.1, 0],
             [0, 0, 0, 0.1]]
        
        """
    
        self._A = np.identity(4)
        self._A[0,2] = 0.25
        self._A[1,3] = 0.25

        self._B = np.identity(4)

        self._C = np.identity(4)
        self._C[0,2] = 1
        self._C[0,3] = 1

        self._Q = np.zeros((4, 4))
        self._Q[2,2] = 0.1
        self._Q[3,3] = 0.1

        self._R = np.identity(4)*0.1
        
        self._X_curr = np.zeros((4, 1))
        self._X_prev = np.zeros((4, 1))
        self._X_pred = np.zeros((4, 1))

        self._P_curr = np.zeros((4, 4))
        self._P_prev = np.zeros((4, 4))
        self._P_pred = np.zeros((4, 4))

        self._Y_curr = np.zeros((4, 1))

        self._K = np.zeros((4, 4))

        self._time_curr = time.time()
        self._time_prev = time.time()

    def getPredictiedStates(self):
        return self._X_curr

    def getMeasuredStates(self):
        return self._Y_curr

    def updateMeasurements(self, x, y):
        """
        Function updates the mouse state measurement, in this case just reading mouse position from PyAuotGUI
        """
        
        self._time_curr = time.time()
        d_time = self._time_curr - self._time_prev

        d_x = (x - self._Y_curr[0,0]) / d_time
        d_y = (y - self._Y_curr[1,0]) / d_time

        self._Y_curr[0,0] = x
        self._Y_curr[1,0] = y
        self._Y_curr[2,0] = d_x
        self._Y_curr[3,0] = d_y

    def predict(self, U= np.zeros((4, 1))):
        """
        Predict states and uncertainty based on the previous state and motion model
        """

        self._X_prev = self._X_curr
        self._P_prev = self._P_curr

        self._X_pred = self._A.dot(self._X_prev) + self._B.dot(U)
        self._P_pred = self._A.dot(self._P_prev).dot(self._A.T) + self._Q
    
    def update(self):
        """
        Update the predicted state based of the measurement
        """

        self._K = self._P_pred.dot(self._C.T).dot(np.linalg.inv(self._C.dot(self._P_pred).dot(self._C.T) + self._R))
        
        self._X_curr = self._X_pred + self._K.dot(self._Y_curr - self._C.dot(self._X_pred))
        self._P_curr = (np.identity(4) - self._K.dot(self._C)).dot(self._P_pred)