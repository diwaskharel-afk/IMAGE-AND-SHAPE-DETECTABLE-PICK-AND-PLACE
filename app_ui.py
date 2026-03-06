"""
Dobot MG400 Vision Pick & Place UI
Run: python -m streamlit run app_ui.py
"""

import streamlit as st
import cv2
import numpy as np
import pandas as pd
import math
import sys
from pathlib import Path

st.set_page_config(layout="wide")
st.title("Dobot MG400 — Vision Guided Pick & Place")


# ------------------------------------------------
# IMAGE SOURCE
# ------------------------------------------------

st.subheader("Image Source")

col1, col2 = st.columns(2)

capture_btn   = col1.button("Capture from Camera")
uploaded_file = col2.file_uploader("Browse Image", type=["jpg", "jpeg", "png", "bmp"])

# Capture from webcam
if capture_btn:
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if ret:
        cv2.imwrite("scene.jpg", frame)
        st.session_state["scene"] = frame
        st.success("Image captured from camera")
    else:
        st.error("Camera capture failed")

# Load uploaded image
if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    cv2.imwrite("scene.jpg", img)
    st.session_state["scene"] = img
    st.success(f"Image loaded: {uploaded_file.name}")


# ------------------------------------------------
# IMAGE DISPLAY
# ------------------------------------------------

img_col1, img_col2 = st.columns(2)

if "scene" in st.session_state:
    img_col1.subheader("Loaded Image")
    img_col1.image(st.session_state["scene"], channels="BGR", use_container_width=True)


# ------------------------------------------------
# MODE + FILTERS
# ------------------------------------------------

st.subheader("Settings")

col1, col2, col3 = st.columns(3)

mode  = col1.radio("Mode", ["Plan", "Execute"])
color = col2.selectbox("Color Filter", ["Any", "Red", "Green", "Blue", "Yellow"])
shape = col3.selectbox("Shape Filter", ["Any", "Circle", "Square", "Rectangle"])


# ------------------------------------------------
# DETECT BUTTON
# ------------------------------------------------

detect_btn = st.button("Detect Targets")


# ------------------------------------------------
# DETECTION LOGIC (mirrors detect.py exactly)
# ------------------------------------------------

def run_detection(image_bgr, shape_filter=None, color_filter=None):
    """
    Replicates detect.py:
      Shapes: Circle / Square / Rectangle
      Colors: Red / Yellow / Green / Blue
    Returns (objects, overlay_image)
      objects = list of dicts with center, shape, color
    """
    img      = image_bgr.copy()
    hsv_img  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, th = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = np.ones((5, 5), np.uint8)
    th = cv2.morphologyEx(th, cv2.MORPH_OPEN,  kernel)
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(th, connectivity=8)

    objects = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if not (1000 < area < 31000):
            continue

        w, h   = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
        cx, cy = centroids[i]
        aspect = w / float(h)

        mask      = (labels == i).astype("uint8") * 255
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue

        cnt       = contours[0]
        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue

        circularity = 4 * math.pi * area / (perimeter ** 2)
        approx      = cv2.approxPolyDP(cnt, 0.02 * perimeter, True)
        vertices    = len(approx)

        if   circularity > 0.85:              detected_shape = "Circle"
        elif vertices == 4:
            detected_shape = "Square" if 0.9 <= aspect <= 1.1 else "Rectangle"
        else:                                 detected_shape = "Unknown"

        hsv_obj = cv2.bitwise_and(hsv_img, hsv_img, mask=mask)
        hues    = hsv_obj[:, :, 0][mask == 255]
        if len(hues) == 0:
            continue
        mh = np.mean(hues)
        if   (0 <= mh <= 12) or (160 <= mh <= 179): detected_color = "Red"
        elif  10 <= mh <= 35:                        detected_color = "Yellow"
        elif  40 <= mh <= 85:                        detected_color = "Green"
        elif  95 <= mh <= 130:                       detected_color = "Blue"
        else:                                        detected_color = "Unknown"

        if shape_filter and shape_filter != "Any" and detected_shape != shape_filter:
            continue
        if color_filter and color_filter != "Any" and detected_color != color_filter:
            continue

        objects.append({
            "center": (int(cx), int(cy)),
            "shape":  detected_shape,
            "color":  detected_color,
        })

    # Draw overlay
    overlay = img.copy()
    DOT = {"Red":(0,0,255), "Green":(0,200,0), "Blue":(255,120,0), "Yellow":(0,200,200)}
    for obj in objects:
        u, v    = obj["center"]
        dot_bgr = DOT.get(obj["color"], (0,255,0))
        cv2.circle(overlay, (u, v), 10, dot_bgr,      -1)
        cv2.circle(overlay, (u, v), 13, (255,255,255),  2)
        cv2.putText(overlay, f"{obj['shape']} | {obj['color']}",
                    (u + 16, v - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,0,0),       2)
        cv2.putText(overlay, f"{obj['shape']} | {obj['color']}",
                    (u + 16, v - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,255,255), 1)

    return objects, overlay


