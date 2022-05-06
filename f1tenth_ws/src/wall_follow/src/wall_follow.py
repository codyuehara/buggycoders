#!/usr/bin/env python
from __future__ import print_function
import sys
import math
import numpy as np

#ROS Imports
import rospy
from sensor_msgs.msg import Image, LaserScan
from ackermann_msgs.msg import AckermannDriveStamped, AckermannDrive

#PID CONTROL PARAMS
kp = 1 #TODO
kd = 0.09 #TODO
ki = 0 #TODO
servo_offset = 0.0
prev_error = 0.0 
error = 0.0
integral = 0.0
derivative = 0.0

#WALL FOLLOW PARAMS
ANGLE_RANGE = 270 # Hokuyo 10LX has 270 degrees scan
DESIRED_DISTANCE_RIGHT = 0.9 # meters
#DESIRED_DISTANCE_LEFT = 0.55
DESIRED_DISTANCE_LEFT = 0.55
VELOCITY = 2.00 # meters per second
CAR_LENGTH = 0.50 # Traxxas Rally is 20 inches or 0.5 meters

class WallFollow:
    """ Implement Wall Following on the car
    """
    def __init__(self):
        #Topics & Subs, Pubs
        lidarscan_topic = '/scan'
        drive_topic = '/vesc/high_level/ackermann_cmd_mux/input/nav_1'

        self.lidar_sub = rospy.Subscriber(lidarscan_topic, LaserScan, self.lidar_callback) #TODO: Subscribe to LIDAR
        self.drive_pub = rospy.Publisher(drive_topic, AckermannDriveStamped, queue_size = 10) #TODO: Publish to drive

    def getRange(self, data, angle):
        # data: single message from topic /scan
        # angle: between -45 to 225 degrees, where 0 degrees is directly to the right
        # Outputs length in meters to object with angle in lidar scan field of view
        #make sure to take care of nans etc.
        #TODO: implement

	#length of data.ranges is 1080
	#rospy.loginfo(len(data.ranges))
	#lidar scan is 360 degrees
	index = (angle * (len(data.ranges)/360)) - 1
	#index = (angle * (len(data.ranges)/270)) - 1
	#rospy.loginfo("ranges[%d]: %f", angle, data.ranges[index])
	length = data.ranges[index]
        return length

    def pid_control(self, error, velocity):
        global integral
        global prev_error
        global kp
        global ki
        global kd
	global derivative
        #TODO: Use kp, ki & kd to implement a PID controller for 

	#derivative = prev_error - error
	if prev_error != 0: 
		derivative = (error - prev_error) / abs(prev_error)
	else:
		derivative = 0.0
	#rospy.loginfo("dedt: %f", derivative)
	
	angle = kp * error + kd * derivative + ki * integral

	#rospy.loginfo("angle: %f", angle)
	prev_error = error
        drive_msg = AckermannDriveStamped()
        drive_msg.header.stamp = rospy.Time.now()
        drive_msg.header.frame_id = "laser"
	drive_msg.drive.steering_angle = angle
	#positive angle is to the left
	drive_msg.drive.speed = 1 #6 - (abs(angle) / 2.35619 * 5)
	#if angle > -10 and angle < 10:
	#	drive_msg.drive.speed = 6.0 #1.5
		#rospy.loginfo("drive straight")
	#elif angle > 10 and angle < 20 or angle > -20 and angle < -10:
	#	drive_msg.drive.speed = 4.0 #1.0
		#rospy.loginfo("turn")
	#else:
	#	drive_msg.drive.speed = 2.0 #0.5
		#rospy.loginfo("idk")
        
        VELOCITY = drive_msg.drive.speed
	
#drive_msg.drive.speed = VELOCITY
        self.drive_pub.publish(drive_msg)

    def followLeft(self, data, leftDist):
        #Follow left wall as per the algorithm 
        #TODO:implement

	a = self.getRange(data, 225)
	#rospy.loginfo("a: %f", a)
	b = self.getRange(data, 270)
	#rospy.loginfo("b: %f", b)

	theta = 45
	theta = math.radians(theta)
	alpha = math.atan((a*math.cos(theta)-b) / (a*math.sin(theta)))
	#rospy.loginfo("alpha(d): %f", math.degrees(alpha))
	dist = b*math.cos(alpha)
	#rospy.loginfo("dist: %f(m)", dist)
	#l = 0.75 original
	l = 0.75 # lookahead distance
	next_dist = dist + l*math.sin(alpha)
	#rospy.loginfo("next_dist: %f(m)", next_dist)
	error = next_dist - DESIRED_DISTANCE_LEFT
	#rospy.loginfo("error: %f(m)", error)
        return error

    def lidar_callback(self, data):
        """ 
        """
        error = self.followLeft(data, DESIRED_DISTANCE_LEFT) #TODO: replace with error returned by followLeft
        #send error to pid_control
        self.pid_control(error, VELOCITY)

def main(args):
    rospy.init_node("WallFollow_node", anonymous=True)
    wf = WallFollow()
    rospy.sleep(0.1)
    rospy.spin()

if __name__=='__main__':
	main(sys.argv)
