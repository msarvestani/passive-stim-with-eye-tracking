from psychopy import visual, logging, core, monitors
import pylab, math, random, serial, numpy, time, imp, sys
sys.path.append("../triggers") #path to trigger classes
from os import path

#---------- Monitor Properties ----------#
mon= monitors.Monitor('stimMonitor') #gets the calibration for stimMonitor 
mon.setDistance(20)
overwriteGammaCalibration=False
newGamma=0.479

#time parameters
numberOfTrials = 11; # how many trials
numberOfPositions = 15; #how many bars
stimulusPeriod = 2; #how long it takes for a bar to move from startPoint to endPoint
blankPeriod = 2; #5 time in seconds to wait before first stimuli. Set to 0 to begin ASAP. 
initialDelay=0; # initial delay in seconds
isRandom =0; # is random

#bar parameters
animalOrientation=0;
stimID = 7; # uses driftGrating standard (1 - Horizontal Bar (Drifting Down), 5 - Horizontal Bar (Drifting Up), 3 - Vertical Bar (Drifting Left), 7 - Vertical Bar (Drifting Right)
orientation =animalOrientation+(stimID-1)*45+180 #0 is horizontal, 90 is vertical. 45 goes from up-left to down-right.
barColor = 0; #1 for white, 0 for black, 0.5 for gray, 0 for black, etc.
backGroundColor = 0.5; #1 for white, 0 for black, 0.5 for gray, 0 for black, etc.

#position parameters
centerPoint = [0,0] #center of screen is [0,0] (degrees).
startPoint = -15; #bar starts this far from centerPoint (in degrees)
endPoint = 15; #bar moves to this far from centerPoint (in degrees)
stimSize = (180,2) # (180,4) #First number is longer dimension no matter what the orientation is. - typically is (180,4)

#flashing parameters
flashPeriod = 0.4 #0.2 #amount of time it takes for a full cycle (on + off). Set to 1 to get static drifting bar (no flash). 
dutyCycle = 0.5 #0.5 #Amount of time flash bar is "on" vs "off". 0.5 will be 50% of the time. Set to 1 to get static drifting bar (no flash). 

#Experiment logging parameters
dataPath='x:/'
animalName='F1654_2014-05-09';
logFilePath =dataPath+animalName+'\\'+animalName+'.txt' #including filepath

# ---------- Stimulus code begins here ---------- #
stimCodeName=path.dirname(path.realpath(__file__))+'\\'+path.basename(__file__)

#Triggering type
#Can be any of:#"NoTrigger" - no triggering; stim will run freely
#"SerialDaqOut" - Triggering by serial port. Stim codes are written to the MCC DAQ.
# "OutOnly" - no input trigger, but does all output (to CED) and logging
#"DaqIntrinsicTrigger" - waits for stimcodes on the MCC DAQ and displays the appropriate stim ID
#triggerType = 'DaqIntrinsicTrigger'
triggerType = 'NoTrigger';
serialPortName = 'COM3' # ignored if triggerType is "None"
adjustDurationToMatch2P=True

#Set up the trigger behavior
trigger = None
if triggerType == "NoTrigger":
    import noTrigger
    trigger = noTrigger.noTrigger(None) 
elif triggerType == "SerialDaqOut" or triggerType == 'OutOnly':
    import serialTriggerDaqOut
    print 'Imported trigger serialTriggerDaqOut'
    trigger = serialTriggerDaqOut.serialTriggerDaqOut(serialPortName) 
    # determine the Next experiment file name
    expName=trigger.getNextExpName([dataPath,animalName])
    print "Trial name: ",expName
    if triggerType == 'OutOnly':
        trigger.readSer=False
    #Record a bunch of serial triggers and fit the stim  to an exact multiple of the trigger time
    if adjustDurationToMatch2P:
        print "Waiting for serial Triggers"
        movementPeriod = trigger.extendStimDurationToFrameEnd(movementPeriod)
    # store the stimulus data and prepare the directory
    trigger.preTrialLogging([dataPath,animalName,expName,stimCodeName,stimID,logFilePath])
elif triggerType=="DaqIntrinsicTrigger":
    import daqIntrinsicTrigger
    trigger = daqIntrinsicTrigger.daqIntrinsicTrigger(None) 
else:
    print "Unknown trigger type", triggerType


#make a window
#backGroundColor = (2*backGroundColor-1)*numpy.ones([3,1,1]);
mywin = visual.Window(monitor=mon,fullscr=True,screen=1,rgb=backGroundColor)
if overwriteGammaCalibration:
    myWin.setGamma(newGamma)
    print "Overwriting Gamma Calibration. New Gamma value:",newGamma

#create bar stim
#barTexture = numpy.ones([256,256,3])*barColor;
barTexture = numpy.ones([256,256,3]);
barStim = visual.PatchStim(win=mywin,tex=barTexture,mask='none',units='deg',pos=centerPoint,size=stimSize,ori=orientation)
barStim.setContrast(0)
barStim.setAutoDraw(True)
barStim.setColor(barColor*255, 'rgb255')

# wait for an initial delay
clock = core.Clock()
if initialDelay>0:
    print" waiting "+str(initialDelay)+ " seconds before starting stim to acquire a baseline."
    while clock.getTime()<initialDelay:
        mywin.flip()

#run
currentTrial=0
for trial in range(0,numberOfTrials): 
    #determine stim order
    print "Beginning Trial",trial+1
    stimOrder = range(0,numberOfPositions)
    if isRandom:
        random.shuffle(stimOrder)
    for stimNumber in stimOrder:
        #display each stim
        print "     Stim",stimNumber+1
        clock.reset()

        startTrialFlag = 1
        while clock.getTime()< stimulusPeriod:
            if startTrialFlag:
                # output trigger at the beginning of every trial
                trigger.preStim(stimNumber)
                trigger.preFlip(None)
                mywin.flip()
                trigger.postFlip(None)
                trigger.postStim(None)
                startTrialFlag = 0
                
            posLinear = (stimNumber / float(numberOfPositions))* (endPoint-startPoint) + startPoint;
            if (clock.getTime()/flashPeriod) % (1.0) < dutyCycle:
                barStim.setContrast(1)
                barStim.setColor(barColor*255, 'rgb255')
            else:
                #barStim.setContrast(0)
                barStim.setColor((1-barColor)*255, 'rgb255')
            posX = posLinear*math.sin(orientation*math.pi/180)+centerPoint[0]
            posY = posLinear*math.cos(orientation*math.pi/180)+centerPoint[1]
            barStim.setPos([posX,posY])
            mywin.flip()

        clock.reset()
        while clock.getTime()< blankPeriod:
            #barStim.setContrast(0)
            barStim.setPos([10000,10000])
            mywin.flip()
                       
trigger.wrapUp([logFilePath, expName])
print 'Finished all stimuli.'
