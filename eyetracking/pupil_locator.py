# pupil_locator.py:  Pupil Locator
# Author: Matthew McCann (@mkm4884)
# Max Planck Florida Institute for Neuroscience (MPFI)
# Date Created: 09/14/016
# Last Modified: 03/09/2017

# Description: A pipelined feature finder to process frames acquired from high speed camera.
# Frames a preprocessed with contrast, brightness, and gamma adjustment. The framesa nd

# [1] Zoccolan, D. et al. (2010) A self-calibrating, camera-based eye tracker for the 
# recording of rodent eye movements. Front. Neurosci. 4, 193.

from numpy import *
import cv2
import time
from Queue import Queue
from stopwatch import clockit
from image_processing import *
from devices.video_file_reader import *
from calibrator.StahlLikeCalibrator import *


class PupilLocator:
    
    def __init__(self, in_queue, ff, guess, filename, **kwargs):

        # define function handles. Online and offline calls result in different handling and display procedures
        self.online = kwargs.get('online', True)
        if self.online:
            self._unpack = self.unpack_online
            self._display = self.display_online
        else:
            self._unpack = self.unpack_offline
            self._display = self.display_offline

        # define flags
        self.stopFlag = False

        # define queues
        self.in_queue = in_queue

        # get feature finder from parent
        self.last = None
        self.ff = ff
        self.calibrator = StahlLikeCalibrator(None, ff, )
        self.guess = guess
        self.reset = False
        self.features = None

        # Number of frames to average
        self.num_frames = kwargs.get('num_frames', 1)

        # Set counter
        self.count = 0
        self.smoothing_samples = 60 * 3
        self.rad_tracker = 20

        # Brightness, Contrast, Gamma Correction
        self.contrast = kwargs.get('contrast', 1)
        self.brightness = kwargs.get('brightness', 0)
        self.gamma = kwargs.get('gamma', 1)

        # data containers
        self.table = None
        self.images = []
        self.frames = []
        self.ts = []
        self.num = []
        self.pupil_avg = [self.guess['pupil_position']] * self.smoothing_samples
        self.cr_avg = [self.guess['cr_position']] * self.smoothing_samples
        self.pupil_rad_avg = [self.ff.pupil_ray_length] * self.rad_tracker
        self.cr_rad_avg = [self.ff.cr_ray_length] * self.rad_tracker

        # display settings
        self.showSobel = True
        self.showFit = False
        self.showAdjFit = False
        self.showRaw = False

        # Extra arguments from keywords
        self.fullGazeTracking = kwargs.get('full_gaze', False)
        self.ROI = kwargs.get('ROI', [])
        self.ROI_diff = kwargs.get('ROI_diff', [0, 0])
        self.save_vid = kwargs.get('save_vid', True)
        self.save_log = kwargs.get('save_log', True)

        # set up basis for circular mask to get luminance values
        self.height = self.ROI[1][1] - self.ROI[0][1]
        self.width = self.ROI[1][0] - self.ROI[0][0]
        self.circle_img = zeros((self.height, self.width), uint8)

        # set up basis for elliptical mask when adjusting image
        self.eye_mask = self.circle_img.copy()
        self.ellipse = kwargs.get('ellipse', None)
        if self.ellipse:
            cv2.ellipse(self.eye_mask, self.ellipse, 255, thickness=-1)

        # create video saving object in openCV to save output file
        path = filename.rsplit('.', 1)
        self.video = None
        self.logFile = None

        if self.save_vid:
            self.frameRate = 60                                             # Set framerate at which video is saved
            fourcc = cv2.cv.CV_FOURCC(*'MJPG')                              # Save as .avi
            self.filename = filename
            vidPath = str(path[0]) + "_pupil_track.avi"
            self.video = cv2.VideoWriter(vidPath, fourcc, self.frameRate, (640, 480), False)
            # self.video = cv2.VideoWriter(vidPath, fourcc, self.frameRate, (self.ROI[1][1]-self.ROI[0][1], self.ROI[1][0]-self.ROI[0][0]), False)

        # create log file for eye tracking data
        if self.save_log:
            # start data logging
            self.logFilePath = str(path[0]) + "_eye_data.txt"
            self.logFile = open(self.logFilePath, 'w')
            # write a header for ROI if we want to validate with offline analysis
            self.logFile.write("ROI: " + str(self.ROI) + "\n")
            # make it human readable
            self.logFile.write("frame_number timestamp pupil_position_x pupil_position_y pupil_radius cr_position_x cr_position_y cr_radius elevation azimuth "
                               "luminance pupil_orientation pupil_short_axis\n\n")
            self.logFile.close()

        self.update_parameters()

    def update_parameters(self):
        # make lookup table for gamma correction
        # adjust gamma - build a lookup table mapping the pixel values [0, 255] to their adjusted gamma values
        self.table = array([((i / 255.0) ** (1.0 / self.gamma)) * 255 for i in range(0, 256)]).astype("uint8")

    def reset_guess(self, new_guess):
        # Reset guess
        del self.pupil_avg[:], self.cr_avg[:], self.pupil_rad_avg[:], self.cr_rad_avg[:], self.guess
        self.guess = new_guess.copy()
        # clear window averages and reset
        pup = self.guess['pupil_position']
        cr = self.guess['cr_position']
        self.pupil_avg = [pup] * self.smoothing_samples
        self.cr_avg = [cr] * self.smoothing_samples
        self.pupil_rad_avg = [self.ff.pupil_ray_length] * self.rad_tracker
        self.cr_rad_avg = [self.ff.cr_ray_length] * self.rad_tracker
        # reset flag
        self.reset = False

    def unpack_online(self):
        """ Online data doesn't send both a full frame and ROI, but just the ROI to speed computation and limit memory consumption
        Unlike in offline processing, the data saved as 'frame' in the queue is just the ROI of the full frame."""
        if self.count == 0:
            # Create FIFO buffer for moving average
            for i in range(0, self.num_frames):
                data = self.in_queue.get()
                frame = data['frame']
                timestamp = data['timestamp']
                frame_num = data['frame_number']
                subset_adj = self.adjust_image(frame.copy())
                self.ts.append(timestamp)
                self.num.append(frame_num)
                self.images.append(subset_adj)
                del data
            self.count += 1
            return frame
        else:
            if self.in_queue.empty() and len(self.images) == 0:
                self.stopFlag = True
                self.stopThread()
            else:
                data = self.in_queue.get()
                frame = data['frame']
                timestamp = data['timestamp']
                frame_num = data['frame_number']
                subset_adj = self.adjust_image(frame.copy())
                self.ts.append(timestamp)
                self.num.append(frame_num)
                self.images.append(subset_adj)
                del data
                self.count += 1
                return frame

    def unpack_offline(self):
        """
        Offline processing sends both an ROI and the full frame in order to save movies with the fit.
        Returns: unpacked data
        """
        if self.count == 0:
            # Create FIFO buffer for moving average
            for i in range(0, self.num_frames):
                data = self.in_queue.get()
                frame = data['frame']
                subset = data.get('subset', None)
                timestamp = data['timestamp']
                frame_num = data['frame_number']
                subset_adj = self.adjust_image(subset.copy())
                self.ts.append(timestamp)
                self.num.append(frame_num)
                self.images.append(subset_adj)
                self.frames.append(frame)
                del data
            self.count += 1
            return subset
        else:
            if self.in_queue.empty() and len(self.images) == 0:
                self.stopFlag = True
                self.stopThread()
            else:
                data = self.in_queue.get()
                frame = data['frame']
                subset = data.get('subset', None)
                timestamp = data['timestamp']
                frame_num = data['frame_number']
                subset_adj = self.adjust_image(subset.copy())
                self.ts.append(timestamp)
                self.num.append(frame_num)
                self.images.append(subset_adj)
                self.frames.append(frame)
                del data
                self.count += 1
                return subset

    def display_offline(self, image, pupil_position, cr_position, pupil_bounds):

        # Get main frames and if first choice is empty, grab next from stack
        if self.frames[0] is not None:
            self.final_frame = self.frames[0]
            subset = self.images[0]
        else:
            self.final_frame = self.frames[1]
            subset = self.images[1]

        if self.showRaw:
            # do nothing
            pass

        elif self.showFit:
            write_im = image

            cv2.circle(write_im, (int(cr_position[1]), int(cr_position[0])), 3, (255, 255, 255))
            cv2.circle(write_im, (int(pupil_position[1]), int(pupil_position[0])), 3, (255, 255, 255))

            for b in pupil_bounds:
                cv2.circle(write_im, (int(b[1]), int(b[0])), 1, (255, 255, 255))

            self.final_frame[self.ROI[0][1]:self.ROI[1][1], self.ROI[0][0]:self.ROI[1][0]] = write_im

        elif self.showAdjFit:
            write_im = subset

            cv2.circle(write_im, (int(cr_position[1]), int(cr_position[0])), 3, (255, 255, 255))
            cv2.circle(write_im, (int(pupil_position[1]), int(pupil_position[0])), 3, (255, 255, 255))

            for b in pupil_bounds:
                cv2.circle(write_im, (int(b[1]), int(b[0])), 1, (255, 255, 255))

            self.final_frame[self.ROI[0][1]:self.ROI[1][1], self.ROI[0][0]:self.ROI[1][0]] = write_im

        elif self.showSobel:
            write_im, _, _ = self.sobel_cv(subset)

            cv2.circle(write_im, (int(cr_position[1]), int(cr_position[0])), 3, (255, 255, 255))
            cv2.circle(write_im, (int(pupil_position[1]), int(pupil_position[0])), 3, (255, 255, 255))

            for b in pupil_bounds:
                cv2.circle(write_im, (int(b[1]), int(b[0])), 1, (255, 255, 255))

            self.final_frame[self.ROI[0][1]:self.ROI[1][1], self.ROI[0][0]:self.ROI[1][0]] = write_im

        cv2.imshow('Fit', self.final_frame)
        cv2.waitKey(1) & 0xFF
        del self.frames[0]

    def display_online(self, image, pupil_position, cr_position, pupil_bounds):

        if image is not None:
            self.final_frame = image
            subset = self.images[0]
        else:
            self.final_frame = self.frames[1]
            subset = self.images[1]

        if self.showRaw:
            pass

        elif self.showFit:
            write_im = image

            cv2.circle(write_im, (int(cr_position[1]), int(cr_position[0])), 3, (255, 255, 255))
            cv2.circle(write_im, (int(pupil_position[1]), int(pupil_position[0])), 3, (255, 255, 255))

            for b in pupil_bounds:
                cv2.circle(write_im, (int(b[1]), int(b[0])), 1, (255, 255, 255))

            self.final_frame = write_im

        elif self.showAdjFit:
            write_im = subset

            cv2.circle(write_im, (int(cr_position[1]), int(cr_position[0])), 3, (255, 255, 255))
            cv2.circle(write_im, (int(pupil_position[1]), int(pupil_position[0])), 3, (255, 255, 255))

            for b in pupil_bounds:
                cv2.circle(write_im, (int(b[1]), int(b[0])), 1, (255, 255, 255))

            self.final_frame = write_im

        elif self.showSobel:
            write_im, _, _ = self.sobel_cv(subset)

            cv2.circle(write_im, (int(cr_position[1]), int(cr_position[0])), 3, (255, 255, 255))
            cv2.circle(write_im, (int(pupil_position[1]), int(pupil_position[0])), 3, (255, 255, 255))

            for b in pupil_bounds:
                cv2.circle(write_im, (int(b[1]), int(b[0])), 1, (255, 255, 255))

            self.final_frame = write_im

        cv2.imshow('Fit', self.final_frame)
        cv2.waitKey(1) & 0xFF

    def adjust_image(self, image):
        """
        Args:
            image: image to be processed
            gamma: value for gamma. Set by GUI
            contrast:  value for contrast. Set by GUI
            brightness: int for brightess. Set by GUI

        Returns: processed image
        """

        # adjust contrast and brightness
        image = image * self.contrast + self.brightness
        # Set thresholds - prevent values form falling outside 8-bit range
        image[image < 0] = 0
        image[image > 255] = 255
        image = image.astype('uint8')
        image1 = image.copy()
        image1 = cv2.bitwise_and(image1, image1, mask=self.eye_mask)
        # apply gamma correction using the lookup table
        image1 = cv2.LUT(image1, self.table)
        # Equalize histogram across the image to get pupil enhancement
        image1 = cv2.equalizeHist(image1)
        # Smooth image
        image1 = cv2.blur(image1, (5, 5))
        el = [image1 != 0]
        image[el] = image1[el]
        return image

    def get_luminance(self, image, pupil_position, pupil_radius, cr_position, cr_radius):
        """

        Args:
            image:
            pupil_position:
            pupil_radius:
            cr_position:
            cr_radius:

        Returns: average luminance from area of circle centered on the pupil center with half the radius of the pupil. Removes CR artifact from calculation.

        """
        # Copy zeros array
        mask_img1 = self.circle_img.copy()
        mask_img2 = self.circle_img.copy()
        # Create circular masks for pupil and cr
        cv2.circle(mask_img1, (int(pupil_position[1]), int(pupil_position[0])), int(0.5 * pupil_radius), 255, thickness=-1)
        cv2.circle(mask_img2, (int(cr_position[1]), int(cr_position[0])), int(cr_radius), 255, thickness=-1)
        # isolate masked regions
        lum_pupil = cv2.bitwise_and(image, image, mask=mask_img1)
        lum_cr = cv2.bitwise_and(lum_pupil, lum_pupil, mask=mask_img2)  # finds overlap between lum_pupil and cr mask
        # subtract, normalize, and average
        lum_pupil = lum_pupil - lum_cr
        lum_nonzero = lum_pupil[lum_pupil != 0]
        if lum_nonzero.size == 0:
            return 0.0
        else:
            lum_max = float16(lum_nonzero.max())
            lum_norm = lum_nonzero / lum_max
            return mean(lum_norm)

    def sobel_cv(self, image):

        sobel_c = array([-1, 0, 1])
        sobel_r = array([1, 2, 1])

        imgx = cv2.sepFilter2D(image, cv2.CV_64F, sobel_c, sobel_r, borderType=cv2.BORDER_DEFAULT)
        imgy = cv2.sepFilter2D(image, cv2.CV_64F, sobel_r, sobel_c, borderType=cv2.BORDER_DEFAULT)

        mag = sqrt(imgx ** 2 + imgy ** 2)
        mag = cv2.blur(mag, (7, 7))

        return mag.astype(uint8), imgx.astype(uint8), imgy.astype(uint8)

    def log_results(self, timestamp, frame_number, pupil_position_x, pupil_position_y, pupil_radius, cr_position_x, cr_position_y, cr_radius, elevation,
                    azimuth, luminance, pupil_orientation, pupil_short_axis):
        """Create a space-separated value file to log eye tracking estimates"""
        line = str(frame_number) + " " + str(timestamp) + " " + str(pupil_position_x) + " " + str(pupil_position_y) + " " + str(pupil_radius) + " " + \
               str(cr_position_x) + " " + str(cr_position_y) + " " + str(cr_radius) + " " + str(elevation) + " " + str(azimuth) + " " + str(luminance) + " " \
               + str(pupil_orientation) + " " + str(pupil_short_axis) + "\n"
        with open(self.logFilePath, 'a') as logFile:
            logFile.write(line)

    def startWorkers(self):
        self.stopFlag = False
        thread = threading.Thread(target=self.runFeatureFinder)
        thread.daemon = True
        thread.start()

    def stopThread(self):
        # When everything done, release the capture
        if self.video is not None:
            self.video.release()
        time.sleep(0.5)
        cv2.destroyWindow('Fit')

    def runFeatureFinder(self):

        while not self.stopFlag:

            # kill if flag is thrown
            if self.stopFlag:
                self.stopThread()

            # Unpack data. Goes to either unpack_offline() or unpack_online()
            if not self.in_queue.empty():
                subset = self._unpack()
            else:
                self.stopThread()

            # Process data
            if len(self.images) > 0:
                # Run feature finder and get results
                self.ff.analyze_image(self.images, self.guess)
                self.features = self.ff.get_result()

                # Extract relevant parameters from features dictionary
                timestamp = self.ts[0]
                frame_num = self.num[0]
                pupil_position = self.features['pupil_position']
                pupil_position_x = pupil_position[1] + self.ROI_diff[1]  # correct for ROI selection in reference to full frame
                pupil_position_y = pupil_position[0] + self.ROI_diff[0]  # correct for ROI selection in reference to full frame
                pupil_radius = self.features['pupil_radius']
                cr_position = self.features['cr_position']
                cr_position_x = cr_position[1] + self.ROI_diff[1]  # correct for ROI selection in reference to full frame
                cr_position_y = cr_position[0] + self.ROI_diff[0]  # correct for ROI selection in reference to full frame
                cr_radius = self.features['cr_radius']
                pupil_orientation = self.features['pupil_orientation']
                pupil_short_axis = self.features['pupil_short_axis']

                # if the feature finder didn't find anything interesting, return
                if cr_position is None or pupil_position is None:
                    return

                # find luminance in circular region of 0.5x calculated pupil radius centered at calculated pupil center
                luminance = self.get_luminance(self.images[0], pupil_position, pupil_radius, cr_position, cr_radius)

                # Find mean position of pupil and cr if list is populated with more than one value
                mean_pupil = mean(self.pupil_avg, axis=0)
                mean_cr = mean(self.cr_avg, axis=0)
                # Same for radius info
                mean_pupil_rad = mean(self.pupil_rad_avg, axis=0)
                mean_cr_rad = mean(self.cr_rad_avg, axis=0)

                # This should catch cases where nothing is found and the starburst algorithm defaults to [-1, -1]
                # If there is a large perturbation, such as an eye blink, don't update guess because data will be bad
                pupil_diff = linalg.norm(pupil_position - mean_pupil)
                cr_diff = linalg.norm(cr_position - mean_cr)
                pupil_cr_diff = linalg.norm(pupil_position - cr_position)

                if pupil_position.any() == -1 or cr_position.any() == -1 or pupil_cr_diff >= 0.3 * mean_pupil_rad:
                    pass
                else:
                    if pupil_diff > mean_pupil_rad * 0.3:
                        pass
                    else:
                        self.guess['pupil_position'] = pupil_position

                    if cr_diff > 0.3 * mean_cr_rad:
                        pass
                    else:
                        self.guess['cr_position'] = cr_position

                # Add things to list, and delete first element if list is full
                # Just checking if one of them is the necessary length is enough to guarantee requirements are met for both
                if len(self.pupil_avg) < self.smoothing_samples:
                    self.pupil_avg.append([pupil_position[1], pupil_position[0]])
                    self.cr_avg.append([cr_position[1], cr_position[0]])
                elif len(self.pupil_avg) == self.smoothing_samples:
                    del self.pupil_avg[0], self.cr_avg[0]
                    self.pupil_avg.append([pupil_position[1], pupil_position[0]])
                    self.cr_avg.append([cr_position[1], cr_position[0]])

                # Ditto for radius info
                if len(self.pupil_rad_avg) < self.rad_tracker:
                    self.pupil_rad_avg.append(pupil_radius)
                    self.cr_rad_avg.append(cr_radius)
                elif len(self.pupil_rad_avg) == self.rad_tracker:
                    del self.pupil_rad_avg[0], self.cr_rad_avg[0]
                    self.pupil_rad_avg.append(pupil_radius)
                    self.cr_rad_avg.append(cr_radius)

                # Get gaze values
                # These will be garbage if any of the positions are [-1, -1], but we can check for those post-hoc
                if self.fullGazeTracking:
                    elevation, azimuth = self.calibrator.transform(pupil_position, cr_position)
                else:
                    elevation = azimuth = 0.0

                # display sequence
                sb = self.features['starburst']
                pupil_bounds = sb['pupil_boundary']

                # calls either display_online() or display_offline()
                self._display(subset, pupil_position, cr_position, pupil_bounds)

                # if applicable, save the video and eye tracking data
                if self.save_vid:
                    self.video.write(self.final_frame)
                if self.save_log:
                    # write to file
                    self.log_results(timestamp, frame_num, pupil_position_x, pupil_position_y, pupil_radius, cr_position_x, cr_position_y, cr_radius, elevation,
                                     azimuth, luminance, pupil_orientation, pupil_short_axis)

                # housekeeping
                del self.images[0], self.ts[0], self.num[0]

            else:
                continue
