
import sys, os
import params
#This sets the path in our computer to where the eyetracker stuff is located
#sys.path.append('/Users/Preetpal/desktop/ubc_4/experimenter_platform/modules')
#sys.path.append('E\\Users\\admin\\Desktop\\experimenter_platform\\modules')
sys.path.append(os.path.join(sys.path[0],'Modules'))
sys.path.append(os.path.join(sys.path[0],'tobii_binder'))

import os
import datetime
import time

import tobii_research as tr

import csv
import numpy as np
from tornado import gen
import emdat_utils
import ast
import subprocess
from application.backend.eye_tracker_class import *


class TobiiControllerNewSdk:

    """    The singleton class used to communicate with Tobii eye tracker API: it initializes the eye tracker,
    stores the raw gaze data, so the detection components can compute the features
    they are responsible for, and it stores the EMDAT features computed over the whole execution of the platform.
    """

    def __init__(self):

        """Initializes TobiiController instances

        keyword arguments
        None
        """
        print("constructing eyetracker object")

        self.gazeData = []
        self.eventData = []
        self.datafile = None
        #Preetpal's code for fixation
        self.x = []
        self.y = []
        self.time = []
        self.validity = []
        self.pupilsize = []
        self.pupilvelocity = []
        self.head_distance = []
        self.EndFixations = []
        self.mouse_clicks = []
        self.keyboard_clicks = []
        #This contains the websocket to send data to be displayed on front end
        self.runOnlineFix = True
        # initialize communications
        self.aoi_ids = {}
        self.dpt_id = 0

        # for computing pupil velocity
        self.last_pupil_left = -1
        self.last_pupil_right = -1
        self.LastTimestamp = -1
        self.init_emdat_global_features()

        
        # Instantiate an eye tracker class corresponding to the EYETRACKER_TYPE determined inside the params.py file
        self.eye_tracker = globals()[EyeTrackerNames[params.EYETRACKER_TYPE].value]()
        print("constructed eyetracker object")
    ############################################################################
    # activation methods
    ############################################################################
    def activate(self):
        self.eye_tracker.activate(self)


    def startTracking(self):
        """Starts the collection of gaze data

        arguments
        None

        keyword arguments
        None

        returns
        None        --    resets both self.gazeData and self.eventData, then
                    sets TobiiTracker.on_gazedata as an event callback
                    for self.eyetracker.events.OnGazeDataReceived and
                    calls self.eyetracker.StartTracking()
        """
        print("starting tracker")
        self.gazeData = []
        self.eventData = []
        #Preetpal's Code to initialize/empty arrays to be used in fixation algorithm
        self.x = []
        self.y = []
        self.time = []
        self.validity = []
        self.pupilsize = []
        self.pupilvelocity = []
        self.head_distance = []
        self.mouse_clicks = []
        self.keyboard_clicks = []
        print("=================== SLEEPING =========================")
        time.sleep(1)
        print("=================== WOKE UP =========================")
        self.eye_tracker.start_tracking(self)


    def stopTracking(self):
        """Stops the collection of gaze data

        arguments
        None

        keyword arguments
        None

        returns
        None        --    calls self.eyetracker.StopTracking(), then unsets
                    TobiiTracker.on_gazedata as an event callback for
                    self.eyetracker.events.OnGazeDataReceived, and
                    calls TobiiTracker.flushData before resetting both
                    self.gazeData and self.eventData
        """
        self.eye_tracker.stop_tracking(self)
        #self.flushData()
        self.gazeData = []
        self.EndFixations = []
        #Preetpals code
        #Empty the arrays needed for fixation algorithm
        #May need to also empty the websocket set
        self.x = []
        self.y = []
        self.time = []
        self.validity = []
        self.pupilsize = []
        self.pupilvelocity = []
        self.head_distance = []
        self.mouse_clicks = []
        self.keyboard_clicks = []
        self.aoi_ids = {}
        self.dpt_id = 0


    def logFixations(self, user_id, task_id):
        """Log the recorded fixations for the current user and task

        arguments
        user_id ID of current user_id
        task_id ID of current task

        keyword arguments
        None

        returns
        None
        """
        with open(str(params.LOG_PREFIX) + "_user_" + str(user_id) + "_task_"+str(task_id) + "_raw_fixations.csv", "wb") as f:
            f.write( "x,y,duration,start_time\n" ) # header
            for fix in self.EndFixations:
                f.write( ",".join([str(x) for x in fix])+"\n" )


    def on_gazedata(self, gaze):

        """Adds new data point to the raw data arrays. If x, y coordinate data is not available,
        stores the coordinates for this datapoint as (-1280, -1024). Any other feature,
        if not available, is stored as -1.

        arguments
        error        --    some Tobii error message, isn't used in function
        gaze        --    Tobii gaze data struct

        keyword arguments
        None

        returns
        None        --    appends gaze to self.gazeData list
        """
        #Don't need raw gaze so this code is commented out
        #self.gazeData.append(gaze)

        #Below code is just print statements that are commented out
        '''
        print gaze.keys()
        print 'Timestamp: ', gaze["device_time_stamp"]
        print 'LeftGazePoint2D: ', gaze["left_gaze_point_on_display_area"]
        print 'RightGazePoint2D: ', gaze["right_gaze_point_on_display_area"]
        print 'LeftEyePosition3D: ', gaze["left_gaze_point_in_user_coordinate_system"]
        print 'RightEyePosition3D', gaze["right_gaze_point_in_user_coordinate_system"]
        print 'LeftPupil: ', gaze["left_pupil_diameter"]
        print 'RightPupil: ', gaze["right_pupil_diameter"]
        print gaze["left_gaze_point_validity"]
        print gaze["right_gaze_point_validity"]
        '''

        #Below code checks to see if the gaze data is valid. If it is valid then
        #we average the left and right. Else we use the valid eye. We are multiplying
        #by SCREEN_SIZE_X and SCREEN_SIZE_Y because those are the dimensions of the monitor and since
        #the gaze values returned are between 0 and 1
        if ((gaze["left_gaze_point_on_display_area"][0] >= 0) & (gaze["right_gaze_point_on_display_area"][0] >= 0)):
            self.x.append(((gaze["left_gaze_point_on_display_area"][0] + gaze["right_gaze_point_on_display_area"][0])/2) * params.SCREEN_SIZE_X)
            self.y.append(((gaze["left_gaze_point_on_display_area"][1] + gaze["right_gaze_point_on_display_area"][1])/2) * params.SCREEN_SIZE_Y)
        elif (gaze["left_gaze_point_on_display_area"][0] >= 0):
            self.x.append(gaze["left_gaze_point_on_display_area"][0] * params.SCREEN_SIZE_X)
            self.y.append(gaze["left_gaze_point_on_display_area"][1] * params.SCREEN_SIZE_Y)
        elif (gaze["right_gaze_point_on_display_area"][0] >= 0):
            self.x.append(gaze["right_gaze_point_on_display_area"][0] * params.SCREEN_SIZE_X)
            self.y.append(gaze["right_gaze_point_on_display_area"][1] * params.SCREEN_SIZE_Y)
        else:
            self.x.append(-1 * params.SCREEN_SIZE_X)
            self.y.append(-1 * params.SCREEN_SIZE_Y)
        #print(gaze.RightGazePoint2D.x * params.SCREEN_SIZE_X, gaze.RightGazePoint2D.y * params.SCREEN_SIZE_Y)
        # print("%f" % (time.time() * 1000.0))

        if (params.USE_EMDAT):
            for aoi, polygon in self.AOIs.iteritems():
                if utils.point_inside_polygon((self.x[-1], self.y[-1]), polygon):
                    self.aoi_ids[aoi].append(self.dpt_id)
        # Pupil size features
        self.pupilsize.append(self.get_pupil_size(gaze["left_pupil_diameter"], gaze["right_pupil_diameter"]))
        if (self.last_pupil_right != -1):
            self.pupilvelocity.append(self.get_pupil_velocity(self.last_pupil_left, self.last_pupil_right, gaze["left_pupil_diameter"], gaze["right_pupil_diameter"], gaze["device_time_stamp"] - self.LastTimestamp))
        else:
            self.pupilvelocity.append(-1)
        self.time.append(gaze["device_time_stamp"])
        self.head_distance.append(self.get_distance(gaze["left_gaze_point_in_user_coordinate_system"][2], gaze["right_gaze_point_in_user_coordinate_system"][2]))
        self.validity.append(gaze["left_gaze_point_validity"] == 1 or gaze["right_gaze_point_validity"] == 1)

        # for pupil velocity
        self.last_pupil_left = gaze["left_pupil_diameter"]
        self.last_pupil_right = gaze["right_pupil_diameter"]
        self.LastTimestamp = gaze["device_time_stamp"]
        self.dpt_id += 1

    def on_gazedata_4c(self, x, y, time_stamp):

        """Adds new data point to the raw data arrays. If x, y coordinate data is not available,
        stores the coordinates for this datapoint as (-1280, -1024). Any other feature,
        if not available, is stored as -1.
        arguments
        error        --    some Tobii error message, isn't used in function
        gaze        --    Tobii gaze data struct
        keyword arguments
        None
        returns
        None        --    appends gaze to self.gazeData list
        """
        #Don't need raw gaze so this code is commented out
        #self.gazeData.append(gaze)

        # print(gaze.RightGazePoint2D.x * 1280, gaze.RightGazePoint2D.y * 1024)
        # print("%f" % (time.time() * 1000.0))
        self.x.append(x)
        self.y.append(y)
        if (params.USE_EMDAT):
            for aoi, polygon in self.AOIs.iteritems():
                if utils.point_inside_polygon((self.x[-1], self.y[-1]), polygon):
                    print("point inside ", aoi)
                    self.aoi_ids[aoi].append(self.dpt_id)
        self.time.append(time_stamp)
        self.validity.append(True)
        self.LastTimestamp = time_stamp
        self.dpt_id += 1
		
    def on_gazedata_simulation(self, x, y, time_stamp):

        """Adds new data point to the raw data arrays. If x, y coordinate data is not available,
        stores the coordinates for this datapoint as (-1280, -1024). Any other feature,
        if not available, is stored as -1.
        arguments
        error        --    some Tobii error message, isn't used in function
        gaze        --    Tobii gaze data struct
        keyword arguments
        None
        returns
        None        --    appends gaze to self.gazeData list
        """
        #Don't need raw gaze so this code is commented out
        #self.gazeData.append(gaze)

        # print(gaze.RightGazePoint2D.x * 1280, gaze.RightGazePoint2D.y * 1024)
        # print("%f" % (time.time() * 1000.0))
        self.x.append(x)
        self.y.append(y)
        if (params.USE_EMDAT):
            for aoi, polygon in self.AOIs.iteritems():
                if utils.point_inside_polygon((self.x[-1], self.y[-1]), polygon):
                    print("point inside ", aoi)
                    self.aoi_ids[aoi].append(self.dpt_id)
        self.time.append(time_stamp)
        self.validity.append(True)
        self.LastTimestamp = time_stamp
        self.dpt_id += 1


    def add_fixation(self, x, y, duration, start_time):
        '''
        Called by FixationDetector when a new fixation is detected.
        Adds a new fixation to data array to be used for EMDAT features calculation.
        Args:
            x             - coordinate of fixation on the screen
            y             - coordinate of fixation on the screen
            duration     - duration of fixation in microseconds
        '''
        self.EndFixations.append((x, y, duration, start_time))

    def add_mouse_key_click(self, mouse_click):
        '''
        Called by MouseKeyboardEventDetector when a new mouse click is detected.
        Adds a new mouse click to data array to be used for EMDAT features calculation.
        Args:
            mouse_click - BasicMouseEvent object
        '''
        self.mouse_clicks.append(mouse_click)

    def add_keyboard_click(self, keyboard_click):
        '''
        Called by MouseKeyboardEventDetector when a new keyboard click is detected.
        Adds a new keyboard click to data array to be used for EMDAT features calculation.
        Args:
            keyboard_click - KeyboardEvent object
        '''
        self.keyboard_clicks.append(keyboard_click)

    def get_pupil_size(self, pupilleft, pupilright):
        '''
        Used for extracting pupilsize in on_gazedata(). If recordings for both eyes are available, return their average,
        else return value for a recorded eye (if any)
        Args:
            pupilleft - recording of pupil size on left eye
            pupilright - recording of pupil size on right eye
        Returns:
            pupil size to generate pupil features with.
        '''
        if pupilleft == 0 and pupilright == 0:
            return -1
        if pupilleft == 0:
            return pupilright
        if pupilright == 0:
            return pupilleft
        return (pupilleft + pupilright) / 2.0


    def get_pupil_velocity(self, last_pupilleft, last_pupilright, pupilleft, pupilright, time):
        '''
        Used for extracting pupilvelocity in on_gazedata().
        If pupilsizes for both eyes are available, return the average of their difference,
        else return value for a recorded eye (if any)
        Args:
            last_pupilleft - pupilsize for left eye from previous gaze object
            last_pupilright - pupilsize for right eye from previous gaze object
            pupilleft - pupilsize for left eye from current gaze object
            pupilright - pupilsize for left eye from current gaze object
            time - timestamp difference between current and last gaze object

        '''
        if (last_pupilleft == 0 or pupilleft == 0) and (last_pupilright == 0 or pupilright == 0):
             return -1
        if (last_pupilleft == 0 or pupilleft == 0):
            return abs(pupilright - last_pupilright) / time
        if (last_pupilright == 0 or pupilright == 0):
            return abs(pupilleft - last_pupilleft) / time
        return abs( (pupilleft + pupilright) / 2 - (last_pupilleft + last_pupilright) / 2 ) / time

    def get_distance(self, distanceleft, distanceright):
        '''
        Used for extracting head distance in on_gazedata(). If recordings for both eyes are available, return their average,
        else return value for a recorded eye (if any)
        Args:
            distanceleft - recording of distance on left eye
            distanceright - recording of distance size on right eye
        '''
        if distanceleft == 0 and distanceright == 0:
            return -1
        if distanceleft == 0:
            return distanceright
        if distanceright == 0:
            return distanceleft
        return (distanceleft + distanceright) / 2.0

    def update_aoi_storage(self, AOIS):
        """
            Add new aois to global EMDAT feature storage dictionary.
            Called during a task switch by EMDATComponent.
        """

        self.AOIs = AOIS
        for event_name in AOIS.keys():
            self.aoi_ids[event_name] = []
            if event_name not in self.emdat_global_features:
                self.emdat_global_features[event_name] = {}
                self.emdat_global_features[event_name]['numfixations']                 = 0
                self.emdat_global_features[event_name]['longestfixation']            = -1
                self.emdat_global_features[event_name]['meanfixationduration']      = -1
                self.emdat_global_features[event_name]['stddevfixationduration']    = -1
                self.emdat_global_features[event_name]['timetofirstfixation']       = -1
                self.emdat_global_features[event_name]['timetolastfixation']        = -1
                self.emdat_global_features[event_name]['proportionnum']                  = 0
                self.emdat_global_features[event_name]['proportiontime']            = 0
                self.emdat_global_features[event_name]['fixationrate']                   = 0
                self.emdat_global_features[event_name]['totaltimespent']            = 0
                self.emdat_global_features[event_name]['meanpupilsize']                  = -1
                self.emdat_global_features[event_name]['stddevpupilsize']            = -1
                self.emdat_global_features[event_name]['maxpupilsize']                   = -1
                self.emdat_global_features[event_name]['minpupilsize']                   = -1
                self.emdat_global_features[event_name]['startpupilsize']             = -1
                self.emdat_global_features[event_name]['endpupilsize']                   = -1
                self.emdat_global_features[event_name]['meanpupilvelocity']          = -1
                self.emdat_global_features[event_name]['stddevpupilvelocity']        = -1
                self.emdat_global_features[event_name]['maxpupilvelocity']           = -1
                self.emdat_global_features[event_name]['minpupilvelocity']           = -1
                self.emdat_global_features[event_name]['numpupilsizes']                  = 0
                self.emdat_global_features[event_name]['numpupilvelocity']           = 0
                self.emdat_global_features[event_name]['numdistancedata']            = 0
                self.emdat_global_features[event_name]['numdistancedata']             = 0
                self.emdat_global_features[event_name]['meandistance']               = -1
                self.emdat_global_features[event_name]['stddevdistance']             = -1
                self.emdat_global_features[event_name]['maxdistance']                = -1
                self.emdat_global_features[event_name]['mindistance']                = -1
                self.emdat_global_features[event_name]['startdistance']              = -1
                self.emdat_global_features[event_name]['enddistance']                = -1
                self.emdat_global_features[event_name]['total_trans_from']            = 0
                self.emdat_global_features[event_name]['startpupilvelocity']        = -1
                self.emdat_global_features[event_name]['endpupilvelocity']             = 0

                self.emdat_global_features[event_name]['numevents']                 = 0
                self.emdat_global_features[event_name]['numleftclic']                 = 0
                self.emdat_global_features[event_name]['numrightclic']                 = 0
