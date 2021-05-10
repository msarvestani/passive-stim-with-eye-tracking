#Hartley subspace_Kuo
"""
This is for reverse correaltion experiment with Hartley subspace  %% Seq file name is on line 190
"""
from __future__ import division  # so that 1/3=0.333 instead of 1/3=0
from psychopy import visual, core, data, event, logging, sound, gui, filters, monitors
from psychopy.constants import *  # things like STARTED, FINISHED
import numpy as np  # whole numpy lib is available, prepend 'np.'
from numpy import sin, cos, tan, log, log10, pi, average, sqrt, std, deg2rad, rad2deg, linspace, asarray
from numpy.random import random, randint, normal, shuffle
import pylab, math, random, numpy, time, imp, sys
import os, random  # handy system and path functions
sys.path.append("../triggers") #path to trigger classes
from os import path
from array import array
import csv
print "initialized"

#---------- Monitor Properties ----------##
mon= monitors.Monitor('stim2') #gets the calibration for stimMonitor
mon.setDistance(20)

# ---------- Stimulus Parameters ---------- ##
timepertrial = 0.2 # Duration for tiral, stimulus and ISI # 26s for single trial
stitime = 0.19
# ISItime = 0.5
Trinumber = 80 #repeat #Run all the stims this many times
Imasize = [300, 300] # size of image by pix
centerPoint = [0,0] 

# Set the random sequence
items = range(1,8001) #For 512 images
random.shuffle(items) # randomize the sequence
cc=-1
# Store info about the experiment session
expName1 = u'trials'  # from the Builder filename that created this script
expInfo = {u'session': u'001', u'participant': u''}
expInfo['date'] = data.getDateStr()  # add a simple timestamp
expInfo['expName'] = expName1

#Triggering type
#Can be any of:
# "NoTrigger" - no triggering; stim will run freely
# "SerialDaqOut" - Triggering by serial port. Stim codes are written to the MCC DAQ.
# "OutOnly" - no input trigger, but does all output (to CED) and logging
# "DaqIntrinsicTrigger" - waits for stimcodes on the MCC DAQ and displays the appropriate stim ID
#<<<<<<< HEAD I don't know what is it?
triggerType = 'OutOnly' #'NoTrigge' 
serialPortName = 'COM1' # ignored if triggerType is "None"
adjustDurationToMatch2P=0

#Experiment logging parameters##########
dataPath='y:/'
animalName='F1642_2014-05-14';
logFilePath =dataPath+animalName+'\\'+animalName+'.txt' #including filepath
#=======
#triggerType = 'OutOnly'
#serialPortName = 'COM1' # ignored if triggerType is "None"
#adjustDurationToMatch2P=True
#
#dataPath='G:/Data'
#>>>>>>> 5a32817238385507c65f3723f961d93640bd44f6
#animalName='FXXXX_2014-05-05';
#logFilePath =dataPath+animalName+'\\'+animalName+'.txt' #including filepath
#Experiment logging parameters##########

# Setup files for saving
if not os.path.isdir('C:/Users/fitzlab1/Documents/psychopy/Dan/kuo/data'):
    os.makedirs('C:/Users/fitzlab1/Documents/psychopy/Dan/kuo/data')  # if this fails (e.g. permissions) we will get error
filename = 'C:/Users/fitzlab1/Documents/psychopy/Dan/kuo/data' + os.path.sep + '%s_%s' %(expInfo['participant'], expInfo['date'])
logFile = logging.LogFile(filename+'.log', level=logging.EXP)
logging.console.setLevel(logging.WARNING)  # this outputs to the screen, not a file

# An ExperimentHandler
thisExp = data.ExperimentHandler(name=expName1, version='',
    extraInfo=expInfo, runtimeInfo=None,
    originPath=None,
    savePickle=True, saveWideText=True,
    dataFileName=filename)

# ---------- Stimulus code begins here ---------- #
stimCodeName=path.dirname(path.realpath(__file__))+'\\'+path.basename(__file__)

# Setup the Window
win = visual.Window(size=[1000, 1000], monitor=mon, fullscr=True, screen=1, allowGUI=True, allowStencil=False,
    color=[0,0,0], colorSpace=u'rgb', waitBlanking=True)
# store frame rate of monitor if we can measure it successfully
expInfo['frameRate']=win.getActualFrameRate()
if expInfo['frameRate']!=None:
    frameDur = 1.0/round(expInfo['frameRate'])
else:
    frameDur = 1.0/60.0 # couldn't get a reliable measure so guess

win.setGamma(.479) #print myWin.gamma
print "made window, setting up triggers"

#Set up the trigger behavior
trigger = None
if triggerType == 'NoTrigger':
    import noTrigger
    trigger = noTrigger.noTrigger(None) 
elif triggerType == 'SerialDaqOut' or triggerType == 'OutOnly':
    import serialTriggerDaqOut
    print 'Imported trigger serialTriggerDaqOut'
    trigger = serialTriggerDaqOut.serialTriggerDaqOut(serialPortName) 
    if triggerType == 'OutOnly':
        trigger.readSer=False
    #Record a bunch of serial triggers and fit the stim duration to an exact multiple of the trigger time
    if adjustDurationToMatch2P:
        stimDuration = trigger.extendStimDurationToFrameEnd(stimDuration)
    # determine the Next experiment file name
    expName=trigger.getNextExpName([dataPath,animalName])
    print "Trial name: ",expName
    # store the stimulus data and prepare the directory
    #trigger.preTrialLogging([dataPath,animalName,expName,stimCodeName,orientations,logFilePath])
elif triggerType=="DaqIntrinsicTrigger":
    import daqIntrinsicTrigger
    trigger = daqIntrinsicTrigger.daqIntrinsicTrigger(None) 
