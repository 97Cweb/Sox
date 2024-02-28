import numpy as np
import cv2

lower_red = np.array([0, 120, 90])
upper_red= np.array([10, 255, 255])

left = cv2.imread("left.png")
hsv = cv2.cvtColor(left, cv2.COLOR_BGR2HSV)
mask0 = cv2.inRange(hsv, lower_red, upper_red)

lower_red = np.array([170, 120, 90])
upper_red= np.array([180, 255, 255])
mask1 = cv2.inRange(hsv, lower_red, upper_red)

mask = mask0+mask1

detected_output = cv2.bitwise_and(left, left, mask = mask)

cv2.imwrite("red color detection.png", detected_output)
cv2.waitKey(0)
