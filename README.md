# TOF-analysis
This program is for the capture, processing, and analysis of TOF images of ultracold clouds in time-of-flight.

## Installation
Follow these steps to install and run software correctly:

1. Install the [Anaconda distribution](https://www.anaconda.com/distribution/) on Windows for Python 2.7.

1. Make sure that git is installed on the computer. If not, [download](https://git-scm.com/downloads) and install it.

1. Find a file directory location to clone (i.e. download) this repository. Right click in the Windows Explorer window for that directory and click on the `Git Bash Here` menu option. When the prompt window opens, enter the normal git config options. Clone the repository.

1. Open the Anaconda Prompt and install the `lmfit` and `pyqt5` packages with the commands:
    * conda install -c conda-forge lmfit  (From [Anaconda](https://anaconda.org/conda-forge/lmfit))
    * conda install -c anaconda pyqt (From [Anaconda](https://anaconda.org/anaconda/pyqt))
Wait for the files and dependencies to download. Close the prompt window.

1. Download and install Microsoft Visual C++ Compiler for Python 2.7: [https://www.microsoft.com/en-ca/download/details.aspx?id=44266
](https://www.microsoft.com/en-ca/download/details.aspx?id=44266
)

1. Download and install from the Google Drive in `My Drive/Scott Wilson/Point Grey USB3 Cam Files` the [mvGenTL_Acquire install file](https://drive.google.com/open?id=15s1UWyee9QR4_iMUHH7fOnKHb7v47idX). After installing you will need to restart the computer. Select the default configurations. 

1. Now that we have the drivers for the cameras, we now need a wrapper that can work in Python. There is a github that does just that: [https://github.com/geggo/MVacquire](https://github.com/geggo/MVacquire). We also have a copy of that same repository in the [Google Drive](https://drive.google.com/file/d/0B2nT0ELbmtx4OFpsUHQwSlpKQWs/view?usp=sharing). 
    1. The instructions provided on the github are all you really need. Once you have installed Microsoft Visual C++ Compiler for Python 2.7, you should be able to run a cmd terminal which is labelled “Visual C++ 2008 XX-Bit Command Prompt”. XX will be either 32 or 64 depending on the computer you’re running it on.
    
    1. In this command prompt you’ll need to use “cd” to navigate to where you unpacked the github files. 
    1. Once there, just run the following 4 commands:
        * `set MSSDK=1`
        * `set DISTUTILS_USE_SDK=1`
        * `python setup.py build`
        * `python setup.py install`
        
    1. Open a new Anaconda terminal and open a python console with `python`. You should now be able to `import mv`. This contains everything needed to run the USB3 camera.


1. It's not a bad idea to install the Point Grey/FLIR camera drivers. Using their FlyCapture software is a good way to test that the cameras are working correctly.

1. After installing the Matrix Vision (mv) software, update the drivers for the cameras: `Device Manager >> Right click on device >> Properties >> Driver >> Update Driver >> "Browse my computer for driver software" >> "Let me pick..." >> Select the driver named "USB3 Vision Device (Bound to MATRIX VISION GmbH driver using libusbK)"`. You will need to restart the computer.

1. In the runTOF.bat file, change the path to the `activate.bat` file in the local /Anaconda2/Scripts directory. With this command, Python is activated in the working terminal; consequently, the batch file does not need to run in a native Anaconda terminal.

1. Update the name and camera S/N in tof-analysis.py

1. Change the save file paths in tof-analysis.py

1. Make sure that the CycleX.vi file paths match those in tof-analysis.py

