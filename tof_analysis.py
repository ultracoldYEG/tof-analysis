# -*- coding: utf-8 -*-
"""
Created on Tue Jan 19 10:09:26 2016

@author: Lindsay
"""
from PyQt5.uic import loadUiType
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

import matplotlib.pyplot as plt    
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Cursor

import sys
import os
import numpy as np
from datetime import date

# import mv
import mock_mv as mv

import bmp_loader
import capture_threads
import atom_analyzer

ROOT_PATH = os.getcwd()

Ui_MainWindow, QMainWindow = loadUiType(os.path.join(ROOT_PATH, 'tof_analysis.ui'))
Ui_CamSelect, QCamSelect = loadUiType(os.path.join(ROOT_PATH, 'cam_selector.ui'))

def funcGaussian(x,A,x0,sigma,y0):
# the independent variable must be sent first for the fit function
       return A*np.exp(-((x-x0)/sigma)**2/2)+y0
        
 
class CamWindow(QCamSelect, Ui_CamSelect):
    def __init__(self):
        super(CamWindow, self).__init__()
        self.setupUi(self)
        self.device_id = None
        self.devices = {
            'Top Cam': '14234117',
            'Side Cam': '14366837',
            'Andrei': '15384643',
        }

        self.cameraCombo.addItems(self.devices.keys())
        self.openButton.clicked.connect(self.opened)
        self.cancelButton.clicked.connect(self.cancelled)
        
    def opened(self):
        self.device_id = self.devices.get(self.cameraCombo.currentText())
        self.done(0)
        
    def cancelled(self):
        sys.exit()

   
