# presenting.py: Visual Stim Control Center
# Author: Matthew McCann (@mkm4884)
# Max Planck Florida Institute for Neuroscience
# Created: 12/02/2016
# Last Modified: 12/08/2016

# Description: Main loop where stimulus presentation and video recording are initiated.
# The stimulus window is

import time
import threading
import random
from subprocess import PIPE, Popen
from Queue import Queue
import os
import fileinput
import cPickle as pkl
import sys

sys.path.append('..')

from stim_with_eyetracking import *


class Presenting:

    def __init__(self, parent):
        self.Parent = parent

        # Make subprocess to run stim file without needing to modify stim file structure
        self.stim_file = str(self.Parent.stimPathFull)
        self.working_dir = str(self.Parent.baseStimPath)
        self.experimentPath = self.Parent.experimentPath
        self.trialNum = self.Parent.trialNum
        self.animalName = self.Parent.animalName

        # ------------------------------------------------------------
        # Eye tracking setup
        # ------------------------------------------------------------

        self.useCam = self.Parent.useCam

        if self.useCam:
            self.fullGazeTracking = self.Parent.fullGazeTracking

            # get information from Parent
            self.cameraID = self.Parent.cameraID
            self.ROI = self.Parent.verticesROI

            # create pkl file to send data to the eye tracking subprocess
            data = self.Parent.guess.copy()
            data['ellipse'] = self.Parent.ellipse
            data['cameraID'] = self.cameraID
            data['ROI'] = self.ROI
            data['animalID'] = self.animalName
            data['basepath'] = self.Parent.baseDataPath
            data['session_path'] = self.experimentPath
            pkl_file = open('data.pkl', 'wb')
            pkl.dump(data, pkl_file)
            pkl_file.close()

            # Start feature finder
            sys.stdout.flush()
            self.fitPreview = subprocess.Popen([sys.executable, 'ui/preview_fit.py', '--called'], cwd=self.Parent.workingDir)
            time.sleep(1)

        # ------------------------------------------------------------
        # Optogenetics Initialization
        # ------------------------------------------------------------
        self.useOpto = self.Parent.useOpto
        if self.useOpto:
            # start opto stuff
            print "Starting Opto LED Controller"
            sys.stdout.flush()
            # Talk to the subprocess through pipes
            self.optoController = subprocess.Popen([sys.executable, 'devices/opto_generator.py', '--called'], cwd=self.Parent.workingDir,
                                                   stdin=PIPE)
            time.sleep(1)

        # ------------------------------------------------------------
        # Stimulus Initialization
        # ------------------------------------------------------------
        # Start psychopy subprocess
        print 'Starting ' + self.stim_file
        sys.stdout.flush()
        self.visStim = Popen(['python', self.stim_file, self.experimentPath, '--called'], cwd=self.working_dir, stdout=PIPE)
        print self.visStim.stdout.readline().rstrip()        # <-- listen to confirm window starts
        self.visStim.stdout.flush()

        # get some stuff set up for the opto stimulus
        if self.useOpto:
            stim_cmd = self.visStim.stdout.readline().rstrip()
            stim_cmd = stim_cmd.strip('cmd ') + '\n'
            self.optoController.stdin.writelines(stim_cmd)

    def main_loop(self):
        # Here is where the magic is
        while not self.stopFlag:
        # Run only if subprocess is still running
            if self.stopFlag:
                self.stop()
            else:
                stim_cmd = self.visStim.stdout.readline().rstrip()        # blocking
                if self.useOpto and 'cmd' in stim_cmd:
                    # parse the output into something the opto controller can understan
                    stim_cmd = stim_cmd.strip('cmd ') + '\n'
                    self.optoController.stdin.writelines(stim_cmd)
                else:
                    print stim_cmd

    def start(self):
        # threading /  main loop stuff goes here
        self.stopFlag = False
        thread = threading.Thread(target=self.main_loop)
        thread.daemon = True
        thread.start()

    def stop(self):
        self.stopFlag = True
        # If subprocess is still running
        if self.visStim.poll() is None:
            self.visStim.kill()
        if self.fitPreview.poll() is None:
            self.fitPreview.terminate()
        # if self.optoController.poll() is None:
        #     stim_cmd = 'kill0 \n'
        #     self.optoController.stdin.writelines(stim_cmd)
        #     time.sleep(1)
        #     self.optoController.terminate()