else:
    print "Unknown trigger type", triggerType
        
#print stimDuration
#changeDirectionTimeAt = stimDuration * changeDirectionAt

barTexture = numpy.ones([256,256,3]);
flipStim = visual.PatchStim(win=win,tex=barTexture,mask='none',units='pix',pos=[-920,500],size=(100,100))
flipStim.setAutoDraw(True)#up left, this is pos in y, neg in x
clrctr=1;
print "made stimulus ensemble"

initialDelay=3
clock=core.Clock()
if initialDelay>0:
    print" waiting "+str(initialDelay)+ " seconds before starting stim to acquire a baseline."
    flipStim.setContrast(1)
    while clock.getTime()<initialDelay:
        win.flip()

clock.reset()

# Initialize components for Routine "trial"
trialClock = core.Clock()
print "\n", ";-)", "stims will be run for",str(Trinumber),"trials."
ISI = core.StaticPeriod(win=win, screenHz=expInfo['frameRate'], name='ISI')
image = visual.ImageStim(win=win, name='image',units=u'pix', 
    image='sin', mask=None,
    ori=0, pos=[40, -40], size=Imasize,
    color=[1,1,1], colorSpace=u'rgb', opacity=1,
    texRes=128, interpolate=True, depth=-1.0)

# Create some handy timers
globalClock = core.Clock()  # to track the time since experiment started
routineTimer = core.CountdownTimer()  # to track time remaining of each (non-slip) routine 

# set up handler to look after randomisation of conditions etc
trials = data.TrialHandler(nReps=Trinumber, method=u'random', 
    extraInfo=expInfo, originPath=None,
    trialList=data.importConditions(u'condition.xlsx'),
    seed=None, name='trials') # nReps*Conditions will be the time of repeats
thisExp.addLoop(trials)  # add the loop to the experiment
thisTrial = trials.trialList[0]  # so we can initialise stimuli with some values
# abbreviate parameter names if possible (e.g. rgb=thisTrial.rgb)
a=[]
if thisTrial != None:
    for paramName in thisTrial.keys():
        exec(paramName + '= thisTrial.' + paramName)

for thisTrial in trials:
    currentLoop = trials
    
    #modified by Kuo on 5/12 !!
    trialClock.reset()
    #trigger.waitForSerial(); # Gordan 5/12
    trigger.preStim(1)
    flipStim.setAutoDraw(True)
    #didn't do the flip contrast change like: flipStim.setColor((0,0,0),colorSpace='rgb')
    flipStim.setContrast(1)
        
    cc = cc+1 # sequence begins here
    if cc > 7999:
        random.shuffle(items)
        cc=cc%8000
    
    # abbreviate parameter names if possible (e.g. rgb = thisTrial.rgb)
    if thisTrial != None:
        for paramName in thisTrial.keys():
            exec(paramName + '= thisTrial.' + paramName)
    #------Prepare to start Routine "trial"-------
    t = 0
    #trialClock.reset()  # clock 5/12
    frameN = -1
    routineTimer.add(timepertrial)
    # update component parameters for each repeat
    aa=items[cc]
    
    print aa # 5/14
    # 5/14 output stimulus sequence to excel
    a.extend([[aa]])
    fl = open('WNJoeSeq.csv', 'w')
    writer = csv.writer(fl)
    # writer.writerow(['label1']) #if needed
    for values in a:
        writer.writerow(values)

    Iname='C:/Users/fitzlab1/Documents/psychopy/Gordon/episodicStims/WaveletStims/tiffDir_GaussWN/wn'+str(1)+'_' + '{:04.0f}'.format(aa+1)+ '.tif'
    image.setImage(Iname)
    # keep track of which components have finished
    trialComponents = []
    trialComponents.append(ISI)
    trialComponents.append(image)
    for thisComponent in trialComponents:
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    
    #-------Start Routine "trial"-------
    continueRoutine = True
    while continueRoutine and routineTimer.getTime() > 0:
        # get current time
        t = trialClock.getTime()
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *image* updates
        if t >= 0.0 and image.status == NOT_STARTED:
            # keep track of start time/frame for later
            image.tStart = t  # underestimates by a little under one frame
            image.frameNStart = frameN  # exact frame index
            image.setAutoDraw(True)
        elif image.status == STARTED and t >= (0.0 + stitime):
            image.setAutoDraw(False)
        # *ISI* period
        if t >= stitime and ISI.status == NOT_STARTED:
            # keep track of start time/frame for later
            ISI.tStart = t  # underestimates by a little under one frame
            ISI.frameNStart = frameN  # exact frame index
            ISItime = timepertrial - t # 5/9
            ISI.start(ISItime)
        elif ISI.status == STARTED: #one frame should pass before updating params and completing
            ISI.complete() #finish the static period
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            routineTimer.reset()  # if we abort early the non-slip timer needs reset
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in trialComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        flipStim.setContrast(0)
        
        # check for quit (the [Esc] key)
        if event.getKeys(["escape"]):
            core.quit()
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            trigger.preFlip(None)
            win.flip()
            trigger.postFlip(None)    
            
    #-------Ending Routine "trial"-------
    for thisComponent in trialComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    thisExp.nextEntry()
    trigger.postStim(None)

    
# completed 512 repeats of 'trials'
# trigger.wrapUp([logFilePath, expName])
print 'Finished all stimuli.'

# get names of stimulus parameters
if trials.trialList in ([], [None], None):  params = []
else:  params = trials.trialList[0].keys()
# save data for this loop
trials.saveAsExcel(filename + 'trials'+ '.xlsx', sheetName='trials',
    stimOut=params,
    dataOut=['n','all_mean','all_std', 'all_raw']) #[params, items]
win.close()
core.quit()
