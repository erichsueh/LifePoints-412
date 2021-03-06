#!/usr/bin/env python
import roslib
import rospy
import smach
import smach_ros
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan

def scan_callback(msg):
    global g_range_ahead
    g_range_ahead = msg.ranges[len(msg.ranges)/2]
    print g_range_ahead



#define state Forward
class Forward(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['Forward', 'Turning'])

    def execute(self, userdata):
        global g_range_ahead
        global cmd_vel_pub
        global state_change_time
        global driving_forward
        global rate
        rospy.loginfo('Executing state Forward')

        if(g_range_ahead < 0.9 or rospy.Time.now() > state_change_time):
            driving_forward = False
            state_change_time = rospy.Time.now() + rospy.Duration(2)

        twist = Twist()
        if driving_forward:
            twist.linear.x = 0.2
        else:
            twist.angular.z = 0.5
        cmd_vel_pub.publish(twist)
        rate.sleep()
        if driving_forward:
            return 'Forward'
        else:
            return 'Turning'


class Turning(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['Forward','Turning'])

    def execute(self, userdata):
        global cmd_vel_pub
        global state_change_time
        global driving_forward
        global rate
        global g_range_ahead
        rospy.loginfo('Executing state Turning')
        if rospy.Time.now() > state_change_time or g_range_ahead > 2.5:
            driving_forward = True
            state_change_time = rospy.Time.now() + rospy.Duration(30)

        twist = Twist()
        if driving_forward:
            twist.linear.x = 0.2
        else:
            twist.angular.z = 0.5
        cmd_vel_pub.publish(twist)
        rate.sleep()
        if driving_forward:
            return 'Forward'
        else:
            return 'Turning'



def main():
    rospy.init_node('wander')

    #Create a SMACH state machine
    sm = smach.StateMachine(outcomes=[])

    #Open the container
    with sm:
        #Add states to the container
        smach.StateMachine.add('Forward', Forward(), transitions = {'Forward':'Forward','Turning':'Turning'})

        smach.StateMachine.add('Turning', Turning(), transitions = {'Forward':'Forward', 'Turning':'Turning'})

    sis = smach_ros.IntrospectionServer('wanderSM', sm, '/SM_ROOT')
    sis.start()
    global g_range_ahead
    global state_change_time
    global driving_forward
    global rate
    g_range_ahead = 1
    scan_sub = rospy.Subscriber('scan', LaserScan, scan_callback)
    global cmd_vel_pub
    cmd_vel_pub = rospy.Publisher('cmd_vel', Twist, queue_size=1)
    state_change_time = rospy.Time.now()
    driving_forward = True
    rate = rospy.Rate(10)

    outcome = sm.execute()
    sis.stop()

if __name__ == '__main__':
    main()