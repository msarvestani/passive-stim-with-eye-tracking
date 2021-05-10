from psychopy import visual, logging, core, filters, event, monitors
import pylab, math, random, numpy, time, imp, sys, fileinput, itertools
from os import path, getcwd
from util.enumeration import *
from PyQt4 import uic
sys.path.append("../triggers")  # path to trigger classes
sys.path.append('..')

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

# ---------- Monitor Properties ----------#
mon = monitors.Monitor('stimMonitor')  # gets the calibration for stim
mon.setDistance(25)
mon.setWidth(51)
mon.setSizePix([1920,1080])

# ---------- Stimulus Parameters ---------- #
animalID = 'Baby'  # MAKE SURE TO REPLACE THIS WITH CORRECT ANIMAL

# trials and duration
numOrientations = 8  # typically 4, 8, or 16
orientations = numpy.arange(0.0, 180, float(180) / numOrientations)  # Remember, ranges in Python do NOT include the final value!
numTrials = 10  # Run all the stims this many times
pauseBetweenTrials = 0  # Wait for user to press space bar in between trials
doBlank = 1  # 0 for no blank stim, 1 to have a blank stim. The blank will have the highest stimcode.
stimDuration = 1  # stimulus duration in seconds; will be adjusted if adjustDurationToMatch2P=1
isMoving = 1  # 1 for moving stimulus, 0 for stationary
changeDirectionAt = .5  # When do we change movement directions? If 1, there should be no reversal.  If 0.5, then movement reverses directions at stimDuration/2
isi = 1  # Kuo 4 to 2
isRandom = 1

# Grating parameters
temporalFreq = 4
spatialFreq = 0.25
contrast = 1  # 0.125
textureType = 'sqr'  # 'sqr' = square wave, 'sin' = sinusoidal
startingPhase = 0  # initial phase for gratingStim

# aperture and position parameters
centerPoint = [0, 0]
stimSize = [200, 200]  # Size of grating in degrees

# Triggering type
# Can be any of:
# "NoTrigger" - no triggering; stim will run freely
# "SerialDaqOut" - Triggering by serial port. Stim codes are written to the MCC DAQ.
# "OutOnly" - no input trigger, but does all output (to CED) and logging
# triggerType = 'OutOnly'
triggerType = 'OutOnly'

serialPortName = 'COM1'  # ignored if triggerType is "None"
adjustDurationToMatch2P = True

# ---------- Optogenetics Parameters ---------- #
pulse_set = ['RAMP', 'SAWTOOTH', 'SINE_RAMP', 'SINE_TRAP', 'SQUARE', 'TRAP', 'TRIANGLE']
pulses = Enumeration("Pulses", pulse_set)

powerLevels = [0, 1, 2, 4, 8]      # mW/mm2
rampDuration = 100     # milliseconds
pulse_type = pulses.SQUARE

# we need to tell the opto process what the parameters for timing are
# ramp times will be equal for rampUp and rampDown
setup_cmd = "cmd pls" + str(pulse_type) + " sus" + str(stimDuration*1000) + ' rmp' + str(rampDuration) + '\n'
sys.stdout.write(setup_cmd)

# hang out for a sec before starting to allow for setup, etc
time.sleep(10)

# Guarantee that all stims have all possible power levels
combos = []
# This is a stupid method to flag the blank in here to make sure we give it all power levels
if doBlank:
    orientations = numpy.append(orientations, [1000])

for p in powerLevels:
    combos.append([(o, p) for o in orientations])
combos = [y for x in combos for y in x]     # stole this off stack overflow.

# ---------- Stimulus code begins here ---------- #
stimCodeName = path.dirname(path.realpath(__file__)) + '\\' + path.basename(__file__)

# make a window
myWin = visual.Window(size=[1920, 1080], monitor=mon, fullscr=True, screen=1, allowGUI=False, waitBlanking=True)

# print myWin.gamma
# myWin.setGamma(.479)

# Set up the trigger behavior
trigger = None
if triggerType == "NoTrigger":
    import noTrigger

    trigger = noTrigger.noTrigger(None)
elif triggerType == "SerialDaqOut" or triggerType == 'OutOnly':
    import serialTriggerDaqOut

    trigger = serialTriggerDaqOut.serialTriggerDaqOut(serialPortName)
    if triggerType == 'OutOnly':
        trigger.readSer = False
    # Record a bunch of serial triggers and fit the stim duration to an exact multiple of the trigger time
    if adjustDurationToMatch2P:
        stimDuration = trigger.extendStimDurationToFrameEnd(stimDuration)
        # determine the Next experiment file name
        #    expName=trigger.getNextExpName([dataPath,animalName])
        # store the stimulus data and prepare the directory
