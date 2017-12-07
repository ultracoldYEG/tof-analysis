import numpy as np
import time


def guass2D(x,y, A, sigx = 1000., sigy = 1000.):
    return A* 250. * np.exp(-(x-100.)**2 / sigx - (y-250.)**2 / sigy)

class setting(object):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)

    def __set__(self, obj, val):
        self.value = val

    def __getattr__(self, item):
        if item == 'value':
            return self.value


class TriggerMode(setting):
    pass
class ExposureAuto(setting):
    pass
class ExposureTime(setting):
    pass
class TriggerSource(setting):
    pass
class TriggerActivation(setting):
    pass
class PixelFormat(setting):
    pass
class WidthMax(setting):
    pass
class HeightMax(setting):
    pass
class Width(setting):
    pass
class Height(setting):
    pass
class OffsetX(setting):
    pass
class OffsetY(setting):
    pass
class GainAuto(setting):
    pass
class Gain(setting):
    pass
class Gamma(setting):
    pass
class GammaEnabled(setting):
    pass
class BlackLevel(setting):
    pass
class ImageRequestTimeout_ms(setting):
    pass

class Device(object):
    def __init__(self):
        self.Setting = Setting()
        self.image = None

    def snapshot(self):
        image_control = self.Setting.Base.Camera.GenICam.ImageFormatControl
        snap = np.zeros((image_control.Height.value, image_control.Width.value))
        rand1 = np.random.rand() * 1000.
        rand2 = np.random.rand() * 1000.
        for i in range(image_control.Height.value):
            for j in range(image_control.Width.value):
                snap[i,j] = int(250.0 - guass2D(float(i),float(j), 0.9, rand1, rand2) + 5 * np.random.rand())
        return snap

    def image_request(self):
        time.sleep(1)
        self.image = Image(self.snapshot())

    def get_image(self, timeout=2):
        init_time = time.time()
        while time.time() - init_time < timeout:
            img = self.image
            self.image = None
            return img
        raise ValueError('No image received')

class Image(object):
    def __init__(self, data):
        self.buffer = data

    def get_buffer(self):
        buffer = self.buffer
        self.buffer = None
        return buffer

class Setting(object):
    def __init__(self):
        self.Base = Base()

class Base(object):
    def __init__(self):
        self.Camera = Camera()

class Camera(object):
    def __init__(self):
        self.ImageRequestTimeout_ms = ImageRequestTimeout_ms(2000)
        self.GenICam = GenICam()

class GenICam(object):
    def __init__(self):
        self.AcquisitionControl = AcquisitionControl()
        self.ImageFormatControl = ImageFormatControl()
        self.AnalogControl = AnalogControl()

class AcquisitionControl:
    TriggerMode = TriggerMode("On")
    ExposureAuto = ExposureAuto('Yes')
    ExposureTime = ExposureTime(5e-6)
    TriggerSource = TriggerSource('0')
    TriggerActivation = TriggerActivation('Rising')


class ImageFormatControl:
    PixelFormat = PixelFormat("Mono8")
    WidthMax = WidthMax(500)
    HeightMax = HeightMax(200)
    Width = Width(500)
    Height = Height(200)
    OffsetX = OffsetX(0)
    OffsetY = OffsetY(0)

class AnalogControl:
    GainAuto = GainAuto('no')
    Gain = Gain(0.0)
    Gamma = Gamma(1.0)
    GammaEnabled = GammaEnabled(True)
    BlackLevel = BlackLevel(1.0)



class DeviceManager():
    def get_device(self, id):
        return Device()

dmg = DeviceManager()