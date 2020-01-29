For this package to run correctly 


1. Install the Anaconda distribution on Windows for Python 2.7


1. Make sure that git is installed on the computer. If not, download and install it.

1. Find a file directory location to clone (i.e. download) this repository. Right click in the Windows Explorer window for that directory and click on the `<Git Bash>` menu option. When the prompt window opens, enter the normal git config options. Clone the repository.

1. Open the Anaconda Prompt and install the `<lmfit>` and `<pyqt5>` packages with the commands:
	* conda install -c conda-forge lmfit  (From [Anaconda](https://anaconda.org/conda-forge/lmfit))
	* conda install -c anaconda pyqt (From [Anaconda](https://anaconda.org/anaconda/pyqt))
Wait for the files and dependencies to download. Close the prompt window.

1. Download and install Microsoft Visual C++ Compiler for Python 2.7: [https://www.microsoft.com/en-ca/download/details.aspx?id=44266
](https://www.microsoft.com/en-ca/download/details.aspx?id=44266
)

1. Download and install from the Google Drive in `<My Drive/Scott Wilson/Point Grey USB3 Cam Files>` the [mvGenTL_Acquire install file](https://drive.google.com/open?id=15s1UWyee9QR4_iMUHH7fOnKHb7v47idX). After installing you will need to restart the computer. Select the default configurations. 


1. The Point Grey/FLIR drivers are already installed. After installing the Matrix Vision (mv) software, update the drivers for the cameras: Device Manager >> Right click on device >> Properties >> Driver >> Update Driver >> "Browse my computer for driver software" >> "Let me pick..." >> Select the driver named "USB3 Vision Device (Bound to MATRIX VISION GmbH driver using libusbK)". You will need to restart the computer.


1. 

1. After creating a runTOF.bat file, change the path to the "activate.bat" file in the local /Anaconda2/Scripts directory
4. Change the save file paths in tof-analysis.py

