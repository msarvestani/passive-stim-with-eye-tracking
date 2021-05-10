from psychopy import visual, logging, core, filters, event, monitors
import pylab, math, random, numpy, time, imp, sys
sys.path.append("../triggers") #path to trigger classes
from os import path

# ---------- Stimulus Description ---------- #
'''A fullscreen drifting grating for 2pt orientation tuning'''
#---------- Monitor Properties ----------#
mon= monitors.Monitor('stimMonitor') #gets the calibration for stimMonitor
frameRate = 120 # not used
mon.setDistance(18)

# ---------- Stimulus Parameters ---------- #
#trials and duration
numOrientations = 8 #typically 4, 8, or 16
CenterOrientations=180  #+15
CenterOrientations=CenterOrientations-90
#orientations = numpy.arange(0.0,1,float(1)/numOrientations) #Remember, ranges in Python do NOT include the final value!
#orientations=[160,162.5,165,167.5,170]
#orientations=[20,22.5,25,27.5,30]
orientations=[0,0.15,0.4,0.5,0.5,0.6,0.85,1]
orientations=[0,0.05,0.1,0.5,0.5,0.9,0.95,1]
numTrials = 10 #Run all the stims this many times 
pauseBetweenTrials = 0 # Wait for user to press space bar in between trials
doBlank = 1 #0 for no blank stim, 1 to have a blank stim. The blank will have the highest stimcode.
stimDuration = 2 #stimulus duration in seconds; will be adjusted if adjustDurationToMatch2P=1
isMoving = 1 # 1 for moving stimulus, 0 for stationary
changeDirectionAt = 1 #When do we change movement directions? If 1, there should be no reversal.  If 0.5, then movement reverses directions at stimDuration/2
isi = 4 # Kuo 4 to 2
isRandom = 1
# Grating parameter
temporalFreq = 4
spatialFreq = 0.15
contrast = 1
textureType = 'sqr' #'sqr' = square wave, 'sin' = sinusoidal
startingPhase=0 # initial phase for gratingStim
#aperture and position parameters
centerPoint = [63.5,0]#[50,-8]  #12
#centerPoint = [50,0]
centerPoint1 = [-37.5,0]#[-50,8]
#centerPoint1 = [-50,0]
#centerPoint1= [150,-25] 
#stimSize = numpy.arange(5,60,float(60)/numSize) #Remember, ranges in Python do NOT include the final value! #Size of grating in degrees
#stimSize = numpy.logspace(0.8,2,float(60)/(numSize-1)) # array([   6.30957344,    9.36329209,   13.89495494,   20.6198601 ,  30.59949687,   45.40909611,   67.38627168,  100.        ])
stimSize = [100] #Size

#Triggering type
#Can be any of:
# "NoTrigger" - no triggering; stim will run freely
# "SerialDaqOut" - Triggering by serial port. Stim codes are written to the MCC DAQ.
# "OutOnly" - no input trigger, but does all output (to CED) and logging
triggerType ='OutOnly'
serialPortName = 'COM10' # ignored if triggerType is "None"
adjustDurationToMatch2P=True

#Experiment logging parameters
#dataPath='x:/'
#animalName='TSmax1323'
#expName = 't00006'
#logFilePath =dataPath+animalName+'//'+animalName+expName+'.txt' #including filepath

# ---------- Stimulus code begins here ---------- #
stimCodeName=path.dirname(path.realpath(__file__))+'\\'+path.basename(__file__)

#make a window
myWin = visual.Window(size=[1920,1080],monitor=mon,fullscr=True,screen=1, allowGUI=False, waitBlanking=True)

#print myWin.gamma
myWin.setGamma(.479)

#Set up the trigger behavior
trigger = None
if triggerType == "NoTrigger":
    import noTrigger
    trigger = noTrigger.noTrigger(None) 
elif triggerType == "SerialDaqOut" or triggerType == 'OutOnly':
    import serialTriggerDaqOut
    trigger = serialTriggerDaqOut.serialTriggerDaqOut(serialPortName) 
    if triggerType == 'OutOnly':
        trigger.readSer=False
    #Record a bunch of serial triggers and fit the stim duration to an exact multiple of the trigger time
    if adjustDurationToMatch2P:
        stimDuration = trigger.extendStimDurationToFrameEnd(stimDuration)
    # determine the Next experiment file name
#    expName=trigger.getNextExpName([dataPath,animalName])
    # store the stimulus data and prepare the directory
#    trigger.preTrialLogging([dataPath,animalName,expName,stimCodeName,orientations])
else:
    print "Unknown trigger type", triggerType
        
print "Stim Duration is", stimDuration, "seconds"
changeDirectionTimeAt = stimDuration * changeDirectionAt
print "The stim will change direction at ", changeDirectionTimeAt 
#create grating stim
gratingStimS = visual.GratingStim(win=myWin,tex=textureType,mask='none',units='deg', # center orientation tuning, orthogonal to surround!!!!!
    pos=centerPoint1,size=[200, 200], sf=0.6, autoLog=False, opacity=1,contrast=0.2)
