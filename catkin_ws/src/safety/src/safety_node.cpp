#include <ros/ros.h>
#include <nav_msgs/Odometry.h>
#include <sensor_msgs/LaserScan.h>
#include <cmath>
#include <ctime>
#include <ackermann_msgs/AckermannDriveStamped.h>
#include <std_msgs/Bool.h>

// TODO: include ROS msg type headers and libraries

class Safety {
// The class that handles emergency braking
private:
    ros::NodeHandle n;
    double speed;

    // TODO: create ROS subscribers and publishers
    ros::Publisher brake_pub;
    ros::Publisher brake_bool_pub;
    ros::Subscriber scan_sub;
    ros::Subscriber odom_sub;

public:
    Safety() {
        n = ros::NodeHandle();
	speed = 0.0;
        /*
        One publisher should publish to the /brake topic with an
        ackermann_msgs/AckermannDriveStamped brake message.
        One publisher should publish to the /brake_bool topic with a
        std_msgs/Bool message.
        You should also subscribe to the /scan topic to get the
        sensor_msgs/LaserScan messages and the /odom topic to get
        the nav_msgs/Odometry messages
        The subscribers should use the provided odom_callback and 
        scan_callback as callback methods
        NOTE that the x component of the linear velocity in odom is the speed
        */

        // TODO: create ROS subscribers and publishers
	brake_pub = n.advertise<ackermann_msgs::AckermannDriveStamped>("brake", 100);
	brake_bool_pub = n.advertise<std_msgs::Bool>("brake_bool", 100);
	scan_sub = n.subscribe("scan", 10, &Safety::scan_callback, this);
	odom_sub = n.subscribe("odom", 10, &Safety::odom_callback, this);	
    }
    void odom_callback(const nav_msgs::Odometry::ConstPtr &odom_msg) {
        // TODO: update current speed
	speed = odom_msg->twist.twist.linear.x;
    }

    void scan_callback(const sensor_msgs::LaserScan::ConstPtr &scan_msg) {
        // TODO: calculate TTC
	float TTC = 0.0;
	float minTTC = 10.0;
	float threshold = 0.300000;
	std::vector<float> ranges = scan_msg->ranges;
	float angle_min = scan_msg->angle_min;
	float angle_max = scan_msg->angle_max;
	float angle_increment = scan_msg->angle_increment;
	float temp = 0.0;
	float z = 0.0;
	ackermann_msgs::AckermannDriveStamped brake_msg;
	std_msgs::Bool brake_bool_msg;
	  
	int index = 0;
	for (int i = 0; i < 1080; i++) {
	    temp = i / 3;
	    z = speed * cos(temp * M_PI / 180);
	    if (-z > 0.0) {
	        TTC = ranges[i] / (-z);
	       // ROS_INFO("TTC[%d]: %f",i, TTC);	
	    } else {
		TTC = 100;
	    }

	    if (TTC > 0.0 && TTC < minTTC) {
		minTTC = TTC;
	    }  
	    
	}

	if (minTTC < threshold) {
	    ROS_INFO("minTTC: %f", minTTC);	
	    brake_bool_msg.data = true;
	    brake_msg.drive.speed = 0.0;
       	    brake_pub.publish(brake_msg);
	    brake_bool_pub.publish(brake_bool_msg);
	} else { 
	    brake_bool_msg.data = false;
	    brake_bool_pub.publish(brake_bool_msg);
	}

        // TODO: publish drive/brake message	
	//brake_pub.publish(brake_msg);
	//brake_bool_pub.publish(brake_bool_msg);
    }
    

};
int main(int argc, char ** argv) {
    ros::init(argc, argv, "safety_node");
    Safety sn;
    ros::spin();
    return 0;
}
