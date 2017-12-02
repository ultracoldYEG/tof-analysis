# -*- coding: utf-8 -*-
"""
Created on Tue Jan 19 10:09:26 2016

@author: Lindsay
"""

# self.dev.Setting.Base.Camera.GenICam.AcquisitionControl.TriggerMode = "Off"
# self.dev.Setting.Base.Camera.GenICam.ImageFormatControl.PixelFormat = "Mono16"
# self.user_width.setMaximum(self.dev.Setting.Base.Camera.GenICam.ImageFormatControl.WidthMax.value)
# self.user_height.setMaximum(self.dev.Setting.Base.Camera.GenICam.ImageFormatControl.HeightMax.value)

# self.expose_time_3.setText(str(GenICam_handle.AcquisitionControl.ExposureTime.value))
# self.auto_expose_3.setText(str(GenICam_handle.AcquisitionControl.ExposureAuto))
# self.gain_3.setText(str(GenICam_handle.AnalogControl.Gain.value))
# self.auto_gain_3.setText(str(GenICam_handle.AnalogControl.GainAuto))
# self.gamma_level.setText(str(GenICam_handle.AnalogControl.Gamma))
# if not GenICam_handle.AnalogControl.GammaEnabled.value:
#     self.gamma_enable.setText("Off")
# else:
#     self.gamma_enable.setText("On")
# self.black_level_3.setText(str(GenICam_handle.AnalogControl.BlackLevel.value))
# self.pixel_format_3.setText(str(GenICam_handle.ImageFormatControl.PixelFormat))
#
# self.width.setText(str(GenICam_handle.ImageFormatControl.Width.value))
# self.height.setText(str(GenICam_handle.ImageFormatControl.Height.value))
# self.horz_offset.setText(str(GenICam_handle.ImageFormatControl.OffsetX))
# self.vert_offset.setText(str(GenICam_handle.ImageFormatControl.OffsetY))
#
# max_height = float(GenICam_handle.ImageFormatControl.HeightMax.value)
# max_width = float(GenICam_handle.ImageFormatControl.WidthMax.value)
#
# left_bound = (int(GenICam_handle.ImageFormatControl.OffsetX.value)) / max_width
# right_bound = (int(GenICam_handle.ImageFormatControl.OffsetX.value) + int(
#     GenICam_handle.ImageFormatControl.Width.value)) / max_width
# upper_bound = (max_height - int(GenICam_handle.ImageFormatControl.OffsetY.value)) / max_height
# lower_bound = (max_height - int(GenICam_handle.ImageFormatControl.OffsetY.value) - int(
#     GenICam_handle.ImageFormatControl.Height.value)) / max_height


# self.trigger_mode.setText(str(GenICam_handle.AcquisitionControl.TriggerMode))
# self.trigger_source.setText(str(GenICam_handle.AcquisitionControl.TriggerSource))
# self.trigger_activation.setText(str(GenICam_handle.AcquisitionControl.TriggerActivation))
# self.trigger_timeout.setText(str(self.dev.Setting.Base.Camera.ImageRequestTimeout_ms.value))

import numpy as np
import time


def guass2D(x,y, A):
    return A* 250. * np.exp(-(x-100.)**2 / 1000. - (y-250.)**2 / 1000.)

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
        snap = 255* np.random.rand(image_control.Height.value, image_control.Width.value)
        # rand = np.random.rand()
        # for i, val_i in enumerate(snap):
        #     for j, val_j in enumerate(val_i):
        #         snap[i,j] = int(255.0 - guass2D(float(i),float(j), 0.9) + np.random.rand())
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