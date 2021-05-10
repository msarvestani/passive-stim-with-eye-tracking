from psychopy import visual, logging, core, monitors
import pylab, math, serial, sys, numpy
sys.path.append("../triggers") #path to trigger classes
from os import path

#---------- Monitor Properties ----------#
mon= monitors.Monitor('madinehMonitor') #gets the calibration for stimMonitor
mon.setDistance(20)
overwriteGammaCalibration=False
newGamma=0.479

#time parameters
numberOfTrials = 30; # how many trials
movementPeriod = 4; #how long it takes for a bar to move from startPoint to endPoint
initialDelay = 0; # time in seconds to wait before first stimuli. Set to 0 to begin ASAP. 3
#bar parameters
animalOrientation=-30
stimID = 1; # uses driftGrating standard (1 - Horizontal Bar (Drifting Down), 5 - Horizontal Bar (Drifting Up), 3 - Vertical Bar (Drifting Left), 7 - Vertical Bar (Drifting Right)
orientation =animalOrientation+(stimID-1)*45+180 #0 is horizontal, 90 is vertical. 45 goes from up-left to down-right.
barColor = 0; #1 for white, 0 for black, 0.5 for low contrast white, etc.

#position parameters
centerPoint = [-20,0] #center of screen is [0,0] (degrees).
startPoint = -35; #bar starts this far from centerPoint (in degrees)
endPoint = 35; #bar moves to this far from centerPoint (in degrees)
stimSize = (180,4) # (180,4) #First number is longer dimension no matter what the orientation is. - typically is (180,4)

#flashing parameters
flashPeriod = 0.4 #0.2 #amount of time it takes for a full cycle (on + off). Set to 1 to get static drifting bar (no flash). 
dutyCycle = 1 #0.5 #Amount of time flash bar is "on" vs "off". 0.5 will be 50% of the time. Set to 1 to get static drifting bar (no flash). 

#Experiment logging parameters
dataPath='x:/'
animalName='TSmax1410';
logFilePath =dataPath+animalName+'\\'+animalName+'.txt' #including filepath

# ---------- Stimulus code begins here ---------- #
stimCodeName=path.dirname(path.realpath(__file__))+'\\'+path.basename(__file__)

#Triggering type
#Can be any of:#"NoTrigger" - no triggering; stim will run freely
#"SerialDaqOut" - Triggering by serial port. Stim codes are written to the MCC DAQ.
# "OutOnly" - no input trigger, but does all output (to CED) and logging
#"DaqIntrinsicTrigger" - waits for stimcodes on the MCC DAQ and displays the appropriate stim ID
triggerType = 'SerialDaqOut';
#triggerType = 'NoTrigger';
serialPortName = 'COM1' # ignored if triggerType is "None"
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
#    trigger.preTrialLogging([dataPath,animalName,expName,stimCodeName,stimID,logFilePath])
elif triggerType=="DaqIntrinsicTrigger":
    import daqIntrinsicTrigger
    trigger = daqIntrinsicTrigger.daqIntrinsicTrigger(None) 
else:
    print "Unknown trigger type", triggerType


#make a window
mywin = visual.Window(monitor=mon,fullscr=True,screen=1)
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
duration=numberOfTrials*movementPeriod #in seconds
print("Stim Duration is "+str(duration)+" seconds")
currentTrial=0
clock.reset()
while clock.getTime()<duration:
    # output trigger at the beginning of every trial
    if clock.getTime()>=currentTrial*movementPeriod:
        currentTrial=currentTrial+1;
        print("Trial "+str(currentTrial))
        trigger.preStim(stimID)
        trigger.preFlip(None)
        mywin.flip()
        trigger.postFlip(None)
        trigger.postStim(None)
    
    posLinear = (clock.getTime() % movementPeriod) / movementPeriod * (endPoint-startPoint) + startPoint; #what pos we are at in degrees
    if (clock.getTime()/flashPeriod) % (1.0) < dutyCycle:
        barStim.setContrast(1)
    else:
        barStim.setContrast(0)
    posX = posLinear*math.sin(orientation*math.pi/180)+centerPoint[0]
    posY = posLinear*math.cos(orientation*math.pi/180)+centerPoint[1]
    barStim.setPos([posX,posY])
    mywin.flip()
   
print clock.getTime()
    