class Main(QMainWindow, Ui_MainWindow):
    def __init__(self, device,):
        super(Main, self).__init__()
        self.setupUi(self)
        self.dev = device

        self.running = RunLock(False)
        self.updating = RunLock(False)
        self.snapshot_thread = capture_threads.AbsorptionCapture(self.dev, self.running)
        self.continuous_capture_thread = capture_threads.ContinuousCapture(self.dev, self.running, min_delay=0)
        self.delayed_capture_thread = capture_threads.DelayedCapture(self.dev, self.running, min_delay=0)
        self.triggered_capture_thread = capture_threads.TriggeredCapture(self.dev, self.running)

        self.snapshot_thread.finished.connect(self.set_images)
        self.continuous_capture_thread.finished.connect(self.new_continuous_capture)
        self.delayed_capture_thread.finished.connect(self.new_capture)
        self.triggered_capture_thread.finished.connect(self.new_capture)

        self.captures = []

        self.analyzer = atom_analyzer.Analyzer(self)

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
        self.canvas1.mpl_connect('button_press_event', self.xyzvals)
        self.cursor1 = Cursor(self.a1, useblit=True, color='k')
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
        self.loadDataButton.clicked.connect(self.start_snapshot_thread)
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
        self.whichImageCombo.addItems(['Image 1', 'Image 2', 'Image 3', 'Processed'])
        self.whichImageCombo.activated.connect(self.update_rawimage)
        self.cmapCombo.addItems(['coolwarm', 'gray', 'spectral', 'coolwarm_r', 'gray_r', 'spectral_r'])
        self.cmapRawCombo.addItems(['coolwarm', 'gray', 'spectral', 'coolwarm_r', 'gray_r', 'spectral_r'])
        self.cmapCombo.activated.connect(self.update_image)
        self.cmapRawCombo.activated.connect(self.update_rawimage)

        self.user_auto_expose_6.addItems(['Off', 'Once', 'Continuous'])
        self.user_auto_gain_6.addItems(['Off', 'Once', 'Continuous'])
        self.user_gamma_enable.addItems(['Off', 'On'])
        self.user_pixel_format_6.addItems(['Mono8', 'Mono16'])
        self.user_trigger_mode.addItems(["Off", "On"])
        self.user_trigger_source.addItems(["Line0", "Line2", "Line3", "Software"])
        self.user_trigger_activation.addItems(["RisingEdge", "FallingEdge", "AnyEdge", "LevelLow", "LevelHigh"])

        self.presets_filepath = os.path.join(ROOT_PATH, 'CAMpresets.csv')
        with open(self.presets_filepath,'r') as f:
            for line in f:
                line=line.split(',')
                if line[0] == 'name':
                    self.preset_combobox.addItems(line[1].rsplit())
        
        # setup spin boxes
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
                   
        # Set for testing
        # self.OutputFile.setText('Z:/Data/ImageData/bmp_test/AllData.txt')
        # self.ControlFile.setText("Z:/PythonData")
        # self.NumDataFolder.setText('Z:/Data/ImageData/')
        self.OutputFile.setText(os.path.join(ROOT_PATH, 'AllData.txt'))
        self.ControlFile.setText(os.path.join(ROOT_PATH, 'PythonData.txt'))
        self.NumDataFolder.setText(os.path.join(ROOT_PATH, 'ImageData'))

        # set original data arrays to zero
        self.atoms = np.random.rand(5,5)
        self.img1 = np.random.rand(5,5)
        self.img2 = np.random.rand(5,5)
        self.img3 = np.random.rand(5,5)
        #

        # initial ROI values
        self.defaultROI()
        self.update_param_disp()
        self.update_trigger_disp()
    
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
            print(e)

        self.update_param_disp()
            
    def set_trigger_params(self):
        #this will apply the trigger settings in the "set to" column to the cameras

        try:
            GenICam_handle = self.dev.Setting.Base.Camera.GenICam
            GenICam_handle.AcquisitionControl.TriggerMode = str(self.user_trigger_mode.currentText())
            GenICam_handle.AcquisitionControl.TriggerSource = str(self.user_trigger_source.currentText())
            GenICam_handle.AcquisitionControl.TriggerActivation = str(self.user_trigger_activation.currentText())
            self.dev.Setting.Base.Camera.ImageRequestTimeout_ms.value = float(self.user_trigger_timeout.value())
            
        except Exception as e:
            print(e)
            
        self.update_trigger_disp()
        
    def read_preset_file(self):
        #this function parses the preset csv file and finds the name that matches the value in the "preset" combo box.
        
        with open(self.presets_filepath, 'r') as f:
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

                if line[1].rstrip() == preset_name:
                    found_name = True
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
        image = np.require(image, np.uint8, 'C')
        img = QImage(image.data, image.shape[1], image.shape[0], image.strides[0], QImage.Format_Indexed8)
        pix_map = QPixmap.fromImage(img)
        self.img_label.setPixmap(pix_map.scaled(self.img_label.width(), self.img_label.height(), QtCore.Qt.KeepAspectRatio))

    def new_capture(self, image):
        self.captures.append(image)
        if len(self.captures) >= self.capture_num.value():
            self.redraw_cam_plot(self.captures[0])
            self.update_param_disp()
            self.update_trigger_disp()
            self.capture_num_info.setText('1/' + str(self.capture_num.value()))
            return
        self.start_single_capture_thread()

    def new_continuous_capture(self, image):
        down_sample_factor = self.user_down_sample.value()
        self.continuous_capture_thread.min_delay = 1.0 / self.user_max_fps.value()
        self.redraw_cam_plot(image[::down_sample_factor, ::down_sample_factor])

    def capture_new_image(self):
        #this will capture a specified number of images with or without a trigger

        self.captures = []
        self.start_single_capture_thread()

    def start_single_capture_thread(self):
        self.delayed_capture_thread.min_delay = self.min_time_delay.value()/1000.
        if str(self.dev.Setting.Base.Camera.GenICam.AcquisitionControl.TriggerMode) == 'On':
            self.triggered_capture_thread.start()
        else:
            self.delayed_capture_thread.start()
        
    def increase_capture_scroll(self):
        #used to scroll left or right if multiple images are collected by a multishot
        if self.running.state:
            print('Cannot scroll while capturing')
            return
        current_index, current_capture_num = [int(x) for x in self.capture_num_info.text().split('/')]
        self.redraw_cam_plot(self.captures[current_index % current_capture_num])
        self.capture_num_info.setText(str((current_index % current_capture_num) + 1)+'/'+str(current_capture_num))
        
    def decrease_capture_scroll(self):
        #used to scroll left or right if multiple images are collected by a multishot capture
        if self.running.state:
            print('Cannot scroll while capturing')
            return
        current_index, current_capture_num = [int(x) for x in self.capture_num_info.text().split('/')]
        self.redraw_cam_plot(self.captures[(current_index-2) % current_capture_num])
        self.capture_num_info.setText(str((current_index-2) % current_capture_num+1)+'/'+str(current_capture_num))

    def update_continuous_capture(self):
        if self.continuous_capture_cb.isChecked():
            if self.running.state:
                print('Cannot capture image while another capture thread is running')
                self.continuous_capture_cb.setCheckState(False)
                return
            self.continuous_capture_thread.start()
        else:
            self.continuous_capture_thread.stop()
        
    def update_auto_update(self):
        self.snapshot_thread.start()

    def set_images(self, images):
        self.img1 = np.array(images[0])
        self.img2 = np.array(images[1])
        self.img3 = np.array(images[2])

        self.analyzer.set_images(images)

        if self.AutoUpdateImage.isChecked():
            self.start_snapshot_thread()

        self.process_data()

    def start_snapshot_thread(self):
        self.snapshot_thread.start()

    def xyzvals(self,event):
        # function to call if the autoupdate is on, and the polling timeout is reached
        if event.inaxes is None:
            return
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
        
        #self.lxRaw.set_ydata(event.ydata)
        #self.lyRaw.set_xdata(event.xdata)
        self.canvas4.draw()

    def update_fits(self):
        # a routine to gather data from various files and compile it nicely
        self.analyzer.process_data()
    
    def update_atoms(self):
        self.analyzer.update_atoms()
        self.atoms = self.analyzer.atoms
    
    def getAtomsData(self):
    # get the values that we select to plot from various files, and create a data file with them        
        filename = self.ImageFile.text()
        atoms = np.loadtxt(filename,delimiter=',')
        return atoms
        
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
            cmesh.set_clim(
                vmin = np.min(self.atoms),
                vmax = np.max(self.atoms)
            )
        else:
            cmesh.set_clim(
                vmin = self.CLimSpinMin.value(),
                vmax = self.CLimSpinMax.value()
            )
        self.a1.set_xlim([self.ROIx1.value(),self.ROIx2.value()])
        self.a1.set_ylim([self.ROIy1.value(),self.ROIy2.value()])

        self.lx = self.a1.axhline(y =  self.ycursor, color = 'black') # the horiz line
        self.ly = self.a1.axvline(x =  self.xcursor, color = 'black')  # the horiz line
         
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
        self.a4.set_xlim([self.analyzer.xvals_haxis[0],self.analyzer.xvals_haxis[-1]])
        self.a4.set_ylim([self.analyzer.yvals_haxis[0],self.analyzer.yvals_haxis[-1]])
    
        self.a4.set_aspect(1)
        self.fig4.colorbar(cmesh,cax=self.cax4)
        self.canvas4.draw()
    
    def update_xplot(self):
        # a routine to update the figure with new data
        # get plot settings before update
 
        self.a2.hold(True) 
        self.a2.plot(self.analyzer.xvals_haxis,self.analyzer.xvals,'-',lw=1,color='deepskyblue')
        self.a2.set_xlim([self.ROIx1.value(),self.ROIx2.value()])
             
        fitx = np.linspace(self.analyzer.xvals_haxis[0],self.analyzer.xvals_haxis[-1])
        fity = funcGaussian(fitx,float(self.Hfit_A.text()),float(self.Hfit_x0.text()),float(self.Hfit_sigx.text()),float(self.Hfit_z0.text()))
        self.lxslice = self.a2.axvline(x =  self.xcursor,color = 'black') # the horiz line
           
        self.a2.plot(fitx,fity,'k--',lw=1)  
        self.a2.hold(False)        

    def update_yplot(self):
        # a routine to update the figure with new data
        # get plot settings before update
         
        self.a3.hold(True)        
        self.a3.plot(self.analyzer.yvals_haxis,self.analyzer.yvals,'g-',lw=1)
        self.a3.set_xlim([self.ROIy1.value(),self.ROIy2.value()])
                 
        fitx = np.linspace(self.analyzer.yvals_haxis[0],self.analyzer.yvals_haxis[-1])
        fity = funcGaussian(fitx,float(self.Vfit_A.text()),float(self.Vfit_y0.text()),float(self.Vfit_sigy.text()),float(self.Vfit_z0.text()))
        self.lyslice = self.a3.axvline(x =  self.ycursor,color = 'black') # the horiz line
           
        self.a3.plot(fitx,fity,'k--',lw=1)
        self.a3.hold(False)

    def process_data(self):
        self.update_atoms()

        self.getCtrldata()
        QApplication.processEvents()
        
        self.initialize_fig_1()
        self.initialize_fig_4()

        self.update_xplot()
        QApplication.processEvents()
        
        self.update_yplot()
        self.update_image()
        QApplication.processEvents()

        self.update_rawimage()
        QApplication.processEvents()

        self.writeDataFile()
        QApplication.processEvents()

    
    def load_Ctrlpath(self): 
        self.Ctrlpath = QFileDialog.getOpenFileName(self,'Select Controls File (PythonData)')
        self.ControlFile.setText(self.Ctrlpath)

    def load_Outpath(self): 
        self.Outpath = QFileDialog.getOpenFileName(self,'Select Output File (Physical Data)')
        self.OutputFile.setText(self.Outpath)

    def load_NumDataFolder(self): 
        self.NumDataFolderName = QFileDialog.getExistingDirectory(self,'Select Directory/Folder (For numbered Control and Physical Data)')
        self.NumDataFolder.setText(self.NumDataFolderName)

    def xchange(self,ax):
        # adjust ROI when using toolbar in image 1
        self.update_ROI(x1 = self.a1.get_xlim()[0], x2 = self.a1.get_xlim()[1], draw = False)

    def ychange(self,ax):
        # adjust ROI when using toolbar in image 1
        self.update_ROI(y1 = self.a1.get_ylim()[0], y2 = self.a1.get_ylim()[1], draw = False)

    def clip(self, y1, y2, min = 0, max = 100):
        y1, y2 = sorted([y1,y2])
        if y1 < min:
            y2 -= y1
            y1 = 0
        if y2 > max:
            y1 -= y2 - max
            y2 = max
        y1 = np.clip(y1, 0, y2 - 1)
        return y1, y2

    def update_ROI(self, event = None, x1 = None, x2 = None, y1 = None, y2 = None, draw = True):
        if self.updating.state:
            return
        with self.updating:
            x1 = x1 or self.ROIx1.value()
            x2 = x2 or self.ROIx2.value()
            y1 = y1 or self.ROIy1.value()
            y2 = y2 or self.ROIy2.value()

            x1, x2 = self.clip(x1, x2, max=self.atoms.shape[1])
            y1, y2 = self.clip(y1, y2, max=self.atoms.shape[0])

            self.ROIx1.setValue(x1)
            self.ROIx2.setValue(x2)
            self.ROIy1.setValue(y1)
            self.ROIy2.setValue(y2)

            # update main figure
            self.a1.set_xlim([x1, x2], emit = False)
            self.a1.set_ylim([y1, y2], emit = False)

            # update 1D figures
            self.a2.set_xlim([x1, x2])
            self.a3.set_xlim([y1, y2])
            if draw:
                self.canvas1.draw()

    def defaultROI(self):
    # initial ROI values
        GenICam_handle = self.dev.Setting.Base.Camera.GenICam
        
        right_bound = int(GenICam_handle.ImageFormatControl.Width.value)
        upper_bound = int(GenICam_handle.ImageFormatControl.Height.value)

        self.ROIx1.setValue(0)
        self.ROIx2.setValue(right_bound)
        self.ROIy1.setValue(0)
        self.ROIy2.setValue(upper_bound)

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

    def writeDataFile(self):
    # create a text file that our data analysis program can read.
        if self.dataSaveCheck.isChecked():
            file = open(self.OutputFile.text(), "w")
            file.write(self.Ctrlfile)      
            file.write('\n')
            file.write('\n')
            self.write_paramaters(file)
            
            file.close()

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
        
        bmp_loader.write_imgs_bmp(self.img1,folder+"Image1.bmp")
        bmp_loader.write_imgs_bmp(self.img2,folder+"Image2.bmp")
        bmp_loader.write_imgs_bmp(self.img3,folder+"Image3.bmp")
        
        control_filepath = folder + "AllData.txt"
        f = open(control_filepath, "w+")
        f.write(self.Ctrlfile)      
        f.write('\n')
        f.write('\n')
        self.write_paramaters(f)
        f.close()
        
        plt.savefig(folder+'Analysis_Window')

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


class RunLock(object):
    def __init__(self, state):
        self.state = state

    def __enter__(self):
        self.state = True

    def __exit__(self, *args):
        self.state = False


if __name__ == '__main__':
    app1 = QApplication(sys.argv)

    cam_selector = CamWindow()
    cam_selector.show()
    app1.exec_()

    if cam_selector.device_id is None:
        raise ValueError('No device found.')

    dev = mv.dmg.get_device(cam_selector.device_id)

    del cam_selector

    main = Main(dev)
    main.show()
    app1.exec_()
    sys.exit()