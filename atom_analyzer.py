# -*- coding: utf-8 -*-
"""
Created on Tue Jan 19 10:09:26 2016

@author: Lindsay
"""

from lmfit import Model
import os
import numpy as np

ROOT_PATH = os.getcwd()


gamma = 6.0e6  # MHz
rb_mass = 87. * 1.67e-27  # kg
kB = 1.38e-23  # J/K
 
def funcGaussian(x,A,x0,sigma,y0):
# the independent variable must be sent first for the fit function
       return A*np.exp(-((x-x0)/sigma)**2/2)+y0


   
class Analyzer(object):
    def __init__(self, main):
        self.main = main

        self.xvals=[]
        self.yvals=[]      
        self.xvals_haxis =[]
        self.yvals_haxis =[]

        self.atoms = np.array([])
        self.sliced_atoms = np.array([])
        self.img1 = np.array([])
        self.img2 = np.array([])
        self.img3 = np.array([])

        self.atom_params = AtomParameters(self.main, self)

        # and fit parameters

        self.main.sliceWidth.setMinimum(2)
        self.main.sliceWidth.setMaximum(500)
        self.main.sliceWidth.setValue(20)
        
        self.main.Hfit_x0.setText(str(1.0))
        self.main.Hfit_A.setText(str(1.0))
        self.main.Hfit_sigx.setText(str(1.0))
        self.main.Hfit_z0.setText(str(1.0))
        self.main.Vfit_y0.setText(str(1.0))
        self.main.Vfit_A.setText(str(1.0))
        self.main.Vfit_sigy.setText(str(1.0))
        self.main.Vfit_z0.setText(str(1.0))

        self.x_model = Model(funcGaussian)
        self.y_model = Model(funcGaussian)

        self.x_model.set_param_hint('A', max=10000, min=0.001)
        self.x_model.set_param_hint('x0', min=1, max=1000)
        self.x_model.set_param_hint('sigma', min=1, max=1000)
        self.x_model.set_param_hint('y0', min=-100, max=100)

        self.y_model.set_param_hint('A', max=10000, min=0.001)
        self.y_model.set_param_hint('x0', min=1, max=1000)
        self.y_model.set_param_hint('sigma', min=1, max=1000)
        self.y_model.set_param_hint('y0', min=-100, max=100)


        self.main.imageTypeCombo.addItems(['Absorption', 'Fluorescence'])
        self.main.FitTypeCombo.addItems(['Gaussian (full)', 'Gaussian (ROI)', 'Gaussian (ROI->slice)'])
        self.main.atomCombo.addItems(['87 Rb', '39 K', '40 K'])

    @property
    def ROIx1(self):
        return self.main.ROIx1.value()

    @property
    def ROIx2(self):
        return self.main.ROIx2.value()

    @property
    def ROIy1(self):
        return self.main.ROIy1.value()

    @property
    def ROIy2(self):
        return self.main.ROIy2.value()

    @property
    def fit_type(self):
        return self.main.FitTypeCombo.currentText()

    @property
    def image_type(self):
        return self.main.imageTypeCombo.currentText()
    
    @property
    def slice_width(self):
        return self.main.sliceWidth.value()

    def set_images(self, images):
        print 'updating images'
        self.img1 = np.array(images[0])
        self.img2 = np.array(images[1])
        self.img3 = np.array(images[2])

        self.process_data()

    def process_data(self):
        self.update_atoms()
        self.update_slices()
        self.update_xfit()
        self.update_yfit()
        self.calcAtoms()

    def update_atoms(self):
        img1_float = self.img1.astype(float)
        img2_float = self.img2.astype(float)
        img3_float = self.img3.astype(float)

        if self.image_type == 'Absorption':
            # analyze image using Beer's law. Check for divide by zero, ln(<0)
            denom = (img2_float - img3_float)
            denom[denom == 0] = 1

            ratio = (img1_float - img3_float) / denom
            ratio[ratio <= 0] = 0.01

            self.atoms = -np.log(ratio)
        elif self.image_type == 'Fluorescence':
            # just subtract background.  Ignore Img3 if it exists
            self.atoms = self.img1 - self.img2
        else:
            self.atoms = self.img1
    
    def update_slices(self):
    # Perform analysis based on the choice between: (['Gaussian (full)','Gaussian (ROI)','Gaussian (ROI->slice)'])        
        if self.main.FitTypeCombo.currentText() == 'Gaussian (full)':
            sliced_atoms = self.atoms
            r, c = np.shape(self.atoms)

            self.xvals = np.sum(self.atoms,0)/r
            self.yvals = np.sum(self.atoms,1)/c

            self.xvals_haxis = np.arange(0,c,1)
            self.yvals_haxis = np.arange(0,r,1)
        else:
            sliced_atoms = self.atoms[self.ROIy1 : self.ROIy2, self.ROIx1 : self.ROIx2]
            r, c = np.shape(sliced_atoms)

            self.xvals = np.sum(sliced_atoms, 0)/r
            self.yvals = np.sum(sliced_atoms, 1)/c

            self.xvals_haxis = np.arange(self.ROIx1, self.ROIx2, 1)
            self.yvals_haxis = np.arange(self.ROIy1, self.ROIy2, 1)
            
            if self.main.FitTypeCombo.currentText() == 'Gaussian (ROI->slice)':
                centrex, a, b, c = self.statAnalysis(self.xvals_haxis, self.xvals)
                centrey, a, b, c = self.statAnalysis(self.yvals_haxis, self.yvals)

                width = int(self.slice_width/2)

                self.xvals = np.sum(sliced_atoms[int(centrey)-width:int(centrey)+width, :], 0)/(2*width)
                self.yvals = np.sum(sliced_atoms[:, int(centrex)-width:int(centrex)+width], 1)/(2*width)
        self.sliced_atoms = sliced_atoms

    def statAnalysis(self,xv,yv):
        # make some guesses for the fits
        centre = np.sum(np.power(yv,2)*xv)/np.sum(np.power(yv,2))
        var = np.sum(np.power(yv,2)*np.power(xv,2))/np.sum(np.power(yv,2))
        sig = np.sqrt(var-centre**2)
        A = np.max(yv)
        z0 = np.mean(yv)
        return centre, sig, A, z0

    def update_xfit(self):
        centre, sig, A, z0 = self.statAnalysis(self.xvals_haxis, self.xvals)

        centre = float(self.main.Hfit_x0.text()) if self.main.Hfit_x0_ck.isChecked() else centre
        sig = float(self.main.Hfit_sigx.text()) if self.main.Hfit_sigx_ck.isChecked() else sig
        A = float(self.main.Hfit_A.text()) if self.main.Hfit_A_ck.isChecked() else A
        z0 = float(self.main.Hfit_z0.text()) if self.main.Hfit_z0_ck.isChecked() else z0

        self.x_model.set_param_hint('A', value=A, vary = not self.main.Hfit_A_ck.isChecked())
        self.x_model.set_param_hint('x0', value=centre, vary = not self.main.Hfit_x0_ck.isChecked())
        self.x_model.set_param_hint('sigma', value=sig, vary = not self.main.Hfit_sigx_ck.isChecked())
        self.x_model.set_param_hint('y0', value=z0, vary = not self.main.Hfit_z0_ck.isChecked())

        params = self.x_model.make_params()
        fits = self.x_model.fit(self.xvals, x=self.xvals_haxis, params=params)
        self.atom_params.x_fits = fits.best_values
        self.main.fitdisplay.setPlainText(fits.fit_report())
        self.update_xfit_display()

    def update_yfit(self):
        centre, sig, A, z0 = self.statAnalysis(self.yvals_haxis, self.yvals)

        centre = float(self.main.Vfit_y0.text()) if self.main.Vfit_y0_ck.isChecked() else centre
        sig = float(self.main.Vfit_sigy.text()) if self.main.Vfit_sigy_ck.isChecked() else sig
        A = float(self.main.Vfit_A.text()) if self.main.Vfit_A_ck.isChecked() else A
        z0 = float(self.main.Vfit_z0.text()) if self.main.Vfit_z0_ck.isChecked() else z0

        self.y_model.set_param_hint('A', value=A, vary=not self.main.Vfit_A_ck.isChecked())
        self.y_model.set_param_hint('x0', value=centre, vary=not self.main.Vfit_y0_ck.isChecked())
        self.y_model.set_param_hint('sigma', value=sig, vary=not self.main.Vfit_sigy_ck.isChecked())
        self.y_model.set_param_hint('y0', value=z0, vary=not self.main.Vfit_z0_ck.isChecked())

        params = self.y_model.make_params()
        fits = self.y_model.fit(self.yvals, x=self.yvals_haxis, params=params)
        self.atom_params.y_fits = fits.best_values
        self.main.fitdisplay.setPlainText(fits.fit_report())
        self.update_yfit_display()

    def update_xfit_display(self):
       self.main.Hfit_A.setText('{:.3f}'.format(self.atom_params.x_fits.get('A')))
       self.main.Hfit_x0.setText('{:.3f}'.format(self.atom_params.x_fits.get('x0')))
       self.main.Hfit_sigx.setText('{:.3f}'.format(self.atom_params.x_fits.get('sigma')))
       self.main.Hfit_z0.setText('{:.3f}'.format(self.atom_params.x_fits.get('y0')))

    def update_yfit_display(self):
       self.main.Vfit_A.setText('{:.3f}'.format(self.atom_params.y_fits.get('A')))
       self.main.Vfit_y0.setText('{:.3f}'.format(self.atom_params.y_fits.get('x0')))
       self.main.Vfit_sigy.setText('{:.3f}'.format(self.atom_params.y_fits.get('sigma')))
       self.main.Vfit_z0.setText('{:.3f}'.format(self.atom_params.y_fits.get('y0')))

    def calcAtoms(self):
        self.main.AtomNumSumLE.setText('{:.3e}'.format(self.atom_params.number_sum))
        self.main.AtomNumFitLE.setText('{:.3e}'.format(self.atom_params.number_fit))
        self.main.TxLE.setText('{:.3f}'.format(self.atom_params.temp_x))
        self.main.TyLE.setText('{:.3f}'.format(self.atom_params.temp_y))
        self.main.TLE.setText('{:.3f}'.format(self.atom_params.temp))
        self.main.xwidthumLE.setText('{:.3f}'.format(self.atom_params.width_x_um))
        self.main.ywidthumLE.setText('{:.3f}'.format(self.atom_params.width_y_um))


