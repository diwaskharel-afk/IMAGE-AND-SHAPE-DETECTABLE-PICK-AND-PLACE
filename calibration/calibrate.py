import numpy as np
import cv2
import json

from datetime import datetime


def compute_homography():
   


    # Image (UV) points – collected points, in order P1 to P6
    img_pts = np.array([(1286, 698), (841, 492), (733, 287), (1162, 374), (434, 826), (334, 412)], dtype=np.float32)

    # Robot coordinates – corresponding P1 to P6
    robot_pts = np.array([
    [265.86, -80.84],
    [311.83, 20.669],
    [360.91, 47.551],
    [339.32, -51.30],
    [233.70, 121.14],
    [335.65, 149.22]
], dtype=np.float32)
    H, mask = cv2.findHomography(img_pts, robot_pts, method=0)

    return H


def save_calibration(H, filename="calibration.json"):
    data = {
        "H": H.tolist(),
        "date": str(datetime.now())
    }

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Calibration saved to {filename}")


def run_calibration():
    print("Computing homography...")
    H = compute_homography()
    print("Homography matrix H:")
    print(H)

    save_calibration(H)


if __name__ == "__main__":
    run_calibration()