#               self.emdat_global_features[event_name]['numdoubleclic']                = 0
                self.emdat_global_features[event_name]['numkeypressed']             = 0
#               self.emdat_global_features[event_name]['numdragdrop']                 = 0
                self.emdat_global_features[event_name]['leftclicrate']                 = -1
                self.emdat_global_features[event_name]['rightclicrate']             = -1
#               self.emdat_global_features[event_name]['doubleclicrate']            = -1
                self.emdat_global_features[event_name]['keypressedrate']             = -1
#               self.emdat_global_features[event_name]['dragdroprate']                 = -1
#               self.emdat_global_features[event_name]['timetofirstleftclic']         = -1
#               self.emdat_global_features[event_name]['timetofirstrightclic']         = -1
#               self.emdat_global_features[event_name]['timetofirstdoubleclic']     = -1
#               self.emdat_global_features[event_name]['timetofirstkeypressed']     = -1
                for cur_aoi in AOIS.keys():
                    self.emdat_global_features[event_name]['numtransfrom_%s'%(cur_aoi)] = 0
                    self.emdat_global_features[event_name]['proptransfrom_%s'%(cur_aoi)] = -1


    def init_emdat_global_features(self):
        '''
        Initialize global EMDAT feature storage dictionary. Called by EMDATComponent.
        '''
        self.emdat_global_features                                 = {}
        self.emdat_global_features['length']                     = 0
        self.emdat_global_features['length_invalid']             = 0
        # Pupil features
        self.emdat_global_features['numpupilsizes']                = 0
        self.emdat_global_features['numpupilvelocity']          = 0
        self.emdat_global_features['meanpupilsize']             = -1
        self.emdat_global_features['stddevpupilsize']             = -1
        self.emdat_global_features['maxpupilsize']                 = -1
        self.emdat_global_features['minpupilsize']                 = -1
        self.emdat_global_features['startpupilsize']             = -1
        self.emdat_global_features['endpupilsize']                 = -1
        self.emdat_global_features['meanpupilvelocity']         = -1
        self.emdat_global_features['stddevpupilvelocity']         = -1
        self.emdat_global_features['maxpupilvelocity']             = -1
        self.emdat_global_features['minpupilvelocity']             = -1
        self.emdat_global_features['startpupilvelocity']         = -1
        self.emdat_global_features['endpupilvelocity']             = -1
        # Distance features
        self.emdat_global_features['numdistancedata']            = 0
        self.emdat_global_features['meandistance']                 = -1
        self.emdat_global_features['stddevdistance']             = -1
        self.emdat_global_features['maxdistance']                 = -1
        self.emdat_global_features['mindistance']                 = -1
        self.emdat_global_features['startdistance']             = -1
        self.emdat_global_features['enddistance']                 = -1
        # Path features
        self.emdat_global_features['numfixdistances']             = 0
        self.emdat_global_features['numabsangles']                 = 0
        self.emdat_global_features['numrelangles']                 = 0
        self.emdat_global_features['meanpathdistance']             = -1
        self.emdat_global_features['sumpathdistance']             = -1
        self.emdat_global_features['stddevpathdistance']         = -1
        self.emdat_global_features['eyemovementvelocity']         = -1
        self.emdat_global_features['sumabspathangles']             = -1
        self.emdat_global_features['abspathanglesrate']         = -1
        self.emdat_global_features['meanabspathangles']            = -1
        self.emdat_global_features['stddevabspathangles']        = -1
        self.emdat_global_features['sumrelpathangles']             = -1
        self.emdat_global_features['relpathanglesrate']         = -1
        self.emdat_global_features['meanrelpathangles']            = -1
        self.emdat_global_features['stddevrelpathangles']         = -1
        # Fixation features
        self.emdat_global_features['numfixations']                 = 0
        self.emdat_global_features['fixationrate']                 = -1
        self.emdat_global_features['meanfixationduration']         = -1
        self.emdat_global_features['stddevfixationduration']     = -1
        self.emdat_global_features['sumfixationduration']         = -1
        self.emdat_global_features['fixationrate']                 = -1
        # Event features
        self.emdat_global_features['numevents']                 = 0
        self.emdat_global_features['numleftclic']                 = 0
        self.emdat_global_features['numrightclic']                 = 0
#       self.emdat_global_features['numdoubleclic']                = 0
        self.emdat_global_features['numkeypressed']             = 0
#       self.emdat_global_features['numdragdrop']                 = 0
        self.emdat_global_features['leftclicrate']                 = -1
        self.emdat_global_features['rightclicrate']             = -1
#       self.emdat_global_features['doubleclicrate']            = -1
        self.emdat_global_features['keypressedrate']             = -1
#       self.emdat_global_features['dragdroprate']                 = -1
#       self.emdat_global_features['timetofirstleftclic']         = -1
#       self.emdat_global_features['timetofirstrightclic']         = -1
#       self.emdat_global_features['timetofirstdoubleclic']     = -1
#       self.emdat_global_features['timetofirstkeypressed']     = -1

#Original code provided by Roberto showing how to start the the eyetracker
"""
#this will be called from a tornado handler
if __name__ == "__main__":
    eb = TobiiController()
    eb.waitForFindEyeTracker()
    print eb.eyetrackers
    eb.activate(eb.eyetrackers.keys()[0])

    eb.startTracking()
    time.sleep(10)
    eb.stopTracking()

    eb.destroy()
"""
