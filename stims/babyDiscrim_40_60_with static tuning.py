from psychopy import visual, logging, core, filters, event, monitors
import pylab, math, random, numpy, time, imp, sys, fileinput
sys.path.append("../triggers") #path to trigger classes
from os import path

# ---------- Log File ---------- #
# Create txt file for stim times with reference to absolute clock time
fileinput.close()  # ensure no file input is active already
if sys.argv[-1] == '--called':
    isCalled = True
    dataPath = sys.argv[-2]
    logFilePath = dataPath + "abs_stim_on_times.txt"
    logFile = open(logFilePath, 'w')
    logFile.close()
    print 'Saving stim times to: ' + logFilePath
else:
    isCalled = False

# ---------- Stimulus Description ---------- #
'''A fullscreen drifting grating for 2pt orientation tuning'''
#---------- Monitor Properties ----------#
mon= monitors.Monitor('stimMonitor') #gets the calibration for stimMonitor
frameRate = 120 # not used
mon.setDistance(25)

# ---------- Stimulus Parameters ---------- #
#trials and duration
numOrientations = 16 #typically 4, 8, or 16
#orientations = numpy.arange(0.0,180,float(180)/numOrientations) #Remember, ranges in Python do NOT include the final value!

#orientations=[20,22.5,25,27.5,30,32.5,35,37.5,40,42.5,45,47.5,50,52.5,55,57.5,60,62.5,65,67.5,70]

#atemp = [-25, -22.5, -20, -17.5, -15, -12.5, -10, -7.5, -5, -2.5, 0, 2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20, 22.5, 25]
atemp = [117.5, 120, 122.5, 125, 127.5, 130, 132.5, 135, 137.5, 140, 142.5, 145, 147.5, 150, 152.5, 155, 157.5, 160, 162.5, 165, 167.5, 170, 172.5, 175, 177.5, 180]
btemp = [65, 67.5, 70, 72.5, 75, 77.5, 80, 82.5, 85, 87.5, 90, 92.5, 95, 97.5, 100, 102.5, 105, 107.5, 110, 112.5, 115]
#atemp = [-25, -22.5, -20, -17.5, -15, -12.5, -10, -7.5, -5, -2.5, 0, 2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20, 22.5, 25]
#btemp = [27.5, 30, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50, 52.5, 55, 57.5, 60, 62.5]
ctemp = [0, 11.25, 22.5, 33.75, 45, 56.25, 67.5, 78.75, 90, 101.25, 112.5, 123.75, 135, 146.25, 157.5, 168.75]
dtemp = [20, 22.5, 25, 27.5, 30, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50, 52.5, 55, 57.5, 60, 62.5]
orientations= atemp+btemp+ctemp+dtemp

#orientations = [0, 45, 90, 135]
#orientations=[55,57.5,60,62.5,65]
#orientations=[85,87.5,90,92.5,95,180,182.5,185,177.5,175]
#orientations=[40,42.5,45,47.5,50,130,132.5,135,137.5,140]
#orientations=[160,162.5,165,167.5,170]
#orientations=[20,22.5,25,27.5,30]
#orientations=[35,40,45,50,55]
#orientations = [40, 42.5, 45, 47.5, 50, 130, 132.5, 135, 137.5, 140]
numTrials = 20 #Run all the stims this many times
pauseBetweenTrials = 0 # Wait for user to press space bar in between trials
doBlank = 1 #0 for no blank stim, 1 to have a blank stim. The blank will have the highest stimcode.
stimDuration = 0.5 #stimulus duration in seconds; will be adjusted if adjustDurationToMatch2P=1
isMoving = 0 # 1 for moving stimulus, 0 for stationary
changeDirectionAt = .5 #When do we change movement directions? If 1, there should be no reversal.  If 0.5, then movement reverses directions at stimDuration/2
isi = 2
isRandom = 1

# Grating parameter
temporalFreq = 6 # Kuo form 4 to 6
spatialFreq = 0.25
contrast = 0.9
textureType = 'sqr' #'sqr' = square wave, 'sin' = sinusoidal
startingPhase=0 # initial phase for gratingStim
#aperture and position parameters
centerPoint = [0,0] 
stimSize = [200, 200] #Size of grating in degrees


#Triggering type
#Can be any of:
# "NoTrigger" - no triggering; stim will run freely
# "SerialDaqOut" - Triggering by serial port. Stim codes are written to the MCC DAQ.
# "OutOnly" - no input trigger, but does all output (to CED) and logging
triggerType ='OutOnly'
#triggerType = 'NoTrigger'

serialPortName = 'COM1' # ignored if triggerType is "None"
adjustDurationToMatch2P=True

# ---------- Stimulus code begins here ---------- #
stimCodeName=path.dirname(path.realpath(__file__))+'\\'+path.basename(__file__)

#make a window
myWin = visual.Window(size=[1920,1080],monitor=mon,fullscr=True,screen=1, allowGUI=False, waitBlanking=True)

#print myWin.gamma
#myWin.setGamma(.479)

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
gratingStim = visual.GratingStim(win=myWin,tex=textureType,units='deg',
    pos=centerPoint,size=stimSize, sf=spatialFreq, autoLog=False)
    
gratingStim.setAutoDraw(True)
#gratingStim.setColor([-0,0,0.8], colorSpace='lms')#blue green
#gratingStim.setColor([-0,0,0.8], colorSpace='lms')#blue green
barTexture = numpy.ones([256,256,3]);
flipStim = visual.PatchStim(win=myWin,tex=barTexture,mask='none',units='pix',pos=[-920,500],size=(100,100))
flipStim.setAutoDraw(True)#up left, this is pos in y, neg in x
clrctr=1;

#run
running = True
clock = core.Clock() # make one clock, instead of a new instance every time. Use 
print "\n", str(len(orientations)+doBlank), "stims will be run for ", str(numTrials), " trials."
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

        # ------------------------------------------------------------
        # If we are working with a called function
        if isCalled:
            t = time.time()
            with open(logFilePath, 'a') as logFile:
                logFile.write("Stim " + str(stimNumber+1) + ' ' + str(t) + '\n')
        # ------------------------------------------------------------

        #display each stim
        trigger.preStim(stimNumber+1)
        #display stim
        flipStim.setContrast(1)
        flipStim.setAutoDraw(True)
        # convert orientations to standard lab notation
        if stimNumber == len(orientations):
            gratingStim.setContrast(0)
            print "\tStim",stimNumber+1," (blank)"
        else:
            gratingStim.setContrast(contrast)
            gratingStim.ori = orientations[stimNumber]-90.00
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
                    gratingStim.setPhase(startingPhase+changeDirectionTimeAt*temporalFreq - (clock.getTime()-changeDirectionTimeAt)*temporalFreq)
                else:
                    gratingStim.setPhase(startingPhase+clock.getTime()*temporalFreq)
            trigger.preFlip(None)
            myWin.flip()
            trigger.postFlip(None)
            
        #now do ISI
        clock.reset()
        gratingStim.setContrast(0)
        flipStim.setContrast(0)
        trigger.preFlip(None)
        myWin.flip()
        trigger.postFlip(None)
        flipStim.setAutoDraw(False)
        while clock.getTime()<isi:
            #Keep flipping during the ISI. If you don't do this you can get weird flash artifacts when you resume flipping later.            
            myWin.flip()
        trigger.postStim(None)
