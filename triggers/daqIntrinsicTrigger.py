# Daq Triggering - triggers when stimcodes arrive via a Measurement Computing DAQ
# used in intrinsic imaging experiments in the SLM room
import UniversalLibrary as UL
from abstractTrigger import trigger
from os import path,makedirs
import shutil
import glob
import serial, csv, time, math, datetime


class daqIntrinsicTrigger(trigger):
    def __init__(self, args):  
        #DAQ setup
        self.boardNum = 0
        UL.cbDConfigPort(self.boardNum,UL.FIRSTPORTA, UL.DIGITALIN)

    def preStim(self, args):
        print 'Waiting for stimcode to arrive on DAQ...'
        stimcode = 0;
        while stimcode > 64 or stimcode == 0:
            #keep trying until a valid stimcode appears
            stimcode = UL.cbDIn(self.boardNum, UL.FIRSTPORTA, stimcode)
        print 'Got stimcode ',stimcode
        return stimcode-1

    def postStim(self, args):
        pass

    def preFlip(self, args):
        pass

    def postFlip(self, args):
        pass

    def wrapUp(self, args):
        pass
    def preTrialLogging(self, args):
        dataDirName = args[0]
        animalName = args[1]
        expName = args[2]
        stimCodeName = args[3]
        orientations = args[4]
        logFilePath = args [5]
        datapath=dataDirName+animalName+'\\'
        # write the dirname and expname for spike2
        f=open(dataDirName+'experimentname.txt','w')
        f.write(animalName)
        f.close()
        f=open(dataDirName+'instruction.txt','w')
        f.write(expName)
        f.close()
        # write the reference file, vht style
        destname=dataDirName+animalName+'\\'+expName+'\\'
        if not path.exists(destname):
            makedirs(destname)
        f=open(destname+'reference.txt','w')
        f.write('name\tref\ttype\ntp\t'+str(1)+'\tprairietp')
        f.close()
        # now write the stim parameters
        stimCodeName=stimCodeName.replace('.pyc','.py')
        shutil.copy(stimCodeName,destname)
        trigcodename=path.dirname(path.realpath(__file__))+'\\'+path.basename(__file__)
        trigcodename=trigcodename.replace('.pyc','.py') # if trigger was already compiled, __file__ is the pyc, not the human readable py.
        shutil.copy(trigcodename,destname)
        # explicitly write orientations
        oout=str(orientations)
        oout=oout.replace('[','')
        oout=oout.replace(']','')
        f=open(destname+'stimorientations.txt','w')
        f.write(oout)
        f.close()
        with open(logFilePath, "a") as csvfile:
            w = csv.writer(csvfile, dialect = "excel")
            w.writerow(["==========="])
            w.writerow([animalName," ",expName," Started at ",datetime.datetime.now()])
    def getNextExpName(self,args):
        dataDirName = args[0]
        animalName = args[1]
        currentDirs=glob.glob(dataDirName+animalName+'\\t*')
        startInt=len(dataDirName)+len(animalName)+3
        mxdir=0;
        for d in currentDirs:
            this=int(d[startInt:len(d)])
            mxdir=max(mxdir,this)
        expName='t{0:05.0f}'.format(mxdir+1)
        return expName
   
          
         
         