if detect_btn:
    if "scene" not in st.session_state:
        st.warning("Capture or upload an image first.")
    else:
        objects, overlay = run_detection(
            st.session_state["scene"],
            shape_filter=shape,
            color_filter=color,
        )

        if not objects:
            st.warning("No matching objects detected.")
            st.session_state.pop("targets", None)
        else:
            # Try to get robot coords from calibration
            targets = []
            table   = []
            try:
                sys.path.insert(0, str(Path(__file__).parent))
                from utils.mapping import load_calibration, pixel_to_robot
                H = load_calibration()
                for i, obj in enumerate(objects):
                    u, v   = obj["center"]
                    X, Y   = pixel_to_robot(H, u, v)
                    targets.append([round(float(X), 2), round(float(Y), 2), -30, 0])
                    cv2.putText(overlay, f"({X:.0f},{Y:.0f})",
                                (u + 16, v + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0,0,0), 2)
                    cv2.putText(overlay, f"({X:.0f},{Y:.0f})",
                                (u + 16, v + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200,255,200), 1)
                    table.append({"#": i+1, "Shape": obj["shape"], "Color": obj["color"],
                                  "Pixel U": u, "Pixel V": v,
                                  "Robot X": round(float(X),2), "Robot Y": round(float(Y),2)})
            except Exception as e:
                st.warning(f"Calibration not loaded — showing pixel coords only. ({e})")
                for i, obj in enumerate(objects):
                    u, v = obj["center"]
                    targets.append(None)
                    table.append({"#": i+1, "Shape": obj["shape"], "Color": obj["color"],
                                  "Pixel U": u, "Pixel V": v})

            st.session_state["targets"]  = targets
            st.session_state["overlay"]  = overlay

            # Show overlay in right column
            img_col2.subheader("Detection Result")
            img_col2.image(overlay, channels="BGR", use_container_width=True)

            # Save overlay
            cv2.imwrite("output_overlay.jpg", overlay)

            st.subheader("Detected Targets")
            st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
            st.success(f"{len(objects)} target(s) detected")

# Show overlay persistently if already detected
elif "overlay" in st.session_state:
    img_col2.subheader("Detection Result")
    img_col2.image(st.session_state["overlay"], channels="BGR", use_container_width=True)


# ------------------------------------------------
# RUN ROBOT
# ------------------------------------------------

run_btn = st.button("Run Pick & Place", disabled=(mode != "Execute"))

if run_btn:
    if "targets" not in st.session_state:
        st.warning("Detect targets first.")
    elif any(t is None for t in st.session_state["targets"]):
        st.error("Cannot run — robot coordinates unavailable. Load calibration first.")
    else:
        st.info("Robot executing pick & place sequence…")
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from main import execute_robot_motion
            execute_robot_motion(st.session_state["targets"])
            st.success("Pick and place completed successfully.")
        except Exception as e:
            st.error(f"Robot error: {e}")
