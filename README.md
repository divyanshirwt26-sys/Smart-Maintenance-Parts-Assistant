# 🤖 Smart Maintenance Parts Assistant

**Voice-controlled maintenance-part retrieval using Python and the Dobot Magician Lite robotic arm.**

A student robotics project exploring how speech recognition can be connected to robotic pick-and-place operations. A spoken request is interpreted as one of three maintenance parts, then the robot is instructed to retrieve and deliver the corresponding colored block.

## 🎯 Project goal

Explore an accessible, hands-free approach to selecting and retrieving maintenance parts by combining voice input, Python programming, and robot-arm control.

## ✨ Features

- Five-second audio recording and speech recognition using the DobotEDU environment
- Keyword-based recognition of three maintenance-part requests
- Pick-and-place sequence with suction-cup control
- Position and movement checks
- Simulation and physical-robot code paths
- Manual request fallback in the physical implementation

## 🧰 Technologies

- **Python 3**
- **Dobot Magician Lite** robotic arm
- **DobotLab / DobotEDU** APIs
- **NumPy**, `wave`, `io`, `base64`, and `re`
- Speech recognition via the DobotEDU `speech.asr` interface

## 🧩 Parts supported

| Part ID | Maintenance part | Block color |
| --- | --- | --- |
| P01 | Bearing | Blue |
| P02 | Bolt | Green |
| P03 | Gear | Red |

The parts are represented by colored blocks in the robot workspace.

## ⚙️ How it works

1. Record a spoken maintenance-part request.
2. Convert the audio to a WAV representation and send it to the speech recognition interface.
3. Identify the requested part by name or part ID.
4. Check the robot's initial position.
5. Approach the part, lower the suction cup, and pick it up.
6. Lift and move the part to the delivery location.
7. Release the part and retreat.

The physical implementation can fall back to a configured manual request when speech recognition does not identify a supported part.

## 📁 Repository structure

```text
Smart-Maintenance-Parts-Assistant/
├── simulation/
│   └── virtual_robot.py
├── implementation/
│   └── physical_robot.py
└── README.md
```

### Virtual simulation

[`simulation/virtual_robot.py`](simulation/virtual_robot.py) contains the supplied simulation coordinates and uses relative robot movements with position checks. It is intended for the matching DobotLab virtual environment, not for direct execution on physical hardware.

### Physical implementation

[`implementation/physical_robot.py`](implementation/physical_robot.py) uses absolute robot poses, a home-position check, and a voice/manual input option.

**Important:** The shared physical implementation is a calibration-required version. Pickup, approach, and delivery poses are intentionally set to `None`. It will reject missing poses and cannot perform physical retrieval until all positions have been measured, verified, and configured for the actual robot and workspace.

The exact code and calibration used in the earlier physical demonstration have not been recovered, so this repository does **not** claim the provided physical file is a ready-to-run copy of that tested configuration.

## ▶️ Running the project

This project requires the compatible **DobotEDU / DobotLab environment** and robot APIs; it is not a standalone Python desktop application.

- For the simulation, open the virtual program in the corresponding DobotLab environment and verify the robot layout and home position.
- For a physical robot, calibrate all required poses and verify workspace clearances, end-effector behavior, and emergency-stop procedures **before enabling motion**.
- Never use the simulation coordinates directly on physical hardware.
- Do not run the physical program with `ENABLE_MOTION = True` until the hardware setup has been checked under appropriate supervision.

## 🎥 Demonstration

[▶ Watch the full DobotLab simulation demonstration](smart-maintenance-simulation-demo-full.mp4) (2 min 43 sec). This recording documents the simulation environment; it is not presented as footage of the physical robot.

## 🧪 Development and limitations

The project explored virtual testing and physical robotic-arm operation. The code demonstrates speech-based part selection, robot control, and error-handling logic. Actual success depends on the robot setup, speech-recognition service, calibrated coordinates, and safe motion configuration.

The simulation checks movement position after issuing commands; the physical version checks the initial home pose and command failure responses but does not independently verify every final target pose.

## 👩‍💻 Author

**Divyanshi Rawat**  
ICT student — Fontys University of Applied Sciences

Built as a practical exploration of robotics, Python programming, voice interfaces, and automation.
