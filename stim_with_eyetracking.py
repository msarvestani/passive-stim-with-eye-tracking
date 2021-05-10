# stim_with_eyetracking.py: Visual Stim GUI
# Author: Matthew McCann (@mkm4884)
# Max Planck Florida Institute for Neuroscience
# Created: 12/01/2016
# Last Modified: 5/09/2021 - madineh

# Description: Simple GUI that allows the user to pick a stimulus protocol from their
# existing stim directory, while providing the option to begin simultaneous eye tracking.

# General packages
from __future__ import division
from PyQt4 import QtCore, QtGui, uic
import _winreg as winreg
import itertools
import glob
import time
import datetime
import os
import shutil
import fileinput
import operator
import subprocess
import cPickle as pkl

# Calibration and Image Processing Packages
from image_processing.ROISelect import *
from image_processing.SubpixelStarburstEyeFeatureFinder import *

# Cameras
from devices.camera_reader import *
from devices.run_Grasshopper import *

# Import task
from task.presenting import *

# load the UI files
StimTracking_class = uic.loadUiType("ui/start_ui.ui")[0]


class StimTracking(QtGui.QMainWindow, StimTracking_class):

    def __init__(self, parent=None):
        # ------------------------------------------------------------
        # UI Initialization
        # ------------------------------------------------------------
        # make Qt window
        super(StimTracking, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Stim + Eye Tracking')

        # becomes a presentation instance when user hits Start
        self.presenting = None

        # set class variables
        self.isPresenting = False
        self.workingDir = os.getcwd()
        self.baseDataPath = "Y:" +os.sep # change this for local machine
        self.baseStimPath = 'stims' + os.sep   # change this for local machine
        self.baseExpPath = 'Y:' + os.sep
        self.experimentPath = self.baseExpPath
        self.stimFile = ''
        self.stimPathFull = ''
        self.animalName = ''
        self.userName = ''
        self.dateStr = str(datetime.date.today())
        self.sessionDirectory = ''  # likewise
        self.trialNum = ''
        self.cameraIDs = []
        self.cameraID = None
        self.useCam = False
        self.useOpto = False
        self.guess = {'pupil_position': [0, 0], 'cr_position': [0, 0]}

        # dropdown actions
        self.cbAnimalName.currentIndexChanged.connect(self.set_animal)
        self.cbCameraID.currentIndexChanged.connect(self.set_camera)

        # Button actions
        self.btnChooseStim.clicked.connect(self.set_stim)
        self.btnSelectROI.clicked.connect(self.selectROI)
        self.btnStart.clicked.connect(self.begin_session)

        # checkbox actions
        self.chkbxEyeTracking.stateChanged.connect(self.set_eyetracking)

        # init dropdown choices
        self.get_animal_dirs()
        self.get_available_cameras()

        # ------------------------------------------------------------
        # Eye Tracking Initialization
        # ------------------------------------------------------------

        # check if a calibration file exists or if we want to skip calibration and eye tracking
        self.isCalibrated = False
        self.onlyEyeMovements = False
        self.fullGazeTracking = False
        self.setROI = False

        # Initialize calibrator and feature finder
        self.camera_device = None
        self.ellipse = None
        self.imaging_modality = '2P'
        self.feature_finder = SubpixelStarburstEyeFeatureFinder(modality=self.imaging_modality)

        # -------------------------------------------------------------
        # Guess for pupil and CR positions
        self.guess = {"pupil_position": array([0, 0]), "cr_position": array([0, 0])}

        # Edges of ROI in relation to full frame
        self.verticesROI = []
        self.ROI_diff = []

    # -- Init Functions _-- #
    def get_animal_dirs(self):
        self.cbAnimalName.addItem("--Select Animal--")
        self.animalDirs = glob.glob(self.baseDataPath + '*')
        for animalDir in self.animalDirs:
            if os.path.isdir(animalDir):
                namePos = animalDir.rfind("\\")+1
                animalName = animalDir[namePos:]
                self.cbAnimalName.addItem(animalName)

    def get_available_cameras(self):
        self.cbCameraID.addItem('Point_Grey')
        cameraPath = 'HARDWARE\\DEVICEMAP\\VIDEO'
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, cameraPath)
        except WindowsError:
            raise EnvironmentError
        for i in itertools.count():
            try:
                val = winreg.EnumValue(key, i)
                self.cameraIDs.append(val[0])
            except EnvironmentError:
                break
        i = 0
        for cameraID in self.cameraIDs:
            self.cbCameraID.addItem(str(i))
            i += 1

    # -- DropDown Actions -- #
    def set_animal(self):
        self.animalName = str(self.cbAnimalName.currentText())

    def set_camera(self):
        self.cameraID = str(self.cbCameraID.currentText())

    # -- Button Actions -- #
    def set_stim(self):
        self.fileDialog = QtGui.QFileDialog(self)
        self.fileDialog.setWindowTitle('Stimulus Files')
        self.fileDialog.setFilter("Python files (*.py)")
        self.stimPathFull = self.fileDialog.getOpenFileName(self, 'Stimulus Files', self.baseStimPath, "Python files (*.py)")
        self.stimFile = str(self.stimPathFull).rsplit('/')[-1]

        if "opto" in self.stimFile.lower():
            print "Using opto stim!"
            self.useOpto = True

        self.txtUpdates.setPlainText('Loaded ' + str(self.stimFile))
        if self.stimFile != '':
            self.chkbxEyeTracking.setEnabled(True)
            self.btnStart.setEnabled(True)
        else:
            self.chkbxEyeTracking.setEnabled(False)
    def make_session(self):
        # check to see if newest data directory already exists
        if self.animalName != '--Select Animal--':
            self.experimentPath = self.experimentPath + self.animalName + '/'
            if not os.path.exists(self.experimentPath):
                os.makedirs(self.experimentPath)

            # We want to save our data to a temporary folder since spike2 doesn't create it's folders until close.
            self.experimentPath = self.experimentPath
            if not os.path.exists(self.experimentPath):
                os.makedirs(self.experimentPath)

            fileinput.close()  # ensure no file input is active already
            exp_num_file = self.baseExpPath + 'instruction.txt'
            if os.path.isfile(exp_num_file):
                for line in fileinput.input(exp_num_file):
                    line = line.rstrip()
                    toks = line.split(' ')

            self.trialNum = toks[0]
            self.experimentPath = self.experimentPath + self.trialNum + '/'
            if not os.path.exists(self.experimentPath):
                os.makedirs(self.experimentPath)

            self.experimentPath = self.experimentPath + self.animalName + '_' + self.trialNum

    def begin_session(self):

        if not self.isPresenting:
            self.isPresenting = True
            self.btnStart.setText('Stop')

            if self.isCalibrated and self.setROI:
                # Run full eye tracking pipeline
                self.useCam = True
                self.fullGazeTracking = True
                self.txtUpdates.append('Full gaze tracking enabled!')
                # start a new recording session by making a dir to put the data in
                self.make_session()
                # start camera recording, live visualization, and training program
                self.start_presenting()

            elif self.setROI and not self.isCalibrated:
                # Run eye tracking pipeline sans gaze angle calculation
                self.useCam = True
                self.onlyEyeMovements = True
                self.txtUpdates.append('Only eye positions will be calculated!')
                # start a new recording session by making a dir to put the data in
                self.make_session()
                # start camera recording, live visualization, and training program
                self.start_presenting()

            elif not self.setROI and not self.isCalibrated:
                # Only present stimulus, do not run camera at all
                self.txtUpdates.append('No video will be saved or analyzed!')
                # start a new recording session by making a dir to put the data in
                self.make_session()
                # start camera recording, live visualization, and training program
                self.start_presenting()

        else:
            self.isPresenting = False
            self.btnStart.setEnabled(False)
            self.presenting.stop()

    # -- Checkbox Actions -- #
    def set_eyetracking(self):
        if self.chkbxEyeTracking.isChecked():
            self.useEyetracking = True
            self.lbAnimalID.setEnabled(True)
            self.cbAnimalName.setEnabled(True)
            self.lbCameraID.setEnabled(True)
            self.cbCameraID.setEnabled(True)
            self.btnSelectROI.setEnabled(True)
            self.btnStart.setEnabled(False)
        else:
            self.useEyetracking = False
            self.lbAnimalID.setEnabled(False)
            self.cbAnimalName.setEnabled(False)
            self.lbCameraID.setEnabled(False)
            self.cbCameraID.setEnabled(False)
            self.btnSelectROI.setEnabled(False)
            self.btnStart.setEnabled(True)

    # -- ROI Sequence -- #
    def selectROI(self):
        """Creates an ROI selection sequence. Returns vertices of ROI rectangle and seed point for feature
        finder. Sets the ROI in Feature Finder and creates the calibrator camera instance.
        """
        if self.cameraID == "None":
            print "An eye tracking camera must be installed. Select an eye tracking camera."
            pass
        else:
            get_roi = ROISelect(self.cameraID)
            get_roi.findROI()
            self.verticesROI, self.ROI_diff, pupil, cr, self.ellipse = get_roi.getData()

            if pupil != []:
                self.guess["pupil_position"] = [pupil[0][0], pupil[0][1]]

            if cr != []:
                self.guess["cr_position"] = [cr[0][0], cr[0][1]]

            self.setROI = True
            del get_roi
            self.txtUpdates.append('ROI selected')
            self.btnStart.setEnabled(True)

    # -- Menu Actions -- #
    def quit(self):
        if self.presenting is not None:
            self.presenting.stop()
            time.sleep(0.5)     # wait for everything to wrap up nicely
        os.remove('data.pkl')
        self.close()

    def closeEvent(self, event):
        # Overrides the PyQt function of the same name, so you can't rename this.
        # Happens when user clicks "X".
        self.quit()
        event.accept()

    # -- Startup sequence -- #
    def start_presenting(self):
        self.presenting = Presenting(self)
        self.presenting.start()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    myWindow = StimTracking(None)
    myWindow.show()
    app.exec_()  # do not change to sys.exit(app.exec_()). This will quit the program without shutting things down nicely or saving the data!!!!