class AtomParameters(object):
    def __init__(self, main, analyzer):
        self.main = main
        self.analyzer = analyzer
        self.x_fits = {}
        self.y_fits = {}
        
        self.main.pixSize.setValue(7.4)
        self.main.detuning.setValue(0)
        self.main.TOF.setValue(5)
        self.main.lamda.setValue(780.24)

    @property
    def wavelength(self):
        return self.main.lamda.value() * 1.e-9

    @property
    def detune(self):
        return self.main.detuning.value() * 1.e6

    @property
    def pixel_size(self):
        return self.main.pixSize.value()

    @property
    def tof(self):
        return self.main.TOF.value()

    @property
    def scatt_0(self):
        return 3./2./np.pi * self.wavelength**2

    @property
    def scatt(self):
        return self.scatt_0/(1.+(2.*self.detune/gamma)**2)

    @property
    def width_x_um(self):
        return self.pixel_size * self.x_fits.get('sigma')

    @property
    def width_y_um(self):
        return self.pixel_size * self.y_fits.get('sigma')

    @property
    def od_max(self):
        return np.sqrt(float(self.x_fits.get('A') * self.y_fits.get('A')))  # geometric average

    @property
    def temp_x(self):
        return self.width_x_um * self.width_x_um * rb_mass / kB / (self.tof ** 2)

    @property
    def temp_y(self):
        return self.width_y_um * self.width_y_um * rb_mass / kB / (self.tof ** 2)

    @property
    def temp(self):
        return self.width_x_um * self.width_y_um * rb_mass / kB / (self.tof ** 2)

    @property
    def number_fit(self):
        return 2. * np.pi * self.od_max * self.width_x_um * self.width_y_um * 1.e-12 / self.scatt

    @property
    def number_sum(self):
        atom_sum = np.sum(self.analyzer.sliced_atoms)
        if self.main.subBkgd.isChecked():
            atom_sum -= self.bkgdAvg * self.analyzer.sliced_atoms.size

        return (self.pixel_size * 1.e-6) ** 2 / self.scatt * (atom_sum)