# trigger.preTrialLogging([dataPath,animalName,expName,stimCodeName,orientations])
else:
    print "Unknown trigger type", triggerType

changeDirectionTimeAt = stimDuration * changeDirectionAt
print "Stim Duration is", stimDuration, "seconds"
print "The stim will change direction at ", changeDirectionTimeAt

# create grating stim
gratingStim = visual.GratingStim(win=myWin, tex=textureType, units='deg',
                                 pos=centerPoint, size=stimSize, sf=spatialFreq, autoLog=False)

gratingStim.setAutoDraw(True)
barTexture = numpy.ones([256, 256, 3])
flipStim = visual.PatchStim(win=myWin, tex=barTexture, mask='none', units='pix', pos=[-920, 500], size=(100, 100))
flipStim.setAutoDraw(True)  # up left, this is pos in y, neg in x
clrctr = 1

# run
print "\n", str(len(combos)), "stims will be run for", str(numTrials), "trials."
clock = core.Clock()  # make one clock, instead of a new instance every time. Use

for trial in range(0, numTrials):
    # determine stim order
    if triggerType != "NoTrigger":
        if pauseBetweenTrials:
            print "Waiting for User Input"
            event.waitKeys(keyList=['space'])
    print "Beginning Trial", trial + 1

    stimOrder = range(0, len(combos))

    if isRandom:
        random.shuffle(stimOrder)

    for stimNumber in stimOrder:
        clock.reset()

        #  we can pull out all of the useful information first
        ori = combos[stimNumber][0]
        power = combos[stimNumber][1]

        # ------------------------------------------------------------
        # Send optogenetic stimulation flags back to other thread
        # This happens regardless of if the visual stim is blank or not
        opto_cmd = 'cmd pwr' + str(power) + '\n'
        sys.stdout.writelines(opto_cmd)

        # sleep for ramping duration before showing the stim
        clock.reset()
        while clock.getTime() < rampDuration * 0.001:
            myWin.flip()
        # ------------------------------------------------------------

        # display each stim
        trigger.preStim(stimNumber + 1)
        # display stim
        flipStim.setContrast(1)
        flipStim.setAutoDraw(True)

        # convert orientations to standard lab notation
        if ori == 1000:
            # We only display a blank if we've found this stupid value
            gratingStim.setContrast(0)
            print "\tStim", stimNumber + 1, " (blank) power ", power, ' mW/mm^2'

        else:
            gratingStim.setContrast(contrast)
            gratingStim.ori = ori - 90.00
            print "\tStim", stimNumber + 1, ori, 'deg power ', power, ' mW/mm^2'

        # ------------------------------------------------------------
        # If we are working with a called function, write the stim file
        if isCalled:
            t = time.time()
            with open(logFilePath, 'a') as logFile:
                logFile.write("Stim " + str(stimNumber + 1) + ' ' + str(t) + '\n')
        # ------------------------------------------------------------

        clock.reset()

        while clock.getTime() < stimDuration:
            clrctr = clrctr + 1
            if clrctr % 2 == 1:
                # flipStim.setColor((0,0,0),colorSpace='rgb')
                flipStim.setContrast(-1)
            else:
                # flipStim.setColor((1,1,1),colorSpace='rgb')
                flipStim.setContrast(1)
            if isMoving:
                if clock.getTime() > changeDirectionTimeAt:
                    gratingStim.setPhase(startingPhase + changeDirectionTimeAt * temporalFreq - (clock.getTime() - changeDirectionTimeAt) * temporalFreq)
                else:
                    gratingStim.setPhase(startingPhase + clock.getTime() * temporalFreq)

            trigger.preFlip(None)
            myWin.flip()
            trigger.postFlip(None)

        # now do ISI
        clock.reset()
        gratingStim.setContrast(0)
        flipStim.setContrast(0)
        trigger.preFlip(None)
        myWin.flip()
        trigger.postFlip(None)
        flipStim.setAutoDraw(False)

        while clock.getTime() < isi-(rampDuration*0.001):
            # Keep flipping during the ISI. If you don't do this you can get weird flash artifacts when you resume flipping later.
            myWin.flip()

        trigger.postStim(None)

# trigger.wrapUp([logFilePath, expName])
print 'Finished all stimuli.'