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

class Device:
    class Setting:
        class Base:
            class Camera:
                class GenICam:
                    class AcquisitionControl:
                        TriggerMode = "On"
                        ExposureAuto = 'Yes'
                        class ExposureTime:
                            value = 5e-6
                        TriggerSource = '0'
                        TriggerActivation = 'Rising'
                    class ImageFormatControl:
                        PixelFormat = "Mono8"
                        class WidthMax:
                            value = 3
                        class HeightMax:
                            value = 4
                        class Width:
                            value = 3
                        class Height:
                            value = 4
                        class OffsetX:
                            value= 0
                        class OffsetY:
                            value= 0
                    class AnalogControl:
                        GainAuto = 'no'
                        class Gain:
                            value=0.0
                        Gamma = 1.0
                        class GammaEnabled:
                            value = True
                        class BlackLevel:
                            value=1.
                class ImageRequestTimeout_ms:
                    value = 1000

    def snapshot(self):
        return np.random.rand(100,100)

class DeviceManager():
    def get_device(self, id):
        return Device()

dmg = DeviceManager()