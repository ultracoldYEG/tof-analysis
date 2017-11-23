# -*- coding: utf-8 -*-
"""
Created on Tue Jan 19 10:09:26 2016

@author: Lindsay
"""
# from PyQt4.uic import loadUiType
# from matplotlib.backends.backend_qt4agg import (
#     FigureCanvasQTAgg as FigureCanvas,
#     NavigationToolbar2QT as NavigationToolbar)
# from PyQt4 import QtGui, QtCore


from PyQt5.uic import loadUiType
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import matplotlib.pyplot as plt    
import matplotlib.gridspec as gridspec
# from lmfit import Model
import sys
import os
import numpy as np
from matplotlib.widgets import Cursor
import time
from datetime import date
# import mv
import mock_mv as mv
import threading
import Queue
import struct

ROOT_PATH = os.getcwd()

Ui_MainWindow, QMainWindow = loadUiType(os.path.join(ROOT_PATH, 'TOFanalysis.ui'))

Ui_CamSelect, QCamSelect = loadUiType(os.path.join(ROOT_PATH, 'cam_selector.ui'))


 
def funcGaussian(x,A,x0,sigma,y0):
# the independent variable must be sent first for the fit function
       return A*np.exp(-((x-x0)/sigma)**2/2)+y0

 
def triggered_snapshot(dev,timeout_value):
    dev.image_request()
    try:
        result = dev.get_image(timeout=(float(timeout_value)/1000.))
    except Exception as e:
        print e
        print "Did not recieve a trigger after "+str(timeout_value)+" milliseconds"
        dev.image_request_reset(0)
        return False
    else:
        print 'captured'
        img = result.get_buffer()
        del result
        return img
        
 
class CamWindow(QCamSelect, Ui_CamSelect):
    def __init__(self):
        super(CamWindow, self).__init__()
        self.setupUi(self)
        
        self.cameraCombo.addItems(['Top Cam', 'Side Cam', 'Andrei'])
        self.cameraSerialNums = ['14234117','14366837','15384643']
        self.openButton.clicked.connect(self.opened)
        self.cancelButton.clicked.connect(self.cancelled)
        
    def opened(self):
        global device_id
        device_id = self.cameraSerialNums[self.cameraCombo.currentIndex()]
        QtCore.QCoreApplication.instance().quit()
        
    def cancelled(self):
        sys.exit()

   
