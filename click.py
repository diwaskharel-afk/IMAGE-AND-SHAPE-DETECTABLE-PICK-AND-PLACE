import cv2

# -----------------------------
# Load original image
# -----------------------------
img = cv2.imread('calibartion.jpg')

if img is None:
    print("Error: Image not found")
    exit()

# Make a copy for drawing points
img_show = img.copy()

points_img = []

# -----------------------------
# Mouse click function
# -----------------------------
def click_event(event, x, y, flags, param):
    global img_show

    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"Clicked pixel coordinates: ({x}, {y})")
        points_img.append((x, y))

        # Draw circle on image
        cv2.circle(img_show, (x, y), 5, (0, 0, 255), -1)

# -----------------------------
# OpenCV window
# -----------------------------
cv2.namedWindow('calib', cv2.WINDOW_NORMAL)
cv2.setMouseCallback('calib', click_event)

while True:
    cv2.imshow('calib', img_show)
    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC to quit
        break

cv2.destroyAllWindows()
print("Collected points:", points_img)