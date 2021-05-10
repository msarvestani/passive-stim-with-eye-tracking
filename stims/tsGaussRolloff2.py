from __future__ import division

from psychopy import visual, logging, core, event
import pylab, math, serial
from numpy import *

#input parameters
duration=6000 #in seconds
temporalFreq=1
spatialFreq=0.25
orientation=48.75
rolloffStartPoint = 0.8 #where to start the Gaussian rolloff

#make a window
mywin = visual.Window(monitor='StimMonitor',fullscr=True,screen=1)

def makeGaussianRolloffMask(rolloffStartPoint):
    #Makes an alpha mask with Gaussian rolloff
    maskSize = 1024 #must be a power of 2. Higher gives nicer resolution but longer compute time.
    sigma = 0.12 #decays nicely to < 1% contrast at the edge
    twoSigmaSquared = 2*pow(sigma,2) #handy for later
    
    mask = ones([maskSize, maskSize])

    maskCenter = maskSize / 2
    rolloffStartPx = maskSize / 2 * rolloffStartPoint
    rolloffStartPxSquared = pow(rolloffStartPx, 2)
    rolloffLengthPx = (1-rolloffStartPoint)*maskSize/2

    #This is just distance formula calculated a bit faster
    squaredDistances = zeros(maskSize) 
    for i in xrange(0,maskSize):
        squaredDistances[i] = math.pow(i-maskCenter, 2)
    
    # Fill in alpha values to produce Gaussian rolloff.
    # Note: In PsychoPy, -1 is "nothing", 0 is "half contrast", 1 is "full contrast".
    for i in xrange(0,maskSize):
        for j in xrange(0,maskSize):
            dSquared = squaredDistances[i] + squaredDistances[j]
            if dSquared > rolloffStartPxSquared:
                #we are outside the main circle, so fade appropriately
                fadeProportion = (math.sqrt(dSquared)-rolloffStartPx) / rolloffLengthPx
                if fadeProportion > 1:
                    #we are outside the circle completely, so we want "nothing" here.
                    mask[i,j] = -1
                else:
                    x = fadeProportion / 2 #input to Gaussian function, in range [0,0.5]
                    alphaValue = math.exp(-pow(x,2)/twoSigmaSquared)*2 - 1
                    mask[i,j] = alphaValue
        
    return mask

def makeLinearRolloffMask(rolloffStartPoint):
    #Makes an alpha mask with linear rolloff
    maskSize = 1024 #must be a power of 2. Higher gives nicer resolution but longer compute time.
    
    mask = ones([maskSize, maskSize])

    maskCenter = maskSize / 2
    rolloffStartPx = maskSize / 2 * rolloffStartPoint
    rolloffStartPxSquared = pow(rolloffStartPx, 2)
    rolloffLengthPx = (1-rolloffStartPoint)*maskSize/2

    #This is just distance formula calculated a bit faster
    squaredDistances = zeros(maskSize) 
    for i in xrange(0,maskSize):
        squaredDistances[i] = math.pow(i-maskCenter, 2)
    
    # Fill in alpha values to produce linear rolloff.
    # Note: In PsychoPy, -1 is "nothing", 0 is "half contrast", 1 is "full contrast".
    for i in xrange(0,maskSize):
        for j in xrange(0,maskSize):
            dSquared = squaredDistances[i] + squaredDistances[j]
            if dSquared > rolloffStartPxSquared:
                #we are outside the main circle, so fade appropriately
                fadeProportion = (math.sqrt(dSquared)-rolloffStartPx) / rolloffLengthPx
                if fadeProportion > 1:
                    #we are outside the circle completely, so we want "nothing" here.
                    mask[i,j] = -1
                else:
                    mask[i,j] = 1-fadeProportion*2
        
    return mask

#create grating
stim1 = visual.GratingStim(win=mywin,tex='sqr',units='deg',pos=(0,0),size=(30,30),ori=orientation,sf=spatialFreq)
stim1.mask = makeGaussianRolloffMask(rolloffStartPoint)

#stim1.mask = 'gauss'
stim1.setAutoDraw(True)

#run
clock = core.Clock()
while clock.getTime()<duration:        
    newPhase = clock.getTime()*temporalFreq
    stim1.setPhase(newPhase)
    mywin.flip()
    
    #exit if user hits space or q
    keyList = event.getKeys(['space','q']) 
    if len(keyList): break
