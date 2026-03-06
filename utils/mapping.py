import numpy as np
import json


def load_calibration(filename="calibration.json"):
    with open(filename, "r") as f:
        data = json.load(f)

    H = np.array(data["H"])
    print("Loaded calibration from file.")
    return H


def pixel_to_robot(H, u, v):
    pixel = np.array([u, v, 1.0])
    robot = H @ pixel

    robot = robot / robot[2]  # normalize

    X = robot[0]
    Y = robot[1]

    return X, Y
