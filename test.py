from openni import openni2
OPENNI_FOLDER_PATH = r'./OpenNI-Linux-x64-2.3/Redist'
openni2.initialize(OPENNI_FOLDER_PATH)
# dev = openni2.Device.open_file('cap1.oni'.encode('utf-8'))
dev = openni2.Device('cap2.oni'.encode('utf-8'))
playback = openni2.PlaybackSupport(dev)
depth_stream = dev.create_depth_stream()
depth_stream.start()
print('Prepare...')
playback.seek(depth_stream, 20)
print('Ok')

# # Clear windows
# blank_image = np.zeros((depth_frame.height, depth_frame.width, 3), np.uint8)
# cv2.imshow('Depth', blank_image)
# cv2.imshow("Color", blank_image)
