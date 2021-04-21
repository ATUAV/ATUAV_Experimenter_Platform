import sys, os
import tobii_research as tr
from websocket_client import EyetrackerWebsocketClient
from SimulationSocket import SimulationSocket
import subprocess
from enum import Enum

sys.path.append(os.path.join(sys.path[0],'Modules'))
sys.path.append(os.path.join(sys.path[0],'tobii_binder'))

"""
Eye Tracker class used to abstract some functionality in the code that depends on the eye tracker type
EyeTracker() is the parent/super class, and all the other eye tracker classes implement this class

EyeTracker class:
params:
- tracker_type -- the eye tracker type as a string

functions:
- activate()
    The function called to activate the eye tracker
- start_tracking()
    The function called to begin tracking fixations
- stop_tracking()
    The function called to stop tracking fixations
*note all of these functions are called and used in eye_tracker_newsdk.py only

The default activate(), start_tracking() and stop_tracking() existing in the parent class correspond to the Tobii 4C implementation

"""
# Parent eyetracker class
class EyeTracker(object):
    def __init__(self, tracker_type):
        self.tracker_type = tracker_type
    
    def activate(self, tobii_controller):
        print("connecting to default (Tobii 4c) eye tracker")
        subprocess.Popen("application/backend/websocket_app/GazeServer.exe")
        self.websocket_client = EyetrackerWebsocketClient(tobii_controller)
    

    def start_tracking(self, tobii_controller):
        self.websocket_client.start_tracking()

    def stop_tracking(self, tobii_controller):
        self.websocket_client.stop_tracking()


# Tobii T120 (old eyetracker) implemetation
class TobiiT120EyeTracker(EyeTracker):
    def __init__(self):
        super(TobiiT120EyeTracker, self).__init__("Tobii T120")
        self.eyetracker = None
        self.eyetrackers = {}
    
    def activate(self, tobii_controller):
        print("connecting to TobiiT120 eyetracker")
        while self.eyetracker is None:
            eyetrackers = tr.find_all_eyetrackers()
            for tracker in eyetrackers:
                self.eyetrackers[tracker.model] = tracker
            self.eyetracker = self.eyetrackers.get(self.tracker_type, None)
    

    def start_tracking(self, tobii_controller):
        self.eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, tobii_controller.on_gazedata, as_dictionary=True)

    def stop_tracking(self, tobii_controller):
        self.eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, tobii_controller.on_gazedata)

# Tobii Pro X3 implementation
class TobiiX3EyeTracker(EyeTracker):
    def __init__(self):
        super(TobiiX3EyeTracker, self).__init__("Tobii Pro X3-120 EPU")
        self.eyetracker = None
        self.eyetrackers = {}
    
    def activate(self, tobii_controller):
        print("connecting to Tobii Pro X3 eyetracker")
        while self.eyetracker is None:
            eyetrackers = tr.find_all_eyetrackers()
            for tracker in eyetrackers:
                self.eyetrackers[tracker.model] = tracker
            self.eyetracker = self.eyetrackers.get(self.tracker_type, None)
    

    def start_tracking(self, tobii_controller):
        self.eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, tobii_controller.on_gazedata, as_dictionary=True)

    def stop_tracking(self, tobii_controller):
        self.eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, tobii_controller.on_gazedata)

# 4C implementation
class Tobii4CEyeTracker(EyeTracker):
    def __init__(self):
        super(Tobii4CEyeTracker, self).__init__("IS4_Large_Peripheral")


# Simulation implementation
class SimulationEyeTracker(EyeTracker):
    def __init__(self):
        super(SimulationEyeTracker, self).__init__("simulation")
    
    def activate(self, tobii_controller):
        self.websocket_client = SimulationSocket(tobii_controller)
        print("connected to simulation eye tracker")



EyeTrackerNames = Enum(
    value="EyeTrackerNames",
    names=[
        ("Tobii T120", "TobiiT120EyeTracker"),
        ("IS4_Large_Peripheral", "Tobii4CEyeTracker"),
        ("simulation", "SimulationEyeTracker"),
        ("Tobii Pro X3-120 EPU", "TobiiX3EyeTracker")
    ]
)