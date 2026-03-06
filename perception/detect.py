
import cv2
import numpy as np
import math



def detect_objects(image_path):
    img = cv2.imread(image_path)

    if img is None:
        print("Error: Image not found.")
        return None, []

    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # ---- Otsu Threshold ----
    _, th = cv2.threshold(
        img_gray,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # ---- Morphological Cleaning ----
    kernel = np.ones((5, 5), np.uint8)
    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel)
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel)

    # ---- Connected Components ----
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        th, connectivity=8
    )

    objects = []

    for i in range(1, num_labels):

        area = stats[i, cv2.CC_STAT_AREA]
        if not (1000 < area < 31000):
            continue

        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        cx, cy = centroids[i]

        aspect_ratio = w / float(h)

        object_mask = (labels == i).astype("uint8") * 255

        contours, _ = cv2.findContours(
            object_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if len(contours) == 0:
            continue

        contour = contours[0]
        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            continue

        circularity = 4 * math.pi * area / (perimeter ** 2)

        epsilon = 0.02 * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)
        vertices = len(approx)

        # ---- Shape Classification ----
        if circularity > 0.85:
            shape = "Circle"
        elif vertices == 4:
            if 0.9 <= aspect_ratio <= 1.1:
                shape = "Square"
            else:
                shape = "Rectangle"
        else:
            shape = "Unknown"

        # ======================================================
        # COLOR DETECTION (NEW PART)
        # ======================================================

        hsv_object = cv2.bitwise_and(hsv_img, hsv_img, mask=object_mask)
        hue_values = hsv_object[:, :, 0][object_mask == 255]

        if len(hue_values) == 0:
            continue

        mean_hue = np.mean(hue_values)
        if (0 <= mean_hue <= 5) or (170 <= mean_hue <= 179):
            color = "Red"

        elif 6 <= mean_hue <= 25:
            color = "Orange"

        elif 45 <= mean_hue <= 75:
            color = "Green"

        elif 95 <= mean_hue <= 125:
            color = "Blue"

        else:
            color = "Unknown"

        print(f"Detected: {shape} | Color: {color}")

        objects.append({
            "center": (int(cx), int(cy)),
            "shape": shape,
            "color": color
        })

    return img, objects

def save_overlay(image, centers, robot_coords=None, output_path="output_overlay.jpg"):
    overlay = image.copy()

    for i, (u, v) in enumerate(centers):
        cv2.circle(overlay, (u, v), 6, (0, 255, 0), -1)

        text = f"({u},{v})"
        if robot_coords:
            X = robot_coords[i][0]
            Y = robot_coords[i][1]
            text += f" -> ({X:.1f},{Y:.1f})"

        cv2.putText(
            overlay,
            text,
            (u - 30, v - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            2
        )

    cv2.imwrite(output_path, overlay)
    print(f"Overlay saved to {output_path}")