class Main(QMainWindow, Ui_MainWindow):
    def __init__(self, device, q):
        super(Main, self).__init__()
        self.setupUi(self)
        self.dev = device
        self.q = q
        
        # Setup figures
        self.fig1 = plt.figure()
        
        self.gs = gridspec.GridSpec(2,2, height_ratios=[3,1])
        
        self.a1=plt.subplot(self.gs[0,:])
        self.fig1.add_subplot(self.a1)
        self.cax1=plt.Axes(self.fig1, [.9,.31,.02,.63])
        self.fig1.add_axes(self.cax1)
        self.a1.imshow(np.random.rand(5,5), cmap = plt.cm.bone)    
        
        self.a2=plt.subplot(self.gs[1,0])
        self.fig1.add_axes(self.a2)
        self.a2.plot(np.random.rand(5))

        self.a3=plt.subplot(self.gs[1,1])
        self.fig1.add_axes(self.a3)
        self.a3.plot(np.random.rand(5))
        
        self.fig1.subplots_adjust(left=0.08, bottom=0.06, right=0.9, top=0.98, wspace=0.32, hspace=0.06)
        
        self.canvas1 = FigureCanvas(self.fig1)
        self.plotLayout.addWidget(self.canvas1)
        self.canvas1.draw()
        self.toolbar1 = NavigationToolbar(self.canvas1, self.image2Dplot, coordinates=True)
        self.plotLayout.addWidget(self.toolbar1)
        self.toolbar1.setFixedHeight(24)
        
        # add facility to draw ROI
        self.a1.callbacks.connect('xlim_changed', self.xchange) 
        self.a1.callbacks.connect('ylim_changed', self.ychange) 
        #self.canvas1.mpl_connect('button_press_event', self.xyzvals)
        #self.cursor1 = Cursor(self.a1,useblit=True,color='k')
        self.xcoordLE.setText('{:.3f}'.format(0))
        self.ycoordLE.setText('{:.3f}'.format(0))



        # Raw images
        self.fig4 = plt.Figure()
        self.a4=plt.Axes(self.fig4, [.1,.1,.8,.8])
        self.fig4.add_axes(self.a4)
        self.cax4=plt.Axes(self.fig4, [.9,.1,.02,.8])
        self.fig4.add_axes(self.cax4)
        self.a4.imshow(np.random.rand(5,5), cmap = plt.cm.bone)    
        self.canvas4 = FigureCanvas(self.fig4)
        self.RawLayout.addWidget(self.canvas4)
        self.canvas4.draw()
        self.fig4.tight_layout        
        self.toolbar4 = NavigationToolbar(self.canvas4, self.RawImages, coordinates=True)
        self.RawLayout.addWidget(self.toolbar4)
        self.toolbar1.setFixedHeight(24)   
        self.xcursor = 0
        self.ycursor = 0
        self.canvas4.mpl_connect('button_press_event', self.xyzvalsRaw)
        self.cursor4 = Cursor(self.a4,useblit=True,color='k')
        self.rawxCursorLE.setText('{:.3f}'.format(0))
        self.rawyCursorLE.setText('{:.3f}'.format(0))
        self.rawzCursorLE.setText('{:.3f}'.format(0))

        self.dev.Setting.Base.Camera.GenICam.AcquisitionControl.TriggerMode = "Off"
        self.dev.Setting.Base.Camera.GenICam.ImageFormatControl.PixelFormat = "Mono16"
        self.fig5 = plt.Figure()
        self.a5=plt.Axes(self.fig5, [.01,.01,.99,.99])
        self.fig5.add_axes(self.a5)
        self.a5.imshow(self.dev.snapshot(),cmap=plt.cm.bone)
        self.a5.axis("off")
        self.canvas5 = FigureCanvas(self.fig5)
        self.plotLayout_2.addWidget(self.canvas5)
        self.canvas5.draw()
        self.fig5.tight_layout
        
        self.fig6 = plt.Figure()
        self.fig6.set_facecolor((1,1,1))
        self.a6 = plt.Axes(self.fig6, [.01,.01,.99,.99],xlim=(-0.01,1.01),ylim=(-0.01,1.01))
        self.fig6.add_axes(self.a6)
        self.a6.plot([0,1,1,0,0],[1,1,0,0,1],color='black',lw=3)
        self.a6.axis("off")
        self.canvas6 = FigureCanvas(self.fig6)
        self.plotLayout_3.addWidget(self.canvas6)
        self.canvas6.draw()
        self.fig6.tight_layout

        #      
        # Set up buttons
        self.controlBrowse.clicked.connect(self.load_Ctrlpath)
        self.outputBrowse.clicked.connect(self.load_Outpath)
        self.NumDataBrowse.clicked.connect(self.load_NumDataFolder)
        self.loadDataButton.clicked.connect(self.load_image_button_func)
        self.updateFitButton.clicked.connect(self.update_fits)
        self.set_user_values.clicked.connect(self.set_cam_params)
        self.capture_button.clicked.connect(self.capture_new_image)
        self.capture_scroll_right.clicked.connect(self.increase_capture_scroll)
        self.capture_scroll_left.clicked.connect(self.decrease_capture_scroll)
        self.preset_param_button.clicked.connect(self.set_preset_params)
        self.view_preset_button.clicked.connect(self.view_preset_params)
        self.continuous_capture_cb.clicked.connect(self.update_continuous_capture)
        self.trigger_apply_button.clicked.connect(self.set_trigger_params)
        self.AutoUpdateImage.clicked.connect(self.update_auto_update)
        self.saveCurrentButton.clicked.connect(self.save_current_images)
        self.ROICanvas.setChecked(True)
        self.ROIDirect.setChecked(False)
        self.AutoUpdateImage.setChecked(False)
        self.dataSaveCheck.setChecked(True)
        self.getBkgd.clicked.connect(self.update_bkgd)
        self.bkgdValue.setValue(0)
        self.bkgdValue.setDecimals(4)
        self.bkgdValue.setMaximum(100000)
         
        # setup combo box
        self.FitTypeCombo.addItems(['Gaussian (full)','Gaussian (ROI)','Gaussian (ROI->slice)'])
        self.atomCombo.addItems(['87 Rb','39 K','40 K'])
        self.imageTypeCombo.addItems(['Absorption','Fluorescence'])        
        self.whichImageCombo.addItems(['Image 1', 'Image 2', 'Image 3', 'Processed'])        
        self.whichImageCombo.activated.connect(self.update_rawimage)
        self.cmapCombo.addItems(['coolwarm','gray','spectral','coolwarm_r','gray_r','spectral_r'])
        self.cmapRawCombo.addItems(['coolwarm','gray','spectral','coolwarm_r','gray_r','spectral_r'])
        self.cmapCombo.activated.connect(self.update_image)
        self.cmapRawCombo.activated.connect(self.update_rawimage)

        self.user_auto_expose_6.addItems(['Off','Once','Continuous'])
        self.user_auto_gain_6.addItems(['Off','Once','Continuous'])
        self.user_gamma_enable.addItems(['Off','On'])
        self.user_pixel_format_6.addItems(['Mono8','Mono16'])
        self.user_trigger_mode.addItems(["Off","On"])
        self.user_trigger_source.addItems(["Line0","Line2","Line3","Software"])
        self.user_trigger_activation.addItems(["RisingEdge","FallingEdge","AnyEdge","LevelLow","LevelHigh"])
        
        global presets_filepath
        presets_filepath = os.path.join(ROOT_PATH, 'CAMpresets.csv')
        f = open(presets_filepath,'r')
        preset_names = []
        for line in f:
            line=line.split(',')
            if line[0] == 'name':
                self.preset_combobox.addItems(line[1].rsplit())
        
        # setup spin boxes
        self.sliceWidth.setMinimum(2)
        self.sliceWidth.setMaximum(500)
        self.sliceWidth.setValue(20)
        self.pixSize.setValue(7.4)
        self.detuning.setValue(0)
        self.TOF.setValue(5)
        self.lamda.setValue(780.24)
        self.RawSpinMin.setValue(0)
        self.RawSpinMax.setValue(100)
        self.CLimSpinMin.setValue(0)
        self.CLimSpinMax.setValue(1)
        self.RawSpinMin.setKeyboardTracking(False)      
        self.RawSpinMax.setKeyboardTracking(False)      
        self.CLimSpinMin.setKeyboardTracking(False)      
        self.CLimSpinMax.setKeyboardTracking(False)      
        self.RawSpinMin.valueChanged.connect(self.update_rawimage)
        self.RawSpinMax.valueChanged.connect(self.update_rawimage)
        self.CLimSpinMin.valueChanged.connect(self.update_image)
        self.CLimSpinMax.valueChanged.connect(self.update_image)
        self.ROIx1.setKeyboardTracking(False)      
        self.ROIx2.setKeyboardTracking(False)      
        self.ROIy1.setKeyboardTracking(False)      
        self.ROIy2.setKeyboardTracking(False)      
        self.ROIx1.valueChanged.connect(self.update_ROI)
        self.ROIx2.valueChanged.connect(self.update_ROI)
        self.ROIy1.valueChanged.connect(self.update_ROI)
        self.ROIy2.valueChanged.connect(self.update_ROI)
        self.user_width.setMaximum(self.dev.Setting.Base.Camera.GenICam.ImageFormatControl.WidthMax.value)
        self.user_height.setMaximum(self.dev.Setting.Base.Camera.GenICam.ImageFormatControl.HeightMax.value)
        # initial ROI values
        self.defaultROI()
                   
        # Set for testing
        self.OutputFile.setText('Z:/Data/ImageData/bmp_test/AllData.txt')
        self.ControlFile.setText("Z:/PythonData")
        self.NumDataFolder.setText('Z:/Data/ImageData/')

        # set original data arrays to zero
        self.xvals=[]
        self.yvals=[]      
        self.xvals_haxis =[]
        self.yvals_haxis =[]      
        self.atoms = []
        self.img1 = []
        self.img2 = []
        self.img3 = []
        #       
        # and fit parameters
        self.Hfit_x0.setText(str(1.0))
        self.Hfit_A.setText(str(1.0))
        self.Hfit_sigx.setText(str(1.0))
        self.Hfit_z0.setText(str(1.0))
        self.Vfit_y0.setText(str(1.0))
        self.Vfit_A.setText(str(1.0))
        self.Vfit_sigy.setText(str(1.0))
        self.Vfit_z0.setText(str(1.0))

        # timer for auto update
        self.timer = QtCore.QTimer()
        self.timer.setInterval(3000) 
        self.timer.timeout.connect(self.auto_update_button_func)
        
        #timer for continuous capture mode
        self.timer2 = QtCore.QTimer() 
        self.timer2.setInterval(100)
        self.timer2.timeout.connect(self.continuous_capture)
    
    # Begin functions         
         
    
    def disable_continuous_modes(self):
        global enable_snapshot_thread
        orig_enable_snapshot_thread = enable_snapshot_thread
        orig_cont_capture = self.continuous_capture_cb.isChecked()
        
        enable_snapshot_thread = False
        self.continuous_capture_cb.setChecked(False)
        self.update_continuous_capture()
        
        time.sleep(0.2)
        
        return [orig_enable_snapshot_thread, orig_cont_capture]
        
    def reactivate_continuous_modes(self, orig_enable_snapshot_thread, orig_cont_capture):
        global enable_snapshot_thread
        enable_snapshot_thread = orig_enable_snapshot_thread
        self.continuous_capture_cb.setChecked(orig_cont_capture)
        self.update_continuous_capture()
    
    def update_param_disp(self):
        #this will update the "value" column of the image settings panel directly from the camera's control board
        GenICam_handle = self.dev.Setting.Base.Camera.GenICam

        self.expose_time_3.setText(str(GenICam_handle.AcquisitionControl.ExposureTime.value))
        self.auto_expose_3.setText(str(GenICam_handle.AcquisitionControl.ExposureAuto))
        self.gain_3.setText(str(GenICam_handle.AnalogControl.Gain.value))
        self.auto_gain_3.setText(str(GenICam_handle.AnalogControl.GainAuto))
        self.gamma_level.setText(str(GenICam_handle.AnalogControl.Gamma))
        if not GenICam_handle.AnalogControl.GammaEnabled.value:
            self.gamma_enable.setText("Off")
        else:
            self.gamma_enable.setText("On")
        self.black_level_3.setText(str(GenICam_handle.AnalogControl.BlackLevel.value))
        self.pixel_format_3.setText(str(GenICam_handle.ImageFormatControl.PixelFormat))
        
        self.width.setText(str(GenICam_handle.ImageFormatControl.Width.value))
        self.height.setText(str(GenICam_handle.ImageFormatControl.Height.value))
        self.horz_offset.setText(str(GenICam_handle.ImageFormatControl.OffsetX))
        self.vert_offset.setText(str(GenICam_handle.ImageFormatControl.OffsetY))
        
        max_height = float(GenICam_handle.ImageFormatControl.HeightMax.value)
        max_width = float(GenICam_handle.ImageFormatControl.WidthMax.value)
                
        left_bound = (int(GenICam_handle.ImageFormatControl.OffsetX.value))/max_width
        right_bound = (int(GenICam_handle.ImageFormatControl.OffsetX.value) + int(GenICam_handle.ImageFormatControl.Width.value))/max_width
        upper_bound = (max_height - int(GenICam_handle.ImageFormatControl.OffsetY.value))/max_height
        lower_bound = (max_height - int(GenICam_handle.ImageFormatControl.OffsetY.value) - int(GenICam_handle.ImageFormatControl.Height.value))/max_height
        
        self.a6.cla()
        self.a6.axis("off")
        self.a6.set_axis_bgcolor((1,1,1))
        self.a6.plot([0,1,1,0,0],[1,1,0,0,1],color='black',lw=3)
        self.a6.plot([left_bound,right_bound,right_bound,left_bound,left_bound],
                     [upper_bound,upper_bound,lower_bound,lower_bound,upper_bound],color='red',lw=1)
        self.a6.plot([left_bound],[upper_bound],marker='o',markersize=5,color='red')
        self.a6.set_xlim((-0.01,1.01))
        self.a6.set_ylim((-0.01,1.01))
        self.canvas6.draw()

    def update_trigger_disp(self):
        #similar to update_param_disp, it will update the value column of the trigger panel
        GenICam_handle = self.dev.Setting.Base.Camera.GenICam
        
        self.trigger_mode.setText(str(GenICam_handle.AcquisitionControl.TriggerMode))
        self.trigger_source.setText(str(GenICam_handle.AcquisitionControl.TriggerSource))
        self.trigger_activation.setText(str(GenICam_handle.AcquisitionControl.TriggerActivation))
        self.trigger_timeout.setText(str(self.dev.Setting.Base.Camera.ImageRequestTimeout_ms.value))
        
    def set_cam_params(self):
        #this will apply the imaging settings in the "set to" column to the camera
        [orig_snap, orig_cont] = self.disable_continuous_modes()
        
        try:
            GenICam_handle = self.dev.Setting.Base.Camera.GenICam
            
            GenICam_handle.AcquisitionControl.ExposureAuto = str(self.user_auto_expose_6.currentText())
            if self.user_auto_expose_6.currentText() == "Off":
                GenICam_handle.AcquisitionControl.ExposureTime = self.user_expose_time_3.value()
    
            GenICam_handle.AnalogControl.GainAuto = str(self.user_auto_gain_6.currentText())
            if self.user_auto_gain_6.currentText() == "Off":
                GenICam_handle.AnalogControl.Gain = self.user_gain_3.value()
    
            if self.user_gamma_enable.currentText() == 'On':
                GenICam_handle.AnalogControl.GammaEnabled = 1
                GenICam_handle.AnalogControl.Gamma = self.user_gamma_level.value()
            else:
                GenICam_handle.AnalogControl.GammaEnabled = 0
            GenICam_handle.AnalogControl.BlackLevel = self.user_black_level_3.value()
    
            if self.user_pixel_format_6.currentText() == "Mono16":
                GenICam_handle.ImageFormatControl.PixelFormat = "Mono16"
            else:
                GenICam_handle.ImageFormatControl.PixelFormat = "Mono8"
    
            #the offsets need to be initialized to properly set the width and height to prevent it from (potentially) momentarily 
            #setting the active area outside of the maximum limits
            
            GenICam_handle.ImageFormatControl.OffsetX = 0
            GenICam_handle.ImageFormatControl.OffsetY = 0
    
            GenICam_handle.ImageFormatControl.Width = self.user_width.value()
            GenICam_handle.ImageFormatControl.Height = self.user_height.value()
            
            max_height = float(GenICam_handle.ImageFormatControl.HeightMax.value)
            max_width = float(GenICam_handle.ImageFormatControl.WidthMax.value)
            
            GenICam_handle.ImageFormatControl.OffsetX = self.user_horz_offset.value()*(max_width-self.user_width.value())/100.
            GenICam_handle.ImageFormatControl.OffsetY = self.user_vert_offset.value()*(max_height-self.user_height.value())/100.
            
        except Exception as e:
            print e
            
        self.reactivate_continuous_modes(orig_snap, orig_cont)
        self.update_param_disp()
            
    def set_trigger_params(self):
        #this will apply the trigger settings in the "set to" column to the cameras 
        [orig_snap, orig_cont] = self.disable_continuous_modes()

        try:
            GenICam_handle = self.dev.Setting.Base.Camera.GenICam
            GenICam_handle.AcquisitionControl.TriggerMode = str(self.user_trigger_mode.currentText())
            GenICam_handle.AcquisitionControl.TriggerSource = str(self.user_trigger_source.currentText())
            GenICam_handle.AcquisitionControl.TriggerActivation = str(self.user_trigger_activation.currentText())
            self.dev.Setting.Base.Camera.ImageRequestTimeout_ms.value = float(self.user_trigger_timeout.value())
            
        except Exception as e:
            print e
            
        self.update_trigger_disp()
        self.reactivate_continuous_modes(orig_snap, orig_cont)
        
    def read_preset_file(self):
        #this function parses the preset csv file and finds the name that matches the value in the "preset" combo box.
        global presets_filepath
        
        f = open(presets_filepath,'r')
        preset_name = self.preset_combobox.currentText()
        found_name = False
        params = []
        
        for line in f:
            line=line.split(',')
            if found_name:
                if line[0] == 'name':
                    break
                if line[1].rstrip():
                    params.append(line[1].rstrip())
                continue
            
            if line[1].rstrip() != preset_name:
                continue
            else:
                found_name = True
        f.close()
        return params
        
    def view_preset_params(self):
        #this function will place the preset values into the "set to" column without actually applying them to the camera
        params=self.read_preset_file()
        [expose_time,auto_expose,gain,auto_gain,gamma,gamma_enable,black_level,pixel_format,
        width,height,offsetx,offsety,decimate,trig_mode,trig_source,trig_act,trig_timeout]=params
        
        self.user_expose_time_3.setValue(float(expose_time))
        self.user_gain_3.setValue(float(gain))
        self.user_gamma_level.setValue(float(gamma))
        self.user_black_level_3.setValue(float(black_level))
        self.user_horz_offset.setValue(int(offsetx))
        self.user_vert_offset.setValue(int(offsety))
        
        self.user_width.setValue(int(width))
        self.user_height.setValue(int(height))
        
        self.user_auto_expose_6.setCurrentIndex(self.user_auto_expose_6.findText(auto_expose,QtCore.Qt.MatchFixedString))
        self.user_auto_gain_6.setCurrentIndex(self.user_auto_gain_6.findText(auto_gain,QtCore.Qt.MatchFixedString))
        self.user_gamma_enable.setCurrentIndex(self.user_gamma_enable.findText(gamma_enable,QtCore.Qt.MatchFixedString))
        self.user_pixel_format_6.setCurrentIndex(self.user_pixel_format_6.findText(pixel_format,QtCore.Qt.MatchFixedString))
        
        self.user_trigger_mode.setCurrentIndex(self.user_trigger_mode.findText(trig_mode,QtCore.Qt.MatchFixedString))
        self.user_trigger_source.setCurrentIndex(self.user_trigger_source.findText(trig_source,QtCore.Qt.MatchFixedString))
        self.user_trigger_activation.setCurrentIndex(self.user_trigger_activation.findText(trig_act,QtCore.Qt.MatchFixedString))
        self.user_trigger_timeout.setValue(int(trig_timeout))
        
    def set_preset_params(self):
        #this will set the values in the preset to the camera using previous functions
        self.view_preset_params()
        self.set_cam_params()
        self.set_trigger_params()
        
    def redraw_cam_plot(self,image):
        #this will simply redraw the capture plot given an image
        self.a5.cla()
        self.a5.imshow(image,cmap = plt.cm.bone, interpolation = 'none')
        self.a5.axis("off")
        self.canvas5.draw()
        self.capture_groupbox.setTitle(str(np.shape(image)[1])+" x "+str(np.shape(image)[0]))

    def capture_new_image(self):
        #this will capture a specified number of images with or without a trigger
        global captures
        global enable_snapshot_thread
        if self.continuous_capture_cb.isChecked() or enable_snapshot_thread:
            print 'Cannot capture image while in continuous capture mode'
            return
        captures = []
        time_delay = self.min_time_delay.value()/1000.
        init_time = time.time()
        if str(self.dev.Setting.Base.Camera.GenICam.AcquisitionControl.TriggerMode) == 'On':
            #this is if a trigger is enabled
            for i in range(self.capture_num.value()):
                last_snapshot = triggered_snapshot(self.dev,self.dev.Setting.Base.Camera.ImageRequestTimeout_ms.value)
                if last_snapshot:
                    captures.append(last_snapshot)
                    print (time.time()-init_time)*1000.
                    
                else:
                    print 'Failed to capture after '+str(i)+' images'
                    break
        else:
            #without a trigger it will use the "min time between" to time the capturing of images
            for i in range(self.capture_num.value()):
                while time.time() - init_time < time_delay:
                    continue
                print (time.time()-init_time)*1000.
                init_time= time.time()
                captures.append(self.dev.snapshot())
        self.redraw_cam_plot(captures[0])
        self.update_param_disp()
        self.update_trigger_disp()
        self.capture_num_info.setText('1/'+str(self.capture_num.value()))
        
    def increase_capture_scroll(self):
        #used to scroll left or right if multiple images are collected by a multishot capture
        global captures
        if self.continuous_capture_cb.isChecked():
            print 'Cannot scroll while in continuous capture mode'
            return
        current_index, current_capture_num = self.capture_num_info.text().split('/')
        self.redraw_cam_plot(captures[int(current_index)%int(current_capture_num)])
        self.capture_num_info.setText(str((int(current_index)%int(current_capture_num))+1)+'/'+str(current_capture_num))
        
    def decrease_capture_scroll(self):
        #used to scroll left or right if multiple images are collected by a multishot capture
        global captures
        if self.continuous_capture_cb.isChecked():
            print 'Cannot scroll while in continuous capture mode'
            return
        current_index, current_capture_num = self.capture_num_info.text().split('/')
        self.redraw_cam_plot(captures[(int(current_index)-2)%int(current_capture_num)])
        self.capture_num_info.setText(str((int(current_index)-2)%int(current_capture_num)+1)+'/'+str(current_capture_num))

    def update_continuous_capture(self):
        global enable_snapshot_thread
        if self.continuous_capture_cb.isChecked():
            #self.dev.Setting.Base.Camera.GenICam.AcquisitionControl.TriggerMode = "Off"
            if enable_snapshot_thread:
                print 'Cannot enter continuous capture while already collecting images'
                self.timer2.stop()
                self.continuous_capture_cb.setCheckState(False)
                return
            self.timer2.start()
        else:
            self.timer2.stop()

    def continuous_capture(self):
        a=triggered_snapshot(self.dev,self.dev.Setting.Base.Camera.ImageRequestTimeout_ms.value)
        down_sample_factor = self.user_down_sample.value()
        max_fps = self.user_max_fps.value()
        
        self.timer2.setInterval(1000.0/max_fps)
        self.redraw_cam_plot(a[::down_sample_factor,::down_sample_factor])
        time.sleep(0.01)
        
    def update_auto_update(self):
        global enable_snapshot_thread
        if self.AutoUpdateImage.isChecked():
            enable_snapshot_thread = True
            self.timer.start()
        else:
            self.timer.stop()
            enable_snapshot_thread = False
            
    def grab_3_triggered_images(self):
        img_list = []
        status = False

        queue_lock.acquire()
        if self.q.full():
            for i in range(self.q.qsize()):
                img_list.append(self.q.get())
            queue_lock.release()
            self.img1 = np.array(img_list[0])
            self.img2 = np.array(img_list[1])
            self.img3 = np.array(img_list[2])
            status = True
        else:
            queue_lock.release()
            print 'queue did not contain 3 images to get'

        return status

    def single_image_load(self):
        temp_imgs = []
        for i in range(3):
            image = triggered_snapshot(dev,dev.Setting.Base.Camera.ImageRequestTimeout_ms.value)
            
            if not image:
                print 'failed to acquire an image'
                return False
                
            else:    
                temp_imgs.append(image)
                
        self.img1 = np.array(temp_imgs[0])
        self.img2 = np.array(temp_imgs[1])
        self.img3 = np.array(temp_imgs[2])
        return True

    def xyzvals(self,event):
     # function to call if the autoupdate is on, and the polling timeout is reached
        self.xcursor=int(event.xdata)
        self.ycursor=int(event.ydata)
        self.xcoordLE.setText('{:.3f}'.format(self.xcursor))
        self.ycoordLE.setText('{:.3f}'.format(self.ycursor))
        self.zcoordLE.setText('{:.3f}'.format(self.atoms[self.ycursor,self.xcursor]))
        
        self.lx.set_ydata(event.ydata)       
        self.ly.set_xdata(event.xdata)
        self.lxslice.set_xdata(event.xdata)       
        self.lyslice.set_xdata(event.ydata)
        self.canvas1.draw() 
      
    # *********************************************************

    def xyzvalsRaw(self,event):
     # function to call if the autoupdate is on, and the polling timeout is reached
        self.xcursorRaw=int(event.xdata)
        self.ycursorRaw=int(event.ydata)
        self.rawxCursorLE.setText('{:.3f}'.format(self.xcursorRaw))
        self.rawyCursorLE.setText('{:.3f}'.format(self.ycursorRaw))
        
        if (self.whichImageCombo.currentText() == 'Image 2'):
            data = self.img2
        elif (self.whichImageCombo.currentText() == 'Image 3'):
            data = self.img3
        elif (self.whichImageCombo.currentText() == 'Processed'):
            data = self.atoms
        else:
            data = self.img1

        self.rawzCursorLE.setText('{:.3f}'.format(data[self.ycursorRaw,self.xcursorRaw]))
        
        self.lxRaw.set_ydata(event.ydata)       
        self.lyRaw.set_xdata(event.xdata)
        self.canvas4.draw()    
    # *********************************************************  

    
    def update_fits(self):
        # a routine to gather data from various files and compile it nicely 
        self.update_slices()   
        self.update_xfit()
        self.update_yfit()
        self.calcAtoms()
    

    
    def update_data(self, isContinuous):
        # a routine to gather data from already-divided files and image files and compile it nicely 
    #        self.atoms = self.getAtomsData()
    #        r,c = np.shape(self.atoms)
    #        # check for nans, make these points zero
    #        self.atoms = np.nan_to_num(self.atoms)      
        if isContinuous:
            if not self.grab_3_triggered_images(): #calling this function will try to update img1 img2 and img3
                return False
        else:
            if not self.single_image_load():
                return False
                
        self.img1_float = self.img1.astype(float)
        self.img2_float = self.img2.astype(float)
        self.img3_float = self.img3.astype(float)
        
        # analyse images depending on type
        if (self.imageTypeCombo.currentText() == 'Absorption'):
            # analyze image using Beer's law. Check for divide by zero, ln(<0)
            denom = (self.img2_float-self.img3_float)
            denom[denom==0] = 1
            
            ratio = (self.img1_float-self.img3_float) / denom      
            ratio[ratio<=0] = 0.01

            self.atoms = -np.log(ratio)
            
        elif (self.imageTypeCombo.currentText() == 'Fluorescence'):    
            # just subtract background.  Ignore Img3 if it exists
            self.atoms = self.img1-self.img2
            
        else:
            self.atoms = self.img1
            
        return True
      
     

    
    def update_slices(self)      :  
    # Perform analysis based on the choice between: (['Gaussian (full)','Gaussian (ROI)','Gaussian (ROI->slice)'])        
        if (str(self.FitTypeCombo.currentText()) == 'Gaussian (full)'): 
        
            r,c = np.shape(self.atoms)
            self.xvals = np.sum(self.atoms,0)/r
            self.xvals_haxis = np.arange(0,c,1)
            self.yvals = np.sum(self.atoms,1)/c
            self.yvals_haxis = np.arange(0,r,1)
    
        else: 
            # find the centre of each from statistics
            x1 = int(self.ROIx1.value()) 
            x2 = int(self.ROIx2.value())
            y1 = int(self.ROIy1.value()) 
            y2 = int(self.ROIy2.value())
            r = y2 - y1 + 1
            c = x2 - x1 + 1
            '''
            self.xvals = np.sum(self.atoms[y1:y2+1,x1:x2+1],0)/r
            self.xvals_haxis = np.arange(x1,x2,1)
            self.yvals = np.sum(self.atoms[y1:y2+1,x1:x2+1],1)/c
            self.yvals_haxis = np.arange(y1,y2,1)
            '''
            self.xvals = np.sum(self.atoms[y1:y2,x1:x2],0)/r
            self.xvals_haxis = np.arange(x1,x2,1)
            self.yvals = np.sum(self.atoms[y1:y2,x1:x2],1)/c
            self.yvals_haxis = np.arange(y1,y2,1)
            
            if (str(self.FitTypeCombo.currentText()) == 'Gaussian (ROI->slice)'): 
                centrex,a,b = self.statAnalysis(self.xvals_haxis,self.xvals)
                centrey,a,b = self.statAnalysis(self.yvals_haxis,self.yvals)
                width = int(self.sliceWidth.value()/2)
                self.xvals = np.sum(self.atoms[int(centrey)-width:int(centrey)+width,x1:x2],0)/2/width
                self.yvals = np.sum(self.atoms[y1:y2,int(centrex)-width:int(centrex)+width],1)/2/width
               
     
             

    
    def getAtomsData(self):
    # get the values that we select to plot from various files, and create a data file with them        
        filename = self.ImageFile.text()
        atoms = np.loadtxt(filename,delimiter=',')
        return atoms
    # *** end gegetAtomsDatatCtrl **************************************
        
    def initialize_fig_1(self):
        self.fig1.clf()
        
        self.fig1.add_subplot(self.a1)
        self.fig1.add_axes(self.cax1)    
        self.fig1.add_axes(self.a2)
        self.fig1.add_axes(self.a3)
        

    

    def initialize_fig_4(self):
        self.fig4.clf()
        
        self.fig4.add_axes(self.a4)
        self.fig4.add_axes(self.cax4)

    
    def update_image(self):
        # a routine to update the figure with new data
        # get plot settings before update
        cmesh = self.a1.imshow(self.atoms,cmap=str(self.cmapCombo.currentText()))

        if (self.CLimAuto.isChecked()):
            cmesh.set_clim(vmin=np.min(np.min(self.atoms)),vmax = np.max(np.max(self.atoms)))
        else:
            cmesh.set_clim(vmin=self.CLimSpinMin.value(),vmax = self.CLimSpinMax.value())
        self.a1.set_xlim([self.ROIx1.value(),self.ROIx2.value()])
        self.a1.set_ylim([self.ROIy1.value(),self.ROIy2.value()])

        self.lx = self.a1.axhline(y =  self.ycursor,color = 'black') # the horiz line
        self.ly = self.a1.axvline(x =  self.xcursor,color = 'black')  # the horiz line
         
        self.a1.set_aspect(1)
        self.fig1.colorbar(cmesh,cax=self.cax1)
        
        # add facility to draw ROI after axis cleared
        self.a1.callbacks.connect('xlim_changed', self.xchange) 
        self.a1.callbacks.connect('ylim_changed', self.ychange) 
        
        self.canvas1.draw()

    

    
    def update_rawimage(self):
        # a routine to update the figure with new data
        # get plot settings before update
        if (self.whichImageCombo.currentText() == 'Image 2'):
            data = self.img2
        elif (self.whichImageCombo.currentText() == 'Image 3'):
            data = self.img3
        elif (self.whichImageCombo.currentText() == 'Processed'):
            data = self.atoms
        else:
            data = self.img1
            
        cmesh = self.a4.imshow(data,cmap=str(self.cmapRawCombo.currentText()))
        if (self.RawCLimAuto.isChecked()):
            cmesh.set_clim(vmin=np.min(np.min(data)),vmax = np.max(np.max(data)))
        else:
             cmesh.set_clim(vmin=self.RawSpinMin.value(),vmax = self.RawSpinMax.value())
        self.a4.set_xlim([self.xvals_haxis[0],self.xvals_haxis[-1]])
        self.a4.set_ylim([self.yvals_haxis[0],self.yvals_haxis[-1]])
    
        self.a4.set_aspect(1)
        self.fig4.colorbar(cmesh,cax=self.cax4)
        self.canvas4.draw()             
    

    
    def update_xplot(self):
        # a routine to update the figure with new data
        # get plot settings before update
 
        self.a2.hold(True) 
        self.a2.plot(self.xvals_haxis,self.xvals,'-',lw=1,color='deepskyblue')
        self.a2.set_xlim([self.ROIx1.value(),self.ROIx2.value()])
             
        fitx = np.linspace(self.xvals_haxis[0],self.xvals_haxis[-1])
        fity = np.ones_like(fitx)
        fity = funcGaussian(fitx,float(self.Hfit_A.text()),float(self.Hfit_x0.text()),float(self.Hfit_sigx.text()),float(self.Hfit_z0.text()))
        self.lxslice = self.a2.axvline(x =  self.xcursor,color = 'black') # the horiz line
           
        self.a2.plot(fitx,fity,'k--',lw=1)  
        self.a2.hold(False)        
                     
    

    
    def update_yplot(self):
        # a routine to update the figure with new data
        # get plot settings before update
         
        self.a3.hold(True)        
        self.a3.plot(self.yvals_haxis,self.yvals,'g-',lw=1)
        self.a3.set_xlim([self.ROIy1.value(),self.ROIy2.value()])
                 
        fitx = np.linspace(self.yvals_haxis[0],self.yvals_haxis[-1])
        fity = np.ones_like(fitx)
        fity = funcGaussian(fitx,float(self.Vfit_A.text()),float(self.Vfit_y0.text()),float(self.Vfit_sigy.text()),float(self.Vfit_z0.text()))
        self.lyslice = self.a3.axvline(x =  self.ycursor,color = 'black') # the horiz line
           
        self.a3.plot(fitx,fity,'k--',lw=1)
        self.a3.hold(False)        
             
    

    
    def update_xfit(self):
        xv = [float(i) for i in self.xvals_haxis]          
        yv = [float(i) for i in self.xvals]
    #if (str(self.FitTypeCompbo.currentText()) == 'Gaussian'): #x,A,x0,sigma,y0
        gmod = Model(funcGaussian)
        
        # make some guesses for the fits
        centre, sig, A= self.statAnalysis(xv,yv)
        self.Hfit_x0.setText('{:.3f}'.format(centre))
        self.Hfit_sigx.setText('{:.3f}'.format(sig))
        self.Hfit_A.setText('{:.3f}'.format(A))
       
        params = gmod.make_params(A=float(self.Hfit_A.text()), x0=float(self.Hfit_x0.text()),sigma=float(self.Hfit_sigx.text()),y0=float(self.Hfit_z0.text()))
        gmod.set_param_hint('A', value =float(self.Hfit_A.text()), max = 10000, min = 0.001)
        gmod.set_param_hint('x0',value =float(self.Hfit_x0.text()), min = 100, max = 900)
        gmod.set_param_hint('sigma',value =float(self.Hfit_sigx.text()), min = 1, max = 1000)
        gmod.set_param_hint('y0', value =float(self.Hfit_z0.text()), min = -1000, max = 1000)
        
        if self.Hfit_A_ck.isChecked(): 
            params['A'].vary = False
        else:
            params['A'].vary = True
        
        if self.Hfit_x0_ck.isChecked():
            params['x0'].vary = False
        else:  
            params['x0'].vary = True
           
        if self.Hfit_sigx_ck.isChecked(): 
            params['sigma'].vary = False
        else:
            params['sigma'].vary = True
        
        if self.Hfit_z0_ck.isChecked():
            params['y0'].vary = False
        else:  
            params['y0'].vary = True
               
        FitResults = gmod.fit(yv,x=xv,params=params)
        
        self.Hfit_A.setText('{:.3f}'.format(FitResults.best_values.get('A')))
        self.Hfit_x0.setText('{:.3f}'.format(FitResults.best_values.get('x0')))
        self.Hfit_sigx.setText('{:.3f}'.format(FitResults.best_values.get('sigma')))
        self.Hfit_z0.setText('{:.3f}'.format(FitResults.best_values.get('y0')))     
        
        #self.update_xplot()
        
        self.fitdisplay.setPlainText(FitResults.fit_report())                        
     
                
     
    def update_yfit(self):
        xv = [float(i) for i in self.yvals_haxis]          
        yv = [float(i) for i in self.yvals] 
        
    #if (str(self.FitTypeCompbo.currentText()) == 'Gaussian'): #x,A,x0,sigma,y0
        gmod = Model(funcGaussian)
       
        centre, sig, A = self.statAnalysis(xv,yv)
        self.Vfit_y0.setText('{:.3f}'.format(centre))
        self.Vfit_sigy.setText('{:.3f}'.format(sig))
        self.Vfit_A.setText('{:.3f}'.format(A))
        
        params = gmod.make_params(A=float(self.Vfit_A.text()), x0=float(self.Vfit_y0.text()),sigma=float(self.Vfit_sigy.text()),y0=float(self.Vfit_z0.text()))
        gmod.set_param_hint('A', value =float(self.Vfit_A.text()), max = 10000, min = 0.001)
        gmod.set_param_hint('x0',value =float(self.Vfit_y0.text()), min = 100, max = 900)
        gmod.set_param_hint('sigma',value =float(self.Vfit_sigy.text()), min = 1, max = 1000)
        gmod.set_param_hint('y0', value =float(self.Vfit_z0.text()), min = -1000, max = 1000)
      
        if self.Vfit_A_ck.isChecked(): 
            params['A'].vary = False
        else:
            params['A'].vary = True
        
        if self.Vfit_y0_ck.isChecked():
            params['x0'].vary = False
        else:  
            params['x0'].vary = True
           
        if self.Vfit_sigy_ck.isChecked(): 
            params['sigma'].vary = False
        else:
            params['sigma'].vary = True
        
        if self.Vfit_z0_ck.isChecked():
            params['y0'].vary = False
        else:  
            params['y0'].vary = True
      
        FitResults = gmod.fit(yv,x=xv,params=params)
        self.Vfit_A.setText('{:.3f}'.format(FitResults.best_values.get('A')))
        self.Vfit_y0.setText('{:.3f}'.format(FitResults.best_values.get('x0')))
        self.Vfit_sigy.setText('{:.3f}'.format(FitResults.best_values.get('sigma')))
        self.Vfit_z0.setText('{:.3f}'.format(FitResults.best_values.get('y0')))     
           
        #self.update_yplot()
        
        self.fitdisplay.appendPlainText(FitResults.fit_report())                        
     

    
    def statAnalysis(self,xv,yv):
        # make some guesses for the fits
        centre = np.sum(np.power(yv,2)*xv)/np.sum(np.power(yv,2))
        var = np.sum(np.power(yv,2)*np.power(xv,2))/np.sum(np.power(yv,2))
        sig = np.sqrt(var-centre**2)
        A = np.max(yv)
        return centre, sig, A     
     
       
    
    def calcAtoms(self):
    # calculate some physical properties
        self.widthxum = self.pixSize.value()*float(self.Hfit_sigx.text())
        self.widthyum = self.pixSize.value()*float(self.Vfit_sigy.text())
        self.ODmax = np.sqrt(float(self.Vfit_A.text())*float(self.Hfit_A.text())) #geometric average
        
        # scattering cross-section
        wavelength = self.lamda.value()*1e-9
        det = self.detuning.value() * 10**6
        gamma = 6e6; # MHz
        mass = 87*1.67e-27 # kg
        kB = 1.38e-23 # J/K
        scatt0 = 3*wavelength**2/2/np.pi
        scatt = scatt0/(1+(2*det/gamma)**2)        
        self.atomNumFit = 2*np.pi*self.ODmax*self.widthxum*self.widthyum*1e-12/scatt
        self.Tx = self.widthxum*self.widthxum*mass/kB/(self.TOF.value()**2)
        self.Ty = self.widthyum*self.widthyum*mass/kB/(self.TOF.value()**2)
        self.T  = self.widthxum*self.widthyum*mass/kB/(self.TOF.value()**2)
      
        # pixel sum atom number  
        # only count inside the ROI
        imgROIx1=int(self.a1.get_xlim()[0])
        imgROIx2=int(self.a1.get_xlim()[1])
        imgROIy1=int(self.a1.get_ylim()[0])
        imgROIy2=int(self.a1.get_ylim()[1])
        self.picInROI = self.atoms[imgROIx1:imgROIx2,imgROIy1:imgROIy2]
        
        # subtract background from fit
        if self.subBkgd.isChecked():
            self.atomSum = np.sum(self.picInROI) - self.bkgdAvg*self.picInROI.size
        else:
            self.atomSum = np.sum(self.picInROI)
    #        bkgd = 0.5*(float(self.Vfit_z0.text()) + float(self.Hfit_z0.text())) # average
    ##             
    ##        self.atomNumSum = (self.pixSize.value()*1e-6)**2/scatt*(np.sum(np.sum(self.atoms))-bkgd*numpix)
        self.atomNumSum = (self.pixSize.value()*1e-6)**2/scatt*(self.atomSum)

        self.AtomNumSumLE.setText('{:.3e}'.format(self.atomNumSum))
        self.AtomNumFitLE.setText('{:.3e}'.format(self.atomNumFit))
        self.TxLE.setText('{:.3f}'.format(self.Tx))
        self.TyLE.setText('{:.3f}'.format(self.Ty))
        self.TLE.setText('{:.3f}'.format(self.T))
        self.xwidthumLE.setText('{:.3f}'.format(self.widthxum))
        self.ywidthumLE.setText('{:.3f}'.format(self.widthyum))     
    # ***end statAnalysis **************************************

    def load_image_button_func(self):
        if self.AutoUpdateImage.isChecked():
            print 'cannot load data while autoupdating'
            return
        self.load_data(False)
        
    def auto_update_button_func(self):
        self.load_data(True)
       
    
    def load_data(self, isContinuous): 
        
        time1 = time.time()
        QtGui.QApplication.processEvents()
        if not self.update_data(isContinuous):
            return 
            
        time2 = time.time()
        self.getCtrldata()
        QtGui.QApplication.processEvents()
        
        time3 = time.time()
        self.update_slices()
        QtGui.QApplication.processEvents()
        
        time4 = time.time()
        self.update_xfit()
        QtGui.QApplication.processEvents()
        
        time5 = time.time()
        self.update_yfit()
        QtGui.QApplication.processEvents()
        
        self.initialize_fig_1()
        self.initialize_fig_4()
        
        time6 = time.time()
        self.update_xplot()
        QtGui.QApplication.processEvents()
        
        self.update_yplot()
        time7 = time.time()
        self.update_image()
        QtGui.QApplication.processEvents()
        
        time8 = time.time()
        self.update_rawimage()
        QtGui.QApplication.processEvents()
        
        time9 = time.time()
        self.calcAtoms()
        QtGui.QApplication.processEvents()
        
        time10 = time.time()
        self.writeDataFile()
        QtGui.QApplication.processEvents()
        
        time11 = time.time()
        '''
        print ''
        print 'xplot+yplot', str(time7 - time6) 
        print 'image      ', str(time8 - time7) 
        print 'raw image  ', str(time9 - time8) 
        print 'total      ', time11 - time1
        '''
        #self.write_imgs_bmp(self.img1,"Z:/Data/ImageData/bmp_test/TOF_test.bmp")
        
    

    
    def load_Ctrlpath(self): 
        self.Ctrlpath = QtGui.QFileDialog.getOpenFileName(self,'Select Controls File (PythonData)')
        self.ControlFile.setText(self.Ctrlpath)
    

    
    def load_Outpath(self): 
        self.Outpath = QtGui.QFileDialog.getOpenFileName(self,'Select Output File (Physical Data)')
        self.OutputFile.setText(self.Outpath)
    

      
    def load_NumDataFolder(self): 
        self.NumDataFolderName = QtGui.QFileDialog.getExistingDirectory(self,'Select Directory/Folder (For numbered Control and Physical Data)')
        self.NumDataFolder.setText(self.NumDataFolderName)
    

             
    # ***** end onclick ******************************* 
    def xchange(self,ax):
    # adjust ROI when using toolbar in image 1
       if self.ROIDirect.isChecked(): return # don't reset numbers in "direct entry" case
       self.ROIx1.setValue(self.a1.get_xlim()[0])
       self.ROIx2.setValue(self.a1.get_xlim()[1])
       
       # update 1D figures
       self.a2.set_xlim([self.ROIx1.value(),self.ROIx2.value()])
       self.canvas1.draw()
    # ***** end onclick ******************************* 

    # ************************************ 
    def ychange(self,ax):
       # adjust ROI when using toolbar in image 1
        if self.ROIDirect.isChecked(): return # don't reset numbers in "direct entry" case
        self.ROIy1.setValue(self.a1.get_ylim()[0])
        self.ROIy2.setValue(self.a1.get_ylim()[1])
        
        # update 1D figures
        self.a3.set_xlim([self.ROIy1.value(),self.ROIy2.value()])
        self.canvas1.draw()    
    # ***** end ychange ******************************* 

    # ************************************ 
    def update_ROI(self,):
    # adjust ROI when box values are changed
       # check that the "1" values are smaller than the "2" values
       if self.ROICanvas.isChecked(): return # don't reset numbers in "direct entry" case
       
       if (self.ROIx1.value() > self.ROIx2.value()):
            temp = self.ROIx1.value()
            self.ROIx1.setValue(self.ROIx2.value())
            self.ROIx2.setValue(temp)
       if (self.ROIy1.value() > self.ROIy2.value()):
            temp = self.ROIy1.value()
            self.ROIy1.setValue(self.ROIy2.value())
            self.ROIy2.setValue(temp)
      
       # update main figure
       self.a1.set_xlim([self.ROIx1.value(),self.ROIx2.value()])
       self.a1.set_ylim([self.ROIy1.value(),self.ROIy2.value()])
      
       # update 1D figures
       self.a2.set_xlim([self.ROIx1.value(),self.ROIx2.value()])
       self.a3.set_xlim([self.ROIy1.value(),self.ROIy2.value()])
       self.canvas1.draw()
    # ***** end update_ROI ******************************* 

    # ************************************ 
    def defaultROI(self):
    # initial ROI values
        GenICam_handle = self.dev.Setting.Base.Camera.GenICam
        
        right_bound = int(GenICam_handle.ImageFormatControl.Width.value)
        upper_bound = int(GenICam_handle.ImageFormatControl.Height.value)

        self.ROIx1.setValue(0)
        self.ROIx2.setValue(right_bound)
        self.ROIy1.setValue(0)
        self.ROIy2.setValue(upper_bound)
        
        
    # ***** end defaultROI ******************************* 
               
    # ************************************ 
    def update_bkgd(self):
    # get a value for the background so we can properly substract in pixel sum atom number counting 
        self.rawROIx1=int(self.a4.get_xlim()[0])
        self.rawROIx2=int(self.a4.get_xlim()[1])
        self.rawROIy1=int(self.a4.get_ylim()[0])
        self.rawROIy2=int(self.a4.get_ylim()[1])
         
        if (self.whichImageCombo.currentText() == 'Image 2'):
            data = self.img2
        elif (self.whichImageCombo.currentText() == 'Image 3'):
            data = self.img3
        elif (self.whichImageCombo.currentText() == 'Processed'):
            data = self.atoms
        else:
            data = self.img1
            
        self.picInROI = data[self.rawROIx1:self.rawROIx2,self.rawROIy1:self.rawROIy2]
        self.picInROI  = np.nan_to_num(self.picInROI)
        self.bkgdAvg = np.sum(self.picInROI)/self.picInROI.size   
        self.bkgdValue.setValue(self.bkgdAvg)
       
    # ***** end defaultROI ******************************* 


    # ************************************ 
    def writeDataFile(self):
    # create a text file that our data analysis program can read.
        if self.dataSaveCheck.isChecked():
            file = open(self.OutputFile.text(), "w")
            file.write(self.Ctrlfile)      
            file.write('\n')
            file.write('\n')
            self.write_paramaters(file)
            
            file.close()
            
    # ***** end writeDataFile *******************************

    def write_paramaters(self,file_handle):
            file_handle.write('# Image Data\n')
            
            file_handle.write('Atom num (sum) = '+ (self.AtomNumSumLE.text()) + '\n')
            file_handle.write('Atom Num (fit) = '+ (self.AtomNumFitLE.text()) + '\n')
            file_handle.write('Temp-x (uK) = '+ (self.TxLE.text()) + '\n')
            file_handle.write('Temp-y (uK) = '+ (self.TyLE.text()) + '\n')
            file_handle.write('Temp (uK) = '+ (self.TLE.text()) + '\n')
            file_handle.write('x-width (um) = '+ (self.xwidthumLE.text()) + '\n')
            file_handle.write('y-width (um) = '+ (self.ywidthumLE.text()) + '\n')
            
            file_handle.write('xfit_x0 = '+ (self.Hfit_x0.text()) + '\n')
            file_handle.write('xfit_A = '+ (self.Hfit_A.text()) + '\n')
            file_handle.write('xfit_sigx = '+ (self.Hfit_sigx.text()) + '\n')
            file_handle.write('xfit_z0 = '+ (self.Hfit_z0.text()) + '\n')
            
            file_handle.write('yfit_y0 = '+ (self.Vfit_y0.text()) + '\n')
            file_handle.write('yfit_A = '+ (self.Vfit_A.text()) + '\n')
            file_handle.write('yfit_sigy = '+ (self.Vfit_sigy.text()) + '\n')
            file_handle.write('yfit_z0 = '+ (self.Vfit_z0.text()))
    
    def save_current_images(self):
        
        d = date.today()        
        
        folder = (str(self.NumDataFolder.text())+ d.strftime("%Y/%m/%d/")+"Filenum_"+str(self.filenum).zfill(4))
        if self.fileTag.text():
            folder +='('+str(self.fileTag.text())+')/'
        else:
            folder += '/'
        
        if not os.path.exists(folder):
            os.makedirs(folder)
        
        self.write_imgs_bmp(self.img1,folder+"Image1.bmp")
        self.write_imgs_bmp(self.img2,folder+"Image2.bmp")
        self.write_imgs_bmp(self.img3,folder+"Image3.bmp")
        
        control_filepath = folder + "AllData.txt"
        f = open(control_filepath, "w+")
        f.write(self.Ctrlfile)      
        f.write('\n')
        f.write('\n')
        self.write_paramaters(f)
        f.close()
        
        plt.savefig(folder+'Analysis_Window')
    
    def write_imgs_bmp(self,image,filepath):
    
        [im_height,im_width] = np.shape(image)
        bpp = 8
        if np.max(image) > 255:
            bpp = 16
            
        write_buffer = bytearray(im_width*im_height*bpp/8 + 1500)

        a=image
        a = bytearray(a)
        
        struct.pack_into('<L',write_buffer, 0, int((np.binary_repr(ord('M'),width = 8)+np.binary_repr(ord('B'),width=8)),2))
        struct.pack_into('<L',write_buffer, 2, im_width*im_height*bpp/8 + 1500) #size of the file
        struct.pack_into('<L',write_buffer, 10, 70) #the byte where the image data begins
        struct.pack_into('<L',write_buffer, 14, 40) #size of this header
        struct.pack_into('<L',write_buffer, 18, im_width) #width
        struct.pack_into('<L',write_buffer, 22, im_height) #height
        struct.pack_into('<L',write_buffer, 26, 1) # number of colour planes
        struct.pack_into('<L',write_buffer, 28, bpp) #bits per pixel
        struct.pack_into('<L',write_buffer, 30, 0) #compression method
        struct.pack_into('<L',write_buffer, 34, 0) #dummy image size
        struct.pack_into('<L',write_buffer, 38, 3000) #horizontal pixels per meter
        struct.pack_into('<L',write_buffer, 42, 3000) #vertical pixels per meter
        struct.pack_into('<L',write_buffer, 46, 0) #dummy colour info
        struct.pack_into('<L',write_buffer, 50, 0) #dummy colour info

        if bpp == 8: #this is if the image is in Mono8 mode (8 bits per pixel)
            for i in range(256):
                bin_string = np.binary_repr(i,width = 8)
                int_to_write = int('00000000'+bin_string+bin_string+bin_string,2)
                struct.pack_into('<L',write_buffer, 54 + 4*i, int_to_write)

            row_size = int(np.floor((8*im_width+31)/32.)*4)    
            last_offset = 1074

            for i in range(im_height)[::-1]:
                current = row_size*i
                for j in range(row_size/4):
                    last_offset += 4
                    write_buffer[last_offset] = a[current]     #first pixel
                    write_buffer[last_offset+1] = a[current+1]     #next pixel
                    write_buffer[last_offset+2] = a[current+2]     #third pixel
                    write_buffer[last_offset+3] = a[current+3]     #last pixel in this byte
                    current += 4
                        
        elif bpp == 16: #this is if the image is in Mono16 mode (16 bits per pixel)
            struct.pack_into('<L',write_buffer, 30, 3) # change compression method to use colour maps

            
            struct.pack_into('>L',write_buffer, 54 + 0, int('0000FFFF',16)) #red bits - will contain nothing
            struct.pack_into('>L',write_buffer, 54 + 4, int('FF000000',16)) #green bits - will contain MSB
            struct.pack_into('>L',write_buffer, 54 + 8, int('00FF0000',16)) #blue bits - will contain LSB

            last_offset = 54+12

            #this saves the MSB digits into the green channel, and LSB into blue channel in little endian format (X,Blue,Green,Red)
            #here the LSB is only 6 bits, leaving the 2 last bits as 0
            for i in range(im_height)[::-1]:
                current = 2*im_width * i
                for j in range(im_width/2):
                    last_offset += 4
                    write_buffer[last_offset+1] = a[current+0]     #LSB to the blue channel
                    write_buffer[last_offset+0] = a[current+1]     #MSB to the green channel
                    #next pixel
                    write_buffer[last_offset+3] = a[current+2]     #LSB to the blue channel
                    write_buffer[last_offset+2] = a[current+3]     #MSB to the green channel
                    current += 4
                
        g = open(filepath,'wb+')
        g.write(write_buffer)

        g.close()

    
    def getCtrldata(self):
    # get the current control data so it matches the image
    #        filename =  "C:/Users/Ultracold/Google Drive/LindsayData/PythonData.txt"\
        filename = self.ControlFile.text()
        fp = open(filename,'r')
        self.Ctrlfile = fp.read()
        temp = self.Ctrlfile
        temp2 = temp.split('=')
        temp = temp2[1]
        temp = temp.split('\n')
        self.filenum = int(temp[0])
        fp.close()
        self.fileNumLabel.setText("Filenum: %i"%(self.filenum))
        
        # get the file number
        
           
    

