from PyQt5 import QtCore
import time


class Capture(QtCore.QThread):
    finished = QtCore.pyqtSignal(object)
    def __init__(self, dev, lock):
        QtCore.QThread.__init__(self)
        self.dev = dev
        self.lock = lock

    def run(self):
        if self.lock.state:
            print RuntimeError('Tried to capture while another thread is active')
            return
        with self.lock:
            self.capture()

    def capture(self):
        image = self.dev.snapshot()
        if image is not None:
            self.finished.emit(image)

class TriggeredCapture(Capture):
    def capture(self):
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
    def __init__(self, dev, lock):
        TriggeredCapture.__init__(self, dev, lock)

    def capture(self):
        imgs = []
        for i in range(3):
            image = self.triggered_snapshot(self.dev.Setting.Base.Camera.ImageRequestTimeout_ms.value)
            if image is None:
                print 'failed to acquire an image'
                return
            imgs.append(image)
        imgs[1] = ((imgs[1] - 255)* 0.1)+255
        imgs[2] = imgs[2] * 0.001
        self.finished.emit(imgs)


class DelayedCapture(Capture):
    def __init__(self, dev, lock, min_delay = 0):
        Capture.__init__(self, dev, lock)
        self.min_delay = min_delay
        self.last_time = time.time()

    def capture(self):
        self.delayed_capture()

    def delayed_capture(self):
        while time.time() - self.last_time < self.min_delay:
            pass
        image = self.dev.snapshot()
        if image is not None:
            self.finished.emit(image)
        self.last_time = time.time()


class ContinuousCapture(DelayedCapture):
    def __init__(self, dev, lock, min_delay = 0):
        DelayedCapture.__init__(self, dev, lock, min_delay)
        self._stop = False

    def capture(self):
        while not self._stop:
            self.delayed_capture()
        self._stop = False

    def stop(self):
        self._stop = True

