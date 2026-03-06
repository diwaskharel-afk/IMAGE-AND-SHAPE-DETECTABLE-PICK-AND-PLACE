
# Machine Vision Final Project
## IMAGE-AND-SHAPE-DETECTABLE-PICK-AND-PLACE

### Course
Machine Vision  
HAMK – Häme University of Applied Sciences  

### Team Members
- Diwas Kharel
- Bikash Basyal
- Biswash Pokhrel

---

# 1. Project Overview

This project implements a **vision-guided robotic pick-and-place system** where a camera detects objects on a table and guides a **Dobot MG400 robot** to pick them and place them into a box.

The project integrates the building blocks developed during the Machine Vision course including:

- Image preprocessing
- Image segmentation
- Coordinate mapping
- Object detection
- Color and shape selection

The system converts object locations detected in the camera image into **robot workspace coordinates** and performs automated pick-and-place operations.

---

# 2. Project Goal

The goal of this project is to build a system capable of:

- Calibrating a real camera with the robot workspace
- Detecting objects from a camera image
- Converting pixel coordinates (u, v) to robot coordinates (X, Y)
- Providing two system modes:
  - **Plan Mode**
  - **Execute Mode**

### Plan Mode
The system detects objects and computes robot coordinates without moving the robot.

### Execute Mode
The system performs the full robot pick-and-place operation.

---

# 3. System Architecture

The project is structured into modular components.
IMAGE-AND-SHAPE-DETECTABLE-PICK-AND-PLACE
### Project Structure

```
calibration/
perception/
robot/
ui/

app_streamlit.py
main.py
```

### Module Description

**Calibration Module**
- Handles camera-to-robot calibration.

**Perception Module**
- Performs image processing and object detection.

**Robot Module**
- Controls the robot pick-and-place motion.

**UI Module**
- Provides a graphical interface for operators.

---

# 4. Calibration System

The calibration tool maps image coordinates to robot workspace coordinates.

The calibration process involves collecting at least **four corresponding points**:

Pixel coordinates (u, v)  
Robot coordinates (X, Y)

Using these correspondences, the system computes a **homography matrix (H)** that transforms coordinates from image space to robot workspace.

The calibration information is saved in a file:
```
calibration.json
```

The file stores:

- Homography matrix (3×3)
- Image resolution
- Metadata such as date or notes

This allows the system to reuse calibration without recalibrating each time.

---

# 5. Vision-to-Robot Pipeline

The detection pipeline performs the following steps:

1. Capture image from camera
2. Preprocess the image
3. Detect objects using segmentation
4. Calculate the center of each object in pixel coordinates (u,v)
5. Convert pixel coordinates to robot coordinates (X,Y) using calibration matrix H
6. Display the detected objects with overlays and coordinates

Detected targets are displayed with markers and coordinate values.

### Example Detection Output

![Color Detection Result](images/color_detection.png)


---

# 6. Color Detection

The system supports filtering objects by color.

Example use cases:

- Pick only **red tiles**
- Pick only **blue objects**

Color detection is implemented using color thresholding.

### Example Color Detection Result
![Color Detection Result Blue)](output/BlueandCircle.jpg)

![Color Detection Result Orange](output/OrangeObjet.jpg)
---


# 7. Shape Detection

The system can detect objects based on shape.

Supported shapes include:

- Circle
- Square
- Rectangle

Shape detection is performed using contour analysis.

### Example Shape Detection Result
![Shape Detection](output/BlueandCircle.jpg)

---

# 8. Combined Selection Logic

The system can combine color and shape detection.

Examples:

- Pick **blue circle**
- Pick **red squares**
- Pick **round objects**

This feature improves the flexibility of the robotic system.

---

# 9. Command Line Interface (CLI)

The system provides a command-line interface to control the operations.

### Calibration

```
python main.py calibrate
```

### Detect Objects (Plan Mode)
```
python main.py detect --mode plan
```

### Detect and Execute Pick
```
python main.py detect --mode execute
```

### Color-Based Detection
```
python main.py detect --color red --mode plan
```

### Shape-Based Detection
```
python main.py detect --shape circle --mode plan
```

### Combined Detection
```
python main.py pick --color blue --shape square --mode execute
```

The CLI outputs:

- Pixel coordinates (u,v)
- Robot coordinates (X,Y)
- Detection status
- Number of targets detected

It also saves an **annotated image with detection overlays**.

---

# 10. Graphical User Interface (GUI)

A graphical interface was implemented using **Streamlit** to allow an operator to interact with the system.

The GUI provides:

- Live or captured camera image
- Mode selection (Plan / Execute)
- Color selection
- Shape selection
- Buttons for detection and robot execution

The interface also displays detected objects and computed robot coordinates.

### GUI Screenshot
![All Shape and Colour Detection](output/image.png)
![Blue Circle](output/bluecircle.png)


---

# 11. Plan Mode

In Plan Mode:

- Objects are detected
- Robot coordinates are calculated
- Detection overlays are shown

The robot does **not move** in this mode.

This allows the operator to verify the detection before execution.

---

# 12. Execute Mode

In Execute Mode:

1. Object is detected
2. Coordinates are calculated
3. Robot receives target coordinates
4. Robot performs the pick-and-place operation

Safety confirmation is required before executing the robot movement.

---

# 13. Running the Project

Clone the repository

Run GUI
```
streamlit run app_streamlit.py
```

---

# 14. Discussion

This project demonstrates the integration of machine vision and robotics for automated object manipulation.

The system successfully performs camera calibration, object detection, coordinate transformation, and robotic pick-and-place operations.

### Observations

- The system works reliably under moderate lighting conditions.
- Calibration accuracy significantly affects robot positioning.
- The GUI improves usability for operators.

### Possible Improvements

- Improve robustness to lighting variations
- Implement real-time object tracking
- Add support for multiple object picking

---

# 15. Repository

Project Repository:

https://github.com/diwaskharel-afk/IMAGE-AND-SHAPE-DETECTABLE-PICK-AND-PLACE