gratingStimS.setAutoDraw(True)

gratingStim = visual.GratingStim(win=myWin,tex=textureType,units='deg',mask='none',
    pos=centerPoint,size=stimSize, sf=spatialFreq, autoLog=False, opacity=1)
    
gratingStim.setAutoDraw(True)

gratingStimB = visual.GratingStim(win=myWin,tex=textureType,mask='none',units='deg', # center orientation tuning, orthogonal to surround!!!!!
    pos=centerPoint1,size=stimSize, sf=spatialFreq, autoLog=False, opacity=1)

#gratingStimB =visual.GratingStim(win=myWin,tex='saw',mask='circle',units='deg',
#    pos=centerPoint, ori=120, size=20, sf=0.00000001000, phase=0, autoLog=False, opacity=1) # center gray mask
    
gratingStimB.setAutoDraw(True)

#gratingStim.setColor([-0,0,0.8], colorSpace='lms')#blue green
#gratingStim.setColor([-0,0,0.8], colorSpace='lms')#blue green
barTexture = numpy.ones([256,256,3]);
flipStim = visual.PatchStim(win=myWin,tex=barTexture,mask='none',units='pix',pos=[-920,500],size=(100,100))
flipStim.setAutoDraw(True)#up left, this is pos in y, neg in x
clrctr=1;

#run
clock = core.Clock() # make one clock, instead of a new instance every time. Use 
print "\n",str(len(orientations)+doBlank), "stims will be run for",str(numTrials),"trials."
for trial in range(0,numTrials): 
    #determine stim order
    if triggerType != "NoTrigger":
        if pauseBetweenTrials:
            print "Waiting for User Input"
            event.waitKeys(keyList=['space'])
    print "Beginning Trial",trial+1
    stimOrder = range(0,len(orientations)+doBlank)
    if isRandom:
        random.shuffle(stimOrder)
    for stimNumber in stimOrder:
        #display each stim
        trigger.preStim(stimNumber+1)
        #display stim
        flipStim.setContrast(1)
        flipStim.setAutoDraw(True)
        # convert orientations to standard lab notation
        if stimNumber == len(orientations):
            gratingStim.setContrast(0)
            gratingStimB.setContrast(0)
            startingPhase1 = 0
            print "\tStim",stimNumber+1," (blank)"
        else:
            gratingStimB.setContrast(orientations[stimNumber])
            gratingStimB.ori = CenterOrientations
            gratingStimS.ori = CenterOrientations+90
            gratingStim.setContrast(1-orientations[stimNumber])
            gratingStim.ori = CenterOrientations
            startingPhase1 = 0
            print "\tStim",stimNumber+1,orientations[stimNumber],'deg'
        clock.reset()
        while clock.getTime()<stimDuration:
            clrctr=clrctr+1;
            if clrctr%2==1:
                #flipStim.setColor((0,0,0),colorSpace='rgb')
                flipStim.setContrast(-1)
            else:
                #flipStim.setColor((1,1,1),colorSpace='rgb')
                flipStim.setContrast(1)
            if isMoving:
                if clock.getTime()>changeDirectionTimeAt:
                    gratingStim.setPhase(startingPhase1+changeDirectionTimeAt*temporalFreq - (clock.getTime()-changeDirectionTimeAt)*temporalFreq)
                    gratingStimB.setPhase(startingPhase+changeDirectionTimeAt*temporalFreq - (clock.getTime()-changeDirectionTimeAt)*temporalFreq)
                    #gratingStimB.setPhase(startingPhase-changeDirectionTimeAt*temporalFreq + (clock.getTime()-changeDirectionTimeAt)*temporalFreq)  % for opposite direction motion
                else:
                    gratingStim.setPhase(startingPhase1+clock.getTime()*temporalFreq)
                    gratingStimB.setPhase(startingPhase+clock.getTime()*temporalFreq)
                    #gratingStimB.setPhase(startingPhase-clock.getTime()*temporalFreq)
            trigger.preFlip(None)
            myWin.flip()
            trigger.postFlip(None)
            
        #now do ISI
        clock.reset()
        gratingStim.setContrast(0)
        gratingStimB.setContrast(0)
        flipStim.setContrast(0)
        trigger.preFlip(None)
        myWin.flip()
        trigger.postFlip(None)
        flipStim.setAutoDraw(False)
        while clock.getTime()<isi:
            #Keep flipping during the ISI. If you don't do this you can get weird flash artifacts when you resume flipping later.            
            myWin.flip()
        trigger.postStim(None)

#trigger.wrapUp([logFilePath, expName])
print 'Finished all stimuli.'