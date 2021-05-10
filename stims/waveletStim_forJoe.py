from psychopy import visual, logging, core, filters, event,monitors
import pylab, math, random, numpy, time, imp, sys
sys.path.append("../triggers") #path to trigger classes
from os import path
print "initialized"

#---------- Monitor Properties ----------#
mon= monitors.Monitor('stimMonitor') #gets the calibration for stimMonitor
mon.setDistance(20)
overwriteGammaCalibration=True
newGamma=0.479


# stim properties
repeats=10;
interRepeatInt=8 # time between repeats through the stims
movies=10; # number of different wavelet movies to show
interMovieInt=5 # in sec, time b/n movies, gray screen here
stimFramesPerTrial=256 # number of images in each movie - should be 480. 
#stimFramesPerTrial = 2700 #for white noise
# Movie is shown at 15 fps, so stim length=stimFramesPerTrial/30.

#Triggering type
#Can be any of:#"NoTrigger" - no triggering; stim will run freely
#"SerialDaqOut" - Triggering by serial port. Stim codes are written to the MCC DAQ.
# "OutOnly" - no input trigger, but does all output (to CED) and logging
#"DaqIntrinsicTrigger" - waits for stimcodes on the MCC DAQ and displays the appropriate stim ID
#triggerType = 'DaqIntrinsicTrigger'
triggerType = 'OutOnly'

serialPortName = 'COM1' # ignored if triggerType is "None"
adjustDurationToMatch2P=False # must be false here

#Experiment logging parameters
#dataPath='y:/'
#animalName='F1642_2014-05-14';
#logFilePath =dataPath+animalName+'\\'+animalName+'.txt' #including filepath


# ---------- Stimulus code begins here ---------- #
stimCodeName=path.dirname(path.realpath(__file__))+'\\'+path.basename(__file__)
win = visual.Window(size=[1920,1080],monitor=mon,fullscr=True,screen=1, allowGUI=False, waitBlanking=True)
if overwriteGammaCalibration:
    win.setGamma(newGamma)
    print "Overwriting Gamma Calibration. New Gamma value:",newGamma
print "made window, setting up triggers"

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
#    expName=trigger.getNextExpName([dataPath,animalName])
#    print "Trial name: ",expName
    if triggerType == 'OutOnly':
        trigger.readSer=False
    #Record a bunch of serial triggers and fit the stim duration to an exact multiple of the trigger time
    if adjustDurationToMatch2P:
        print "Waiting for serial Triggers"
        stimDuration = trigger.extendStimDurationToFrameEnd(stimDuration)
    # store the stimulus data and prepare the directory
#    trigger.preTrialLogging([dataPath,animalName,expName,stimCodeName,[0],logFilePath])
elif triggerType=="DaqIntrinsicTrigger":
    import daqIntrinsicTrigger
    trigger = daqIntrinsicTrigger.daqIntrinsicTrigger(None) 
else:
    print "Unknown trigger type", triggerType
        

#make image stim
image = visual.ImageStim(win=win, name='image',units=u'pix', 
    pos=[120,0], size=[300,300],
    color=[1,1,1], colorSpace=u'rgb', opacity=1,
    texRes=128, interpolate=True)
   
clock = core.Clock()  # to track the time since experiment started
for rep in range(1,repeats+1):
    print "Starting repition "+str(rep)
    for tr in range(1,(movies+1)):
        print "Starting wavelet movie "+str(tr)
        trigger.preStim(tr)
        im=0;
        Iname='C:/Users/fitzlab1/Documents/psychopy/Gordon/episodicStims/WaveletStims/tiffDir_20pctSat/wv'+str(tr)+'_' + '{:04.0f}'.format(im+1)+ '.tif'
        #Iname = 'C:/Users/fitzlab1/Documents/psychopy/Gordon/episodicStims/WaveletStims/tiffDir_GaussWN/wn'+str(tr)+'_' + '{:04.0f}'.format(im+1)+ '.tif'
        image.setImage(Iname)

        image.setAutoDraw(True)
        while im < (stimFramesPerTrial-1):
            clock.reset()
            trigger.preFlip(None)
            win.flip()
            trigger.postFlip(None)
            while clock.getTime()<(.06666-1.0/120.0):
                win.flip()
            im=im+1
            Iname='C:/Users/fitzlab1/Documents/psychopy/Gordon/episodicStims/WaveletStims/tiffDir_20pctSat/wv'+str(tr)+'_' + '{:04.0f}'.format(im+1)+ '.tif'
            #Iname = 'C:/Users/fitzlab1/Documents/psychopy/Gordon/episodicStims/WaveletStims/tiffDir_GaussWN/wn'+str(tr)+'_' + '{:04.0f}'.format(im+1)+ '.tif'
            image.setImage(Iname)

        # now do isi
        image.setAutoDraw(False)
        win.flip()
        clock.reset()
        trigger.postFlip(None)
        while clock.getTime()<interMovieInt:#, time b/n movies, gray screen here
            #Keep flipping during the ISI. If you don't do this you can get weird flash artifacts when you resume flipping later.            
            win.flip()
        trigger.postStim(None)
    if rep<repeats:
        clock.reset()
        while clock.getTime()<(interRepeatInt-interMovieInt):#, time b/n repeats, gray screen here
            win.flip()

if triggerType != "NoTrigger":
    trigger.wrapUp([logFilePath, expName])
print 'Finished all stimuli.'
