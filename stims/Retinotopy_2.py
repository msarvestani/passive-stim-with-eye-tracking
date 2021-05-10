from psychopy import visual, logging, core, filters, event, monitors, tools
import pylab, math, random, numpy, time, imp, sys, itertools
sys.path.append("../triggers") #path to trigger classes
sys.path.append("C:/Users/fitzlab1/Documents/psychopy/Dan/triggers") #path to trigger clases
from os import path
print "initialized"

#Experiment logging parameters
animalID = 'Ami'
dataPath='C:/Data/'
animalName='Ami'
expName='test'
logFilePath =dataPath+'\\'+expName+'.txt' #including filepath


# ---------- Stimulus Description ---------- #
'''A fullscreen drifting grating for 2pt orientation tuning'''
#---------- Monitor Properties ----------#
mon= monitors.Monitor('stimMonitor') #gets the calibration for stimMonitor
mon.setDistance(20) 
myWin = visual.Window(size=mon.getSizePix(),monitor=mon,fullscr=True,screen=1, allowGUI=False, waitBlanking=True)

#time parameters
numberOfTrials = 40; # how many trials
movementPeriod =8; #how long it takes for a bar to move from startPoint to endPoint
initialDelay = 0; # time in seconds to wait before first stimuli. Set to 0 to begin ASAP. 

#bar parameters
animalOrientation=0;
#stimID = 1; # uses driftGrating standard (1 - Horizontal Bar (Drifting Down), 5 - Horizontal Bar (Drifting Up), 3 - Vertical Bar (Drifting Left), 7 - Vertical Bar (Drifting Right)
stimID =3
# uses driftGrating standard (1 - Horizontal Bar (Drifting Down), 5 - Horizontal Bar (Drifting Up), 3 - Vertical Bar (Drifting Left), 7 - Vertical Bar (Drifting Right)
orientation =animalOrientation+(stimID-1)*45+180 #0 is horizontal, 90 is vertical. 45 goes from up-left to down-right.
barColor = 0; #1 for white, 0 for black, 0.5 for low contrast white, etc.

#position parameters
#position parameters
centerPoint = [0,0] #center of screen is [0,0] (degrees).
startPoint = -70; #bar starts this far from centerPoint (in degrees)
endPoint = 70; #bar moves to this far from centerPoint (in degrees)
stimSize = (380,6) # (180,4) #First number is longer dimension no matter what the orientation is. - typically is (180,4)

#flashing parameters
flashPeriod =1#0.2 #amount of time it takes for a full cycle (on + off). Set to 1 to get static drifting bar (no flash).
dutyCycle = 1 #0.5 #Amount of time flash bar is "on" vs "off". 0.5 will be 50% of the time. Set to 1 to get static drifting bar (no flash).

# ---------- Stimulus code begins here ---------- #
stimCodeName=path.dirname(path.realpath(__file__))+'\\'+path.basename(__file__)

#Triggering type
#Can be any of:#"NoTrigger" - no triggering; stim will run freely
#"SerialDaqOut" - Triggering by serial port. Stim codes are written to the MCC DAQ.
# "OutOnly" - no input trigger, but does all output (to CED) and logging
#"DaqIntrinsicTrigger" - waits for stimcodes on the MCC DAQ and displays the appropriate stim ID
triggerType = 'OutOnly';
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
    #trigger.preTrialLogging([dataPath,animalName,expName,stimCodeName,stimID,logFilePath])
elif triggerType=="DaqIntrinsicTrigger":
    import daqIntrinsicTrigger
    trigger = daqIntrinsicTrigger.daqIntrinsicTrigger(None) 
else:
    print "Unknown trigger type", triggerType


#create bar stim
#barTexture = numpy.ones([256,256,3])*barColor;
barTexture = numpy.ones([256,256,3]);
barStim = visual.PatchStim(win=myWin,tex=barTexture,mask='none',units='deg',pos=centerPoint,size=stimSize,ori=orientation)
barStim.setContrast(0)
barStim.setAutoDraw(True)
barStim.setColor(barColor*255, 'rgb255')
RFstim = visual.PatchStim(myWin,pos=(25,22), units = 'deg',
                           tex="sin",mask="circle", #"gauss"
                           size=(0.0,0.0), sf=(0.3), ori=22.5*0,  depth=0, opacity=1.0,
                           autoLog=False)#this stim changes too much for autologging to work 'sqr', 'saw', 'tri'
RFstim.setContrast(0)
RFstim.setAutoDraw(True)
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
        myWin.flip()
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
    myWin.flip()
   
print clock.getTime()
    