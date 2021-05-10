# reports when a trigger comes in. 
# Useful to test whether 2P triggers are arriving properly.
from psychopy import visual, logging, core, filters, event, monitors
import pylab, math, random, numpy, time, imp, sys
sys.path.append("../triggers") #path to trigger classes
from os import path
print "initialized"
import inputTriggerTestTrigger


serialPortName = 'COM3' # ignored if triggerType is "None"
trigger = inputTriggerTestTrigger.inputTriggerTestTrigger(serialPortName) 
count=0;
clock=core.Clock()
print 'Waiting for serial inputs...'
#t=trigger.getTimeBetweenTriggers
#print 'Time bn trig: ',t
stimDuration = trigger.extendStimDurationToFrameEnd(5)
print stimDuration

clock.reset()
trigger.waitForSerial()
while True:
    time.sleep(0.015)
    trigger.waitForSerial()
    count=count+1
    print 'Trigger ',count,' recieved in ',clock.getTime()
    clock.reset()


