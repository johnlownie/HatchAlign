import threading
import logging
from networktables import NetworkTables
from enum import Enum

cond = threading.Condition()
notified = [False]
robot_modes = Enum("Mode", "sandstorm teleop")
vision_table = None
logging.basicConfig(level=logging.DEBUG)

def connectionListener(connected, info):
    print(info, '; Connected=%s' % connected)
    with cond:
        notified[0] = True
        cond.notify()
        
def init(ip):
    global vision_table
    NetworkTables.initialize(server=ip)
    NetworkTables.addConnectionListener(connectionListener, immediateNotify=True)
    
    with cond:
        print("Waiting...")
        if not notified[0]:
            cond.wait()
            
    vision_table = NetworkTables.getTable("SmartDashboard/Vision")

def publish(rotation, distance):
    global vision_table
    
    if notified[0]:
        vision_table.putNumber("Motor", rotation)
        vision_table.putNumber("Distance", distance)

def getMode():
    if bool(vision_table.getNumber("isTeleop", 1.0)):
        return robot_modes.teleop
    else:
        return robot_modes.sandstorm