class snapshot_thread(threading.Thread):
    def __init__(self,q):
        threading.Thread.__init__(self)
        self.q = q
        self._stop = threading.Event()
    def run(self,):
        global dev
        global enable_snapshot_thread
        
        while not self._stop.isSet():
            if not enable_snapshot_thread:
                time.sleep(0.2)
                continue
            
            failed_to_acq = False    
            temp_imgs = []    
            
            for i in range(3):
                image = triggered_snapshot(dev,dev.Setting.Base.Camera.ImageRequestTimeout_ms.value)
                
                if not image:
                    failed_to_acq = True
                    print 'failed to acquire an image'
                    time.sleep(1)
                    break
                    
                else:    
                    temp_imgs.append(image)
                    
            if not failed_to_acq:
                queue_lock.acquire()
                if self.q.qsize() > 0:
                    for i in range(self.q.qsize()):
                        a = self.q.get()
                for i in temp_imgs:
                    self.q.put(i)
                queue_lock.release()
                time.sleep(0.5)
    def stop(self,):
        self._stop.set()
            
class GUIThread(QtCore.QObject):
    kill_signal = QtCore.pyqtSignal(threading.Thread)
    
    def __init__(self,q):
        QtCore.QObject.__init__(self)
        self.q = q
        
    def run(self,thread_to_kill):
        global dev
        app = QApplication(sys.argv)
        main = Main(dev,self.q)
        main.show()
        main.update_param_disp()
        main.update_trigger_disp()
        app.exec_()
        self.kill_signal.emit(thread_to_kill)

@QtCore.pyqtSlot(threading.Thread)
def kill_thread(thread):
    thread.stop()
    
    
    
if __name__ == '__main__':
    global device_id
    global enable_snapshot_thread
    
    app1 = QApplication(sys.argv)
    main = CamWindow()
    main.show()
    app1.exec_()
    
    del main, app1
    
    enable_snapshot_thread = False
    
    dev = mv.dmg.get_device(device_id)
    
    image_queue = Queue.Queue(3)
    queue_lock = threading.Lock()
    
    t1 = GUIThread(image_queue)
    t2 = snapshot_thread(image_queue)
    t1.kill_signal.connect(kill_thread)
    t2.start()
    t1.run(t2)
    sys.exit()
    

    