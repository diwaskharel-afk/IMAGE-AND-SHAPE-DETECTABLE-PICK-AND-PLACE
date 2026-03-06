"""
Main application for Dobot MG400 control with machine vision integration
Supports:
    python main.py calibrate
    python main.py detect --mode plan
    python main.py detect --mode execute
"""

import argparse
from time import sleep

# ===== Dobot Controller =====
from dobot_controller import (
    ConnectRobot,
    StartFeedbackThread,
    SetupRobot,
    MoveJ,
    MoveL,
    WaitArrive,
    ControlDigitalOutput,
    GetCurrentPosition,
    DisconnectRobot
)

# ===== Vision System =====
from calibration.calibrate import run_calibration
from perception.detect import detect_objects, save_overlay
from utils.mapping import load_calibration, pixel_to_robot


# ==========================================================
# VISION → ROBOT COORDINATE FUNCTION
# ==========================================================

def get_vision_target_points(
        image_path="inputimage.jpg",
        shape=None,
        color=None):

    print("Loading calibration...")
    H = load_calibration()

    print("Detecting objects...")
    img, objects = detect_objects(image_path)

    if not objects:
        print("No target found.")
        return None

    # ---- Filtering ----
    filtered = []

    for obj in objects:
        if shape and obj["shape"] != shape:
            continue
        if color and obj["color"] != color:
            continue
        filtered.append(obj)

    if not filtered:
        print("No matching objects found.")
        return None

    print(f"{len(filtered)} target(s) selected.")

    robot_targets = []

    for obj in filtered:
        u, v = obj["center"]
        X, Y = pixel_to_robot(H, u, v)

        print(f"{obj['shape']} ({obj['color']}) -> Pixel ({u},{v}) -> Robot ({X:.2f},{Y:.2f})")

        robot_targets.append([X, Y, -30, 0])

    save_overlay(img,
                 [obj["center"] for obj in filtered],
                 robot_targets)

    return robot_targets


# ==========================================================
# ROBOT EXECUTION
# ==========================================================

def execute_robot_motion(target_points):
    ROBOT_IP = "192.168.1.6"

    dashboard = move = feed = feed_thread = None

    try:
        print("=" * 50)
        print("DOBOT MG400 VISION PICK & PLACE (With Pause & Pressure)")
        print("=" * 50)

        # Connect
        dashboard, move, feed = ConnectRobot(ip=ROBOT_IP, timeout_s=5.0)
        feed_thread = StartFeedbackThread(feed)

        SetupRobot(dashboard, speed_ratio=50, acc_ratio=50)

        # Positions
        REST_POS = [300, 0, -70, 0]
        PICK_Z = -166
        HOVER_Z = -70  # safe height above the object
        PLACE_X, PLACE_Y, PLACE_Z = 228.3982, -216.5938, -70
        R = 0  # fixed rotation

        # Go to rest position first
        print("\n--- Moving to REST position ---")
        MoveJ(move, REST_POS)
        WaitArrive(REST_POS)

        for target in target_points:
            X, Y = target[0], target[1]

            # Hover above pick point first
            hover_point = [X, Y, HOVER_Z, R]
            pick_point = [X, Y, PICK_Z, R]
            lift_point = [X, Y, HOVER_Z, R]  # lift back to hover

            print(f"\n--- Moving above PICK target: {X}, {Y} ---")
            MoveL(move, hover_point)
            WaitArrive(hover_point)

            # Descend to pick
            print("--- Descending to PICK position ---")
            MoveL(move, pick_point)
            WaitArrive(pick_point)

            # Grip object
            print("--- Activating vacuum at PICK ---")
            ControlDigitalOutput(dashboard, output_index=1, status=1)  # vacuum ON
            sleep(1)

            # Lift back to hover
            print("--- Lifting object to safe height ---")
            MoveL(move, lift_point)
            WaitArrive(lift_point)

            # Move to place
            place_point = [PLACE_X, PLACE_Y, PLACE_Z, R]
            print("--- Moving to PLACE position ---")
            MoveJ(move, place_point)
            WaitArrive(place_point)

            # Place object
            print("--- Turning OFF vacuum ---")
            ControlDigitalOutput(dashboard, output_index=1, status=0)
            sleep(0.3)

            print("--- Activating pressure to repel object ---")
            ControlDigitalOutput(dashboard, output_index=2, status=1)  # pressure ON
            sleep(0.3)

            print("--- Deactivating pressure ---")
            ControlDigitalOutput(dashboard, output_index=2, status=0)
            sleep(0.2)

        print("\nAll targets processed. Returning to REST position.")
        MoveJ(move, REST_POS)
        WaitArrive(REST_POS)

    except Exception as e:
        print(f"ERROR: {e}")

    finally:
        if dashboard:
            DisconnectRobot(dashboard, move, feed, feed_thread)

# ==========================================================
# MAIN
# ==========================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("command", choices=["calibrate", "detect"])
    parser.add_argument("--mode", choices=["plan", "execute"], default="plan")
    parser.add_argument("--shape", type=str, default=None)
    parser.add_argument("--color", type=str, default=None)

    args = parser.parse_args()

    if args.command == "calibrate":
        run_calibration()

    elif args.command == "detect":

        targets = get_vision_target_points(
            shape=args.shape,
            color=args.color
        )

        if not targets:
            return

        if args.mode == "plan":
            print("\nPLAN mode: Robot will NOT move.")

        elif args.mode == "execute":
            print("\nEXECUTE mode: Robot WILL move.")
            execute_robot_motion(targets)


if __name__ == "__main__":
    main()