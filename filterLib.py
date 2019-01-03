import numpy as np
import copy
from collections import OrderedDict

class FilterParameter(object):
    """ Filter Parameter Class
    To hold the parameter name, data and documentation for single parameter
    """

    def __init__(self, name, data, doc=None):
        self._name = copy.deepcopy(name)
        self._data = copy.deepcopy(data)
        self._doc = copy.deepcopy(doc)
    
    @property
    def name(self):
        return self._name

    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, d):
        print 'Set Parameter {0} to'.format(self._name)
        print d, '\n'

        self._data = copy.deepcopy(d)

    @property
    def doc(self):
        return self._doc

class KalmanFilter:
    """ Kalman Filter Class 
    for containing filter related parameters and handle filter basic operations

    states of mouse pointer: [x, y, dx, dy]
    
    State Transition Matrix:
    A = [[1, 0, 0.25, 0],
        [0, 1, 0, 0.25],
        [0, 0, 1, 0],
        [0, 0, 0, 1]]

    Control Matrix:
    B = indentity(4)

    Measurement Matrix:
    C = [[1, 0, 1, 0],
        [0, 1, 0, 1],
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

    def __init__(self):
        self._params = OrderedDict()
        self._params['A'] = FilterParameter('A', np.identity(4), 'State Transition Matrix')
        self._params['A'].data[0, 2] = 0.25
        self._params['A'].data[1, 3] = 0.25

        self._params['B'] = FilterParameter('B', np.identity(4), 'Control Matrix')

        self._params['C'] = FilterParameter('C', np.identity(4), 'Measurement Matrix')
        self._params['C'].data[0, 2] = 1.0
        self._params['C'].data[1, 3] = 1.0

        self._params['Q'] = FilterParameter('Q', np.zeros((4, 4)), 'Action Uncertainty Matrix')
        self._params['Q'].data[2, 2] = 0.1
        self._params['Q'].data[3, 3] = 0.1

        self._params['R'] = FilterParameter('R', np.identity(4)*0.1, 'Sensor Noise Matrix')
        
        # state
        self._X_curr = np.zeros((4, 1))
        self._X_prev = np.zeros((4, 1))
        self._X_pred = np.zeros((4, 1))

        # uncertainty
        self._P_curr = np.zeros((4, 4))
        self._P_prev = np.zeros((4, 4))
        self._P_pred = np.zeros((4, 4))

        # measurement
        self._Y_curr = np.zeros((4, 1))

        # Kalman gain
        self._K = np.zeros((4, 4))

        self._time_curr = 0
        self._time_prev = 0

    def getParams(self):
        return self._params
    
    def setParam(self, n, val):
        self._params[n].data = val

    def getPredictiedStates(self):
        return self._X_curr

    def getMeasuredStates(self):
        return self._Y_curr

    def updateMeasurements(self, x, y, time):
        """
        Function updates the mouse state measurement, in this case just reading mouse position with/without noise injection from PyAuotGUI
        """
        
        self._time_curr = time
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

        self._X_pred = self._params['A'].data.dot(self._X_prev) + self._params['B'].data.dot(U)
        self._P_pred = self._params['A'].data.dot(self._P_prev).dot(self._params['A'].data.T) + self._params['Q'].data
    
    def update(self):
        """
        Update the predicted state based of the measurement
        """

        self._K = self._P_pred.dot(self._params['C'].data.T).dot(np.linalg.inv(self._params['C'].data.dot(self._P_pred).dot(self._params['C'].data.T) + self._params['R'].data))
        
        self._X_curr = self._X_pred + self._K.dot(self._Y_curr - self._params['C'].data.dot(self._X_pred))
        self._P_curr = (np.identity(4) - self._K.dot(self._params['C'].data)).dot(self._P_pred)

# Add filters here
FILTERS = {'KalmanFilter': KalmanFilter, 'NoFilter': None}