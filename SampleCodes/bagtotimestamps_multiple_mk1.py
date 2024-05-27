
import os 
import rosbag
cwd=os.getcwd()
bag_folder = "/media/abinmath/Drive2/17-05-22_17-02-09_Done/images1"


save_folder = cwd

import cv2 #opencv library

from cv_bridge import CvBridge, CvBridgeError #cvbridge allows conversion from ros image message to opencv image 

timestamps=[]
count = 0
# def extract(dirs,filename):
# 	global count
# 	bag = rosbag.Bag(dirs + "//" + filename)
# 	for topic, msg, t in bag.read_messages(topics=['/camera3/usb_cam3/image_raw/compressed']):  # mention topics to be extracted example taken from rosbag wiki
# 	    """
# 	    topics can be found on a ubuntu system installed with ROS by typing in cmd line   $ rosbag info something.bag 
# 	    """
# 	    #bridge = CvBridge() 
# 	    #try:
# 		#frame =  cvv.bridge.imgmsg_to_cv2(ros_image, "bgr8")
# 		#cv_img = bridge.compressed_imgmsg_to_cv2(msg ) #compressed_imgmsg_to_cv2(msg, desired_encoding="passthrough") #allows compressed image msg to be converted to cv2 image
# 	    #except CvBridgeError, e:
# 		#print e
# 	    #filename = save_folder + 'frame_' + str(count)+ '_' + str(t) + '.png' 
# 	    #with open(filename, 'w' ) as text_file: #open/make file with filename
# 		#cv2.imwrite(filename, cv_img)  #save image file
# 	    #break
# 		#timestamps.append(str(t))
# 	    #print t
# 	    #print count
# 		count +=1 #update count
# 	bag.close()

def extract_1(dirs, filename):
	bag = rosbag.Bag(dirs + "//" + filename)
	count = 0
	for topic, msg, t in bag.read_messages(topics=['/camera3/usb_cam3/image_raw/compressed']):
		count+=1
		timestamps.append(str(t))
	bag.close()


for (root,dirs,files) in os.walk(bag_folder): 
	for file in sorted(files):
		print(file)
		extract_1(root, file)
		#break
with open(cwd+'/images1_timestamps.txt','a') as f:
	f.write('\n'.join(timestamps))
	f.close()


