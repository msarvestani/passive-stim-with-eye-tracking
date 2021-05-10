from psychopy import visual, logging, core, filters, event, monitors
import pylab, math, random, numpy, time, imp, sys
sys.path.append("C:/Users/fitzlab1/Documents/psychopy/Gordon/triggers") #path to trigger classes
from os import path
print "initialized"


#---------- Monitor Properties ----------#
mon= monitors.Monitor('stim2') #gets the calibration for stimMonitor
mon.setDistance(26)

triggerType = 'OutOnly'
serialPortName = 'COM1' # ignored if triggerType is "None"
import serialTriggerDaqOut
trigger = serialTriggerDaqOut.serialTriggerDaqOut(serialPortName) 
trigger.readSer=False
myWin = visual.Window(size=[1920,1080],monitor=mon,fullscr=True,screen=1, allowGUI=False, waitBlanking=True)
barTexture = numpy.ones([256,256,3]);
flipStim = visual.PatchStim(win=myWin,tex=barTexture,mask='none',units='pix',pos=[-920,500],size=(200,200))
flipStim.setAutoDraw(True)#up left, this is pos in y, neg in x
clrctr=1;
print "made grating"
#run
flipStim.setContrast(1)
flipStim.setAutoDraw(True)
while True:
    clrctr=clrctr+1;
    if clrctr%2==1:
        flipStim.setContrast(-1)
    else:
        flipStim.setContrast(1)
    trigger.preFlip(None)
    myWin.flip()
    trigger.postFlip(None)
