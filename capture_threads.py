from PyQt5 import QtCore
import time


class Capture(QtCore.QThread):
    finished = QtCore.pyqtSignal(object)
    def __init__(self, dev):
        QtCore.QThread.__init__(self)
        self.dev = dev

    def run(self):
        image = self.dev.snapshot()
        if image is not None:
            self.finished.emit(image)


class TriggeredCapture(Capture):
    def run(self):
        image = self.triggered_snapshot(self.dev.Setting.Base.Camera.ImageRequestTimeout_ms.value)
        if image is not None:
            self.finished.emit(image)

    def triggered_snapshot(self, timeout_value):
        self.dev.image_request()
        try:
            result = self.dev.get_image(timeout=(float(timeout_value) / 1000.))
        except Exception as e:
            print "Did not recieve a trigger after " + str(timeout_value) + " milliseconds"
            self.dev.image_request_reset(0)
            return None
        else:
            print 'captured'
            img = result.get_buffer()
            del result
            return img


class AbsorptionCapture(TriggeredCapture):
    def __init__(self, dev):
        TriggeredCapture.__init__(self, dev)
        self.running = RunLock(False)

    def run(self, ):
        with self.running:
            imgs = []
            for i in range(3):
                image = self.triggered_snapshot(self.dev.Setting.Base.Camera.ImageRequestTimeout_ms.value)
                if image is None:
                    print 'failed to acquire an image'
                    return
                imgs.append(image)

            self.finished.emit(imgs)


class DelayedCapture(Capture):
    def __init__(self, dev, min_delay = 0):
        Capture.__init__(self, dev)
        self.min_delay = min_delay
        self.last_time = time.time()

    def run(self,):
        self.delayed_capture()

    def delayed_capture(self):
        while time.time() - self.last_time < self.min_delay:
            pass
        image = self.dev.snapshot()
        if image is not None:
            self.finished.emit(image)
        self.last_time = time.time()


class ContinuousCapture(DelayedCapture):
    def __init__(self, dev, min_delay = 0):
        DelayedCapture.__init__(self, dev, min_delay)
        self._stop = False

    def run(self,):
        while not self._stop:
            self.delayed_capture()
        self._stop = False

    def stop(self):
        self._stop = True


class RunLock(object):
    def __init__(self, state):
        self.state = state

    def __enter__(self):
        self.state = True

    def __exit__(self, *args):
        self.state = False
