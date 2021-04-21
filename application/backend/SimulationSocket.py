from tornado.ioloop import IOLoop, PeriodicCallback
from tornado import gen
from tornado.websocket import websocket_connect
import time

class SimulationSocket(object):
    def __init__(self, tobii_controller):
        self.tobii_controller = tobii_controller
        self.ws = None
        self.track_data = False
        # list of coordinate dicts to loop through in the function
        # can add more objects if needed, as long as the format of the object stays as:
        # {"x": <your x coordinate>, "y": <your y coordinate>, "time": <i or a timestamp>}
        self.coordinates = [
            {"x": 400, "y": 310, "time": 1}
        ]

    @gen.coroutine
    def connect(self):
        try:
            IOLoop.instance().add_callback(callback = self.run)
        except Exception, e:
            print "connection error"
        else:
            print "simulation started"
			
    @gen.coroutine
    def run(self):
        i = 1
        #time.sleep(10)
        while True:
            self.coordinates = [
                {"x": 400, "y": 310, "time": i},
                {"x": 600, "y": 310, "time": i}
            ]
            index = 0

            if self.track_data:
                index = (index + 1) % len(self.coordinates) if (i % 10) == 0 else index
                self.tobii_controller.on_gazedata_simulation(self.coordinates[index]["x"], self.coordinates[index]["y"], self.coordinates[index]["time"] * 20000)
                yield gen.sleep(.1)
                i += 1

    def start_tracking(self):
        self.track_data = True
        self.connect()

    def stop_tracking(self):
        self.track_data = False
