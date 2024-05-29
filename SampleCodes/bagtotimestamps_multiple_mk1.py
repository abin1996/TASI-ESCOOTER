
import os 
import bagpy
import time
import pandas as pd
import rosbag
cwd=os.getcwd()
image_folders = [
	"/media/abinmath/Drive2/15-05-22_19-01-19_Done/images1",
	"/media/abinmath/Drive2/15-05-22_19-01-19_Done/images2",
	"/media/abinmath/Drive2/15-05-22_19-01-19_Done/images3",
	"/media/abinmath/Drive2/15-05-22_19-01-19_Done/images4",
	"/media/abinmath/Drive2/15-05-22_19-01-19_Done/images5",
	"/media/abinmath/Drive2/15-05-22_19-01-19_Done/images6",
	# "/media/abinmath/Drive2/17-05-22_17-02-09_Done/images3",
	# "/media/abinmath/Drive2/17-05-22_17-02-09_Done/images6",
]
# bag_folder = "/media/abinmath/Drive2/17-05-22_17-02-09_Done/images1"




import cv2 #opencv library

from cv_bridge import CvBridge, CvBridgeError #cvbridge allows conversion from ros image message to opencv image 



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

def extract_1(dirs, filename, save_folder, topic_name, count, timestamps):
	# bag = bagpy.bagreader(os.path.join(dirs, filename))
	# CAMERA_BAG = bag.message_by_topic('/camera1/usb_cam1/image_raw/compressed')
	# count = 0
	# for topic, msg, t in CAMERA_BAG:
	# 	count+=1
	# 	timestamps.append(str(t))
	bag = rosbag.Bag(dirs + "/" + filename)
	print(bag)

	for topic, msg, t in bag.read_messages(topics=[topic_name]):
		count+=1
		timestamps[count] = str(t)

		# video_frame = CvBridge().compressed_imgmsg_to_cv2(msg)
		#cv2.imshow("Image window", video_frame)
		# cv2.imwrite(save_folder + '/frame_' + str(count)+ '_' + str(t) + '.png', video_frame)
	print(count)
	return timestamps, count

for bag_folder in image_folders:
	start_time = time.time()
	save_folder = cwd + '/'+ bag_folder.split('/')[-1]
	count = 0
	timestamps = {}

	if not os.path.exists(save_folder):
		os.makedirs(save_folder)
	topic_name = '/camera{}/image_color/compressed'.format(bag_folder.split('/')[-1][-1], bag_folder.split('/')[-1][-1])
	print(topic_name)
	for (root,dirs,files) in os.walk(bag_folder): 
		for file in sorted(files):
			print(file)
			timestamps, count = extract_1(root, file, save_folder, topic_name, count, timestamps)
			#break
	save_path = save_folder + '/{}_timestamps.csv'.format(bag_folder.split('/')[-1])
	df = pd.DataFrame(list(timestamps.items()), columns=['Frame Number', 'Timestamp'])
	df.to_csv(save_path, index=False)
	print(f"Saved timestamps to {save_path}")
	print(f"Time taken: {(time.time() - start_time)/60} mins")



