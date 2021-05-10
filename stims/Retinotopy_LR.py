from psychopy import visual, logging, core, filters, event, monitors, tools
import pylab, math, random, numpy, time, imp, sys, itertools
sys.path.append('C:/Users/fitzlab1/Documents/psychopy/Madineh/python3/triggers')
from os import path
import os
import fileinput

print("initialized")


# ---------- Stimulus Description ---------- #
'''A fullscreen drifting grating for 2pt orientation tuning'''
#---------- Monitor Properties ----------#
#---------- Monitor Properties ----------#
mon= monitors.Monitor(name='madinehMonitor') #gets the calibration for stimMonitor
mon.setSizePix((1920, 1080))
mon.setWidth(62)
mon.setDistance(25)
monitorSize=[1920,1080]
myWin = visual.Window(size=monitorSize,monitor=mon,fullscr=True,screen=1, allowGUI=False, waitBlanking=True,units='deg',
                      allowStencil=True)

#Experiment logging parameters
animalID = 'Mel'
dataPath='Y:'
animalName=animalID

fileinput.close()
exp_num_file = dataPath + 'instruction.txt'
if os.path.isfile(exp_num_file):
    for line in fileinput.input(exp_num_file):
        line = line.rstrip()
        toks = line.split(' ')
expName = toks[0]

logFilePath =dataPath+'\\'+expName+'.txt' #including filepath
print logFilePath

Direction ='right'

#time parameters
numberOfTrials = 30; # how many trials
movementPeriod = 6; #how long it takes for a bar to move from startPoint to endPoint
initialDelay = 0; # time in seconds to wait before first stimuli. Set to 0 to begin ASAP. 
ISI=3

#position parameters
#position parameters
centerPoint = [0,0] #center of screen is [0,0] (degrees).
stimSize = (380,4) # (180,4) #First number is longer dimension no matter what the orientation is. - typically is (180,4)
startPointR = -10#this is  ipsilateral hemisphere
endPointR = 35 #this is contralateral hemisphere

if Direction == 'right':
    stimID = 7
    startPoint=startPointR
    endPoint=endPointR

elif Direction == 'left':
    stimID =3
    startPoint=-endPointR
    endPoint=-startPointR

#bar parameters
animalOrientation=0;
#stimID = 1; # uses driftGrating standard (1 - Horizontal Bar (Drifting Down), 5 - Horizontal Bar (Drifting Up), 3 - Vertical Bar (Drifting Left), 7 - Vertical Bar (Drifting Right)
# uses driftGrating standard (1 - Horizontal Bar (Drifting Down), 5 - Horizontal Bar (Drifting Up), 3 - Vertical Bar (Drifting Left), 7 - Vertical Bar (Drifting Right)
orientation =animalOrientation+(stimID-1)*45+180 #0 is horizontal, 90 is vertical. 45 goes from up-left to down-right.
barColor = 0; #1 for white, 0 for black, 0.5 for low contrast white, etc.



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
#triggerType ='SerialDaqOut'
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
    print('Imported trigger serialTriggerDaqOut')
    trigger = serialTriggerDaqOut.serialTriggerDaqOut(serialPortName) 
    # determine the Next experiment file name
    #7expName=trigger.getNextExpName([dataPath,animalName])
    print("Trial name: ",expName)
    if triggerType == 'OutOnly':
        trigger.readSer=False
    #Record a bunch of serial triggers and fit the stim  to an exact multiple of the trigger time
    if adjustDurationToMatch2P:
        print("Waiting for serial Triggers")
        movementPeriod = trigger.extendStimDurationToFrameEnd(movementPeriod)
    # store the stimulus data and prepare the directory
    trigger.preTrialLogging([dataPath,animalName,expName,stimCodeName,stimID,logFilePath])
elif triggerType=="DaqIntrinsicTrigger":
    import daqIntrinsicTrigger
    trigger = daqIntrinsicTrigger.daqIntrinsicTrigger(None) 
else:
    print("Unknown trigger type", triggerType)



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
    print(" waiting "+str(initialDelay)+ " seconds before starting stim to acquire a baseline.")
    while clock.getTime()<initialDelay:
        myWin.flip()

#run
duration=numberOfTrials*movementPeriod #in seconds
print(("Stim Duration is "+str(duration)+" seconds"))
currentTrial=0
clock.reset()

for trial in range(0,numberOfTrials):
    currentTrial = currentTrial + 1;
    print(("Trial " + str(currentTrial)))
    clock.reset()
    trigger.preStim(stimID)
    trigger.preFlip(None)
    while clock.getTime() < movementPeriod:
        # output trigger at the beginning of every trial
        posLinear = (clock.getTime() % movementPeriod) / movementPeriod * (endPoint-startPoint) + startPoint; #what pos we are at in degrees
        posX = posLinear*math.sin(orientation*math.pi/180)+centerPoint[0]
        posY = posLinear*math.cos(orientation*math.pi/180)+centerPoint[1]
        barStim.setPos([posX,posY])
        barStim.setContrast(1)
        myWin.flip()
        trigger.postStim(None)
        trigger.postFlip(None)

    # now do ISI
    clock.reset()
    barStim.setContrast(0)
    myWin.flip()
    while clock.getTime() < ISI:
        # Keep flipping during the ISI. If you don't do this you can get weird flash artifacts when you resume flipping later.
        myWin.flip()

trigger.wrapUp()
