#include <ros/ros.h>
#include <nav_msgs/Odometry.h>
#include <sensor_msgs/LaserScan.h>
#include <cmath>
#include <algorithm>
#include <ackermann_msgs/AckermannDriveStamped.h>
#include <std_msgs/Bool.h>

// TODO: include ROS msg type headers and libraries

class Safety {
// The class that handles emergency braking
private:
    ros::NodeHandle n;
    double speed;
    // TODO: create ROS subscribers and publishers
    ros::Subscriber scan_sub;
    ros::Subscriber odom_sub;
    ros::Publisher drive_pub;
    ros::Publisher brake_pub;

public:
    Safety() {
        n = ros::NodeHandle();
        speed = 0.0;
        scan_sub = n.subscribe("scan", 1000, &Safety::scan_callback, this);
        odom_sub = n.subscribe("odom", 1000, &Safety::odom_callback, this);
        drive_pub = n.advertise<ackermann_msgs::AckermannDriveStamped>("brake", 1);
        brake_pub = n.advertise<std_msgs::Bool>("brake_bool", 1);
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
        
    }
    void odom_callback(const nav_msgs::Odometry::ConstPtr &odom_msg) {
        // TODO: update current speed
        float x_velocity = odom_msg->twist.twist.linear.x;
        std::string x_string = std::to_string(x_velocity);
        const char *x_array = x_string.c_str();
        speed = x_velocity;
    }

    void scan_callback(const sensor_msgs::LaserScan::ConstPtr &scan_msg) {
        ackermann_msgs::AckermannDriveStamped drive_msg;
        std_msgs::Bool brake_msg;

        // TODO: calculate TTC
        float angle_min = scan_msg->angle_min;
        float angle_max = scan_msg->angle_max;
        float angle_increment = scan_msg->angle_increment;
        std::vector<float> ranges = scan_msg->ranges;

        // TODO: publish drive/brake message

        std::string tmp_string = "";
        const char *tmp_array;
        float ttc = 100;
        for(int i = 0; i < ranges.size(); i++){
            tmp_string = std::to_string(ranges[i]);
            tmp_array = tmp_string.c_str();
            float theta = angle_min + (i * angle_increment);
            float temp_ttc = time_to_collision(speed, ranges[i], theta);
            if(temp_ttc != 0 && temp_ttc < 100){
                ttc = temp_ttc < ttc ? temp_ttc : ttc;
                //ROS_INFO("%f", temp_ttc);
            }
        }
        if(ttc < 0.5){
            ROS_INFO("STOP!");
            ROS_INFO("TTC: %f", ttc);
            drive_msg.drive.speed = 0;
            drive_pub.publish(drive_msg);
            brake_msg.data = true;
            brake_pub.publish(brake_msg);
        }
    }

    float time_to_collision(double velocity, float distance, float theta){
        float time_derivative = velocity * cos(theta);
        float max = time_derivative > 0 ? time_derivative : 0;
        float ttc = distance / max;
        return ttc;
    }

};
int main(int argc, char ** argv) {
    ros::init(argc, argv, "safety_node");
    Safety sn;
    ros::spin();
    return 0;
}