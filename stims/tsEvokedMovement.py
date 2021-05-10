# tsEvokedEyeMove.py: Evoked Eye Movement Psychophysics script
# Author: Matthew McCann (@mkm4884)
# Max Planck Florida Institute for Neuroscience
# Created: 08/18/2017
# Last Modified:

# Description: Script to evoke gaze fixation and saccades using static and moving stimuli,
# which are either black dots or natural images. Stimulus position, movement type, and natural or
# artificial stimulus are randomly assigned. A log containing this information is output.


from psychopy import visual, logging, core, filters, event, monitors
import pylab, math, random, numpy, time, imp, sys, fileinput
import os
import glob
from math import pi, radians, cos, sin, floor
import random
from scipy.stats import norm

# ---------- Log File ---------- #
# Create txt file for stim times with reference to absolute clock time
fileinput.close()  # ensure no file input is active already
if sys.argv[-1] == '--called':
    isCalled = True
    dataPath = sys.argv[-2] + os.sep + 'dot_stim' + os.sep
    logFilePath = dataPath + "stim_movement_times.txt"
    logFile = open(logFilePath, 'w')
    logFile.write('fix_movement type movement position time\n')
    logFile.close()
    print 'Saving stim times to: ' + logFilePath
else:
    isCalled = False

# ---------- Monitor Properties ---------- #
windowed = False
res = [1920, 1080]
if windowed:
    res = [800, 600]
mon = monitors.Monitor('stimMonitor') # gets the calibration for stim
mon.setDistance(25)
mon.setSizePix(res)
mon.setWidth(51)

# ---------- Stimulus Properties ---------- #
stimDuration = 5        # stimulus duration in seconds; will be adjusted if adjustDurationToMatch2P=1
changeDirectionAt = .5
changeDirectionTimeAt = changeDirectionAt * stimDuration
timeBetweenFrames = 0.008   # 120Hz

stimKinds = ['none', 'brownian', 'circle', 'bernoulli']
# Brownian motion
delta = 1
dt = 0.1
# circular motion
radius = 1.5
omega = 0.15  # Angular velocity
# figure 8 using the Lemniscate of Bernoulli
bdt = 0.1
# bugs
curr_dir = os.getcwd()
bug_dir = curr_dir + os.sep + 'bugs' + os.sep
bug_files = glob.glob(bug_dir + '*.png')

#make a window
myWin = visual.Window(size=res, monitor=mon, fullscr=(not windowed), screen=1)

print "Stim Duration is", stimDuration, "seconds"
all_stims = []
# stim dot positions
r = 30
thetas = [-135, -90, -45, 0, 45, 90, 135, 180]
black_dot = {'stim': visual.ImageStim(myWin, color=(-1, -1, -1), units="deg", mask="circle", size=(5,5)),
             'movement': stimKinds,
             'name': 'dot'
             }
fixation_dot = visual.ImageStim(myWin, color=(-1, -1, -1), units="deg", mask="circle", size=(5,5))
all_stims.append(black_dot)

# make bug stim
# for bug in bug_files:
#     name = bug.rsplit(os.sep)[-1].rsplit('.')[0]
#     stim = {'stim': visual.ImageStim(myWin, image=bug, units="deg", size=10),
#             'movement': stimKinds,
#             'name': name,
#             }
#     all_stims.append(stim)
# make bug stim - Removed 08/23

clock = core.Clock()    # make one clock, instead of a new instance every time.
i = 0
while True:
    i += 1
    # reset parameters for motion
    clock.reset()
    myWin.flip()
    angle1 = radians(0)
    t1 = 0
    angle2 = radians(0)
    t2 = 0
    # pick stimulus randomly
    stim_dict = random.choice(all_stims)
    # get stim
    stim = stim_dict['stim']
    # pick movement type randomly
    fix_mov = random.choice(stimKinds)
    mov = random.choice(stim_dict['movement'])
    # pick starting position randomly
    angle = random.choice(thetas)
    pos = [r*cos(radians(angle)), r*sin(radians(angle))]
    fix_pos = [0,0]
    # direction
    direction = random.choice([-1, 1])
    # rotation
    ori = random.choice(range(-45, 46, 15))
    # get stim name and print in readable format
    name = stim_dict['name']
    # print "{}: {} motion type at position {} and rotation {} degrees".format(i, name, mov, pos, ori)
    print "{}: {} motion at {} degrees".format(i, mov, angle)

    # ------------------------------------------------------------
    # If we are working with a called function
    if isCalled:
        t = time.time()
        with open(logFilePath, 'a') as logFile:
            logFile.write(name + ' ' + mov + ' ' + str(r) + ' ' + str(angle) + ' ' + str(time.time()) + '\n')
    # ------------------------------------------------------------

    while clock.getTime() < stimDuration:
        # Maintain fixation dot
        while clock.getTime() < changeDirectionTimeAt:
            myWin.flip()
            if fix_mov == 'brownian':
                fixation_dot.setPos(fix_pos)
                fix_pos[0] += norm.rvs(scale=delta ** 2 * dt)
                fix_pos[1] += norm.rvs(scale=delta ** 2 * dt)
                fixation_dot.draw()
            elif fix_mov == 'circle':
                fixation_dot.setPos(fix_pos)
                angle1 += omega
                fix_pos[0] += direction * omega * cos(angle1 + pi / 2)
                fix_pos[1] += direction * radius * omega * sin(angle1 + pi / 2)
                fixation_dot.draw()
            elif fix_mov == 'bernoulli':
                fixation_dot.setPos(fix_pos)
                t1 += bdt
                scale = 2.5
                fix_pos[0] += direction * scale * (cos(t1) - cos(t1 - bdt))
                fix_pos[1] += direction * scale * (sin(2 * t1) / 2 - sin(2 * (t1 - bdt)) / 2)
                fixation_dot.draw()
            else:
                stim.setPos(fix_pos)
                fixation_dot.draw()

        # Draw moving dot in randomly assigned position
        myWin.flip()
        if name != 'dot':
            stim.ori = ori

        if mov == 'brownian':
            stim.setPos(pos)
            pos[0] += norm.rvs(scale=delta**2 * dt)
            pos[1] += norm.rvs(scale=delta**2 * dt)
            stim.draw()
        elif mov == 'circle':
            stim.setPos(pos)
            angle2 += omega
            pos[0] += direction*omega*cos(angle2 + pi/2)
            pos[1] += direction*radius*omega*sin(angle2 + pi/2)
            stim.draw()
        elif mov == 'bernoulli':
            stim.setPos(pos)
            t2 += bdt
            scale = 2.5
            pos[0] += direction*scale*(cos(t2) - cos(t2-bdt))
            pos[1] += direction*scale*(sin(2*t2)/2 - sin(2*(t2-bdt))/2)
            stim.draw()
        else:
            stim.setPos(pos)
            stim.draw()
