# video_file_reader.py:  Video Reader
# Author: Matthew McCann (@mkm4884)
# Max Planck Florida Institute for Neuroscience
# Created 09/06/2016
# Last Modified 10/03/2016

# Description: Read video stream from previously acquired video file. Extracts timestamp, 
# framerate, and frame number information and adds each frame + info to a queue. 
# For use with the ShrewDriver software package (Theo Walker, MPFI). 
# Modified from code originally written by Theo Walker.

################# System Modules #################
from __future__ import division
import cv2
import time
import threading
from numpy import reshape, array


class VideoReader:
    
    def __init__(self, vidPath, **kwargs):
        
        # ------------------------------------------------------------
        # set up frame acquisition, display, and file saving
        # ------------------------------------------------------------
        
        # get other variables from keyword argumants
        self.enable_display = kwargs.get("enable_display", True)            # display recorded video on screen
        self.out_queue = kwargs.get("image_queue", None)              # output queue for images and frame data
        
        self.windowName = vidPath  # name display window
        self.ROI = kwargs.get("roi", [])
        # Use previously recorded video as input stream
        self.cap = cv2.VideoCapture(vidPath)

        self.stopFlag = False                                               # initialize flag to end image acquisition as FALSE (that is, run continuously for now)
        
        # ------------------------------------------------------------
        # Initialize variables
        # ------------------------------------------------------------
        self.finished = False
        
        self.timestamp = 0                                               # initialize timestamp
        self.frame_number = 0                                            # initialize frame number
        self.frame_rate = 0                                              # initialize frame rate

    ###################### Functions to Acquire and Save Video ######################
        
    def readFrame(self, **kwargs):
        self.ret, self.frame = self.cap.read()

        if 'send' in kwargs:
            return cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

    def displayVid(self):
        # Displays previously recorded video feed in new window
        self.readFrame() 
        
        #If we are at the end of the video, end process
        if self.frame is None or not self.ret:
            self.stopFlag = True
            self.stopCameraThread()

        else:
            #Once in a while, a bad frame comes off the camera. Skip it
            rows, cols, chans = self.frame.shape
            if rows == 0 or cols == 0:
                return

            if len(self.frame.shape) > 2:
                self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

            #self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)               # display image in greyscale
            cv2.imshow(self.windowName, self.frame)
            cv2.waitKey(17) & 0xFF
            
    def runVideo(self):
        # thread function, loops capture until stopped
        # blocking happens automatically at self.cap.read() so this won't consume much CPU.
        # No need for a sleep() call.
        
        while not self.stopFlag:
            
            # Check if stop flag has been thrown
            if self.stopFlag:
                self.stopCameraThread()
                break
            else:

                # If we don't want to see the displayed video
                if not self.enable_display:
                    self.readFrame()
                    
                # If we want to see the displayed video    
                else:
                    self.displayVid()

                # Get frame number, timestamp, and frame rate    
                self.frame_number = self.cap.get(cv2.cv.CV_CAP_PROP_POS_FRAMES)  # log number of frames acquired  
                self.timestamp = self.cap.get(cv2.cv.CV_CAP_PROP_POS_MSEC)       # get timestamp of video  
                self.frame_rate = self.cap.get(cv2.cv.CV_CAP_PROP_FPS)           # get framerate of video
                                         
                # Create dictionary with frame, timestamp, and frame number and add to queue
                if self.ROI and self.frame is not None:
                    self.subset = array(self.frame[self.ROI[0][1]:self.ROI[1][1], self.ROI[0][0]:self.ROI[1][0]])

                data = {'frame': self.frame, 'subset': self.subset, 'frame_number': self.frame_number, 'timestamp': self.timestamp}
                if self.out_queue is not None:
                    self.out_queue.put(data)

    def startReadThread(self):
        self.stopFlag = False
        thread = threading.Thread(target = self.runVideo)
        thread.daemon = True
        thread.start()

    def stopCameraThread(self):
        # When everything done, release the capture
        print 'Stop'
        cv2.waitKey(1) & 0xFF
        self.cap.release()
        cv2.destroyWindow(self.windowName)
        self.finished = True
        return self.finished


"""Test Code"""
if __name__ == '__main__':
    from Queue import Queue
    from image_processing.ROISelect import *

    #set up CameraReader object
    im_q = Queue()
    vidPath = 'C:\Users\mccannm\Desktop\Test_Data\Baby_vid_short_adjust.mp4'
    get_roi = ROISelect('video', vidPath=vidPath)
    get_roi.findROI()
    verticesROI, frame_size, pupil, cr = get_roi.getData()
    cr = VideoReader(vidPath, image_queue=im_q, roi=verticesROI)

    #start it running
    cr.startReadThread()

    #keep busy while it runs
    startTime = time.time()
    while time.time() - startTime < 45:
        data = im_q.get()
        frame = data['frame']
        cv2.imshow("ROI", frame)
        cv2.waitKey(1) & 0xFF
        pass
    
    #stop it, and wait for it to shut down nicely
    cr.stopFlag = True
    time.sleep(1)
    print 'Done'