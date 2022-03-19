#!/usr/bin/env python
from __future__ import print_function
import sys
import math
import numpy as np

#ROS Imports
import rospy
from sensor_msgs.msg import Image, LaserScan
from ackermann_msgs.msg import AckermannDriveStamped, AckermannDrive

speed = 0

class reactive_follow_gap:
    def __init__(self):
        #Topics & Subscriptions,Publishers
        lidarscan_topic = '/scan'
        drive_topic = '/vesc/high_level/ackermann_cmd_mux/input/nav_0' #make new topic

        self.lidar_sub = rospy.Subscriber(lidarscan_topic, LaserScan, self.lidar_callback) #TODO
        self.drive_pub = rospy.Publisher(drive_topic, AckermannDriveStamped, queue_size = 10) #TODO
    
    def preprocess_lidar(self, ranges):
        """ Preprocess the LiDAR scan array. Expert implementation includes:
            1.Setting each value to the mean over some window
            2.Rejecting high values (eg. > 3m)
        """

	proc_ranges = [0] * 120
	count = 0
	#ranges from 0-180 degrees
	#for i in range(270, 810, 3): 
	for i in range(360, 720, 3):
	    mean = (ranges[i] + ranges[i+1] + ranges[i+2]) / 3
	    proc_ranges[count] = mean
	    #rospy.loginfo("proc_ranges[%d]: %f", count, proc_ranges[count])
	    count += 1
	
        return proc_ranges

    def find_max_gap(self, free_space_ranges):
        """ Return the start index & end index of the max gap in free_space_ranges
        """
	gap1_start = None
	gap1_end = None
	gap2_start = None
	gap2_end = None
	for i in range(len(free_space_ranges)):
	    #gap 1 start
	    if (free_space_ranges[i] != 0 and gap1_start == None):
	        gap1_start = i
	    #gap 1 end
	    if (gap1_end == None and free_space_ranges[i+1] == 0):
	        gap1_end = i
	    #gap 2 start
	    if (free_space_ranges[i-1] == 0):
		gap2_start = i
	    #gap 2 end
	    if (free_space_ranges[i] != 0):
		gap2_end = i
	
	if (gap1_end - gap1_start > gap2_end - gap2_start):
	    max_gap = [gap1_start, gap1_end]
	else:
	    max_gap = [gap2_start, gap2_end]
	#max_gap = [max_start_i, max_end_i]
	#rospy.loginfo("max gap start: %f", max_gap[0])
	#rospy.loginfo("max gap end: %f", max_gap[1])
        return max_gap
    
    def find_best_point(self, start_i, end_i, ranges):
        """Start_i & end_i are start and end indicies of max-gap range, respectively
        Return index of best point in ranges
	Naive: Choose the furthest point within ranges and go there
        """
	global speed
	#Naive approach
	farthest_dist = 0
	farthest_pt = 90
	for i in range(start_i, end_i):
	    if ranges[i] > farthest_dist:
	        farthest_dist = ranges[i]
		farthest_pt = i

	#if car is 3-4m away from closest obstacle should you immediately make a sharp turn to avoid it?
	#Choose speed based on distance
	if (farthest_dist > 3):
	    speed = 2.0
	elif (farthest_dist > 1 and farthest_dist <=3):
	    speed = 1.5
	else:
	    speed = 1.0
	
        return farthest_pt

    def lidar_callback(self, data):
        """ Process each LiDAR scan as per the Follow Gap algorithm & publish an AckermannDriveStamped Message
        """
	global speed
        ranges = data.ranges
        proc_ranges = self.preprocess_lidar(ranges)
	angle = 0

        #Find closest point to LiDAR
        closest = 100
	closest_degree = None
	for i in range(len(proc_ranges)):
	    #rospy.loginfo("degree: %f", i)
	    #rospy.loginfo("proc_range[%d]: %f", i, proc_ranges[i])
            if proc_ranges[i] < closest:
	        closest = proc_ranges[i]
                closest_degree = i
	#rospy.loginfo("closest degree: %f", closest_degree + 30)

        #Eliminate all points inside 'bubble' (set them to zero) 
	#radius = 5
	if (closest_degree != None):
	    proc_ranges[closest_degree] = 0
	if (closest_degree != 119):
	    proc_ranges[closest_degree+1] = 0
	if (closest_degree != 0):
	    proc_ranges[closest_degree-1] = 0
	if (closest_degree+1 < 119):
	    proc_ranges[closest_degree+2] = 0
	if (closest_degree-1 > 0):
	    proc_ranges[closest_degree-2] = 0

#	for i in range(len(proc_ranges)):
	    #rospy.loginfo("degree: %f", i)
	    #rospy.loginfo("proc_range[%d]: %f", i, proc_ranges[i])

        #Find max length gap 
	max_gap = self.find_max_gap(proc_ranges)

        #Find the best point in the gap 
	best_point = self.find_best_point(max_gap[0], max_gap[1], proc_ranges)
	#rospy.loginfo("best point: %f", best_point + 30)

	#Calculate steering angle relative to best point in radians
	angle = math.radians(best_point + 30 - 90)
	#rospy.loginfo("angle: %f(rad)", angle)

        #Publish Drive message
	drive_msg = AckermannDriveStamped()
        drive_msg.header.stamp = rospy.Time.now()
        drive_msg.header.frame_id = "laser"
	drive_msg.drive.steering_angle = angle
	#if (closest < 0.3):
	    #angle = math.radians(best_point - 90)
	 #   drive_msg.drive.speed = 1.0
	#else:
	#    drive_msg.drive.speed = 2.0
	drive_msg.drive.speed = 2.0
	self.drive_pub.publish(drive_msg)

def main(args):
    rospy.init_node("FollowGap_node", anonymous=True)
    rfgs = reactive_follow_gap()
    rospy.sleep(0.1)
    rospy.spin()

if __name__ == '__main__':
    main(sys.argv)
