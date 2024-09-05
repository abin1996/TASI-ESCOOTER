import rosbag
import os

bagfile = "/home/pate2372/TASI/Work/other_data/1/other_2024-05-29_15-06-03_0.bag"
bag = rosbag.Bag(bagfile)
for topic, msg, t in bag.read_messages(topics=['/tf_static']):
    print(f"Topic: {topic}, Message: {msg}")
bag.close()