from picamera2 import Picamera2
import cv2



picam2 = Picamera2()

picam2.start_and_capture_file("test.png", show_preview = False)

image = cv2.imread('test.png')

image = cv2.resize(image, (0,0), fx=0.25, fy=0.25) 

height, width, channels = image.shape

halfWidth = width//2
left = image[:,:halfWidth]
right = image[:,halfWidth:]

cv2.imwrite("left.png", left)
cv2.imwrite('right.png', right)


