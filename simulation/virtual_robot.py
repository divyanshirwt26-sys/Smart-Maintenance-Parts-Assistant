# version: Python3
from DobotEDU import *

import numpy as np
import base64
import wave
import io
import re

# ==========================================
# SMART MAINTENANCE PARTS ASSISTANT
# AI SPEECH + VIRTUAL ROBOT INTEGRATION
# ==========================================

PARTS = {
    "P01": {"name": "Bearing", "color": "Blue", "pickup": (292.76, -9.20, -44.42, 0.67)},
    "P02": {"name": "Bolt", "color": "Green", "pickup": (294.11, -30.74, -44.47, 1.53)},
    "P03": {"name": "Gear", "color": "Red", "pickup": (295.58, 27.83, -45.62, -0.42)}
}

DELIVERY_X = 292.76
DELIVERY_Y = -114.97
DELIVERY_Z = -35.61

TRAVEL_Z = 40.0
MAX_STEP = 8.0
TOLERANCE = 1.0


# ==========================================
# SPEECH RECOGNITION
# ==========================================

def recognise_voice():
    print("\nListening for a maintenance request...")
    print("Recording for 5 seconds.")

    voice = util.record(timeout=5)

    if voice is None or len(voice) == 0:
        print("ERROR: No audio recorded.")
        return None

    audio = np.asarray(voice)

    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    if np.issubdtype(audio.dtype, np.floating):
        audio = np.clip(audio, -1.0, 1.0)
        audio = (audio * 32767).astype(np.int16)
    elif audio.dtype != np.int16:
        audio = audio.astype(np.int16)

    wav_buffer = io.BytesIO()

    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(audio.tobytes())

    encoded_voice = base64.b64encode(wav_buffer.getvalue())

    print("Recognising speech...")

    return speech.asr(voice=encoded_voice)


# ==========================================
# PART IDENTIFICATION
# ==========================================

def identify_request(text):
    words = re.findall(r"[a-z0-9]+", str(text).lower())

    keywords = {
        "P01": ["bearing", "p01"],
        "P02": ["bolt", "p02"],
        "P03": ["gear", "p03"]
    }

    matches = []

    for part_id, terms in keywords.items():
        if any(term in words for term in terms):
            matches.append(part_id)

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        print("ERROR: Multiple parts requested.")
    else:
        print("ERROR: Unknown maintenance part.")

    return None


# ==========================================
# ROBOT MOVEMENT
# ==========================================

def get_position():
    return m_lite.get_pose()


def move_relative(dx, dy, dz, dr=0):
    before = get_position()

    result = m_lite.set_ptpcmd(
        ptp_mode=7,
        x=dx,
        y=dy,
        z=dz,
        r=dr
    )

    after = get_position()

    reached = (
        abs(after["x"] - (before["x"] + dx)) < TOLERANCE
        and abs(after["y"] - (before["y"] + dy)) < TOLERANCE
        and abs(after["z"] - (before["z"] + dz)) < TOLERANCE
        and abs(after["r"] - (before["r"] + dr)) < TOLERANCE
    )

    if not reached:
        print("ERROR: Movement target not reached.")
        print("Command result:", result)
        print("Actual position:", after)

    return reached


def move_axis(axis, target):
    for attempt in range(60):
        current = get_position()
        difference = target - current[axis]

        if abs(difference) < TOLERANCE:
            return True

        step = max(-MAX_STEP, min(MAX_STEP, difference))

        dx = step if axis == "x" else 0
        dy = step if axis == "y" else 0
        dz = step if axis == "z" else 0
        dr = step if axis == "r" else 0

        if not move_relative(dx, dy, dz, dr):
            print("STOP: Failed movement on", axis)
            return False

    print("STOP: Movement limit exceeded.")
    return False


def move_to(x, y, z, r):
    if not move_axis("z", z):
        return False
    if not move_axis("x", x):
        return False
    if not move_axis("y", y):
        return False
    if not move_axis("r", r):
        return False

    return True


def suction_on():
    result = m_lite.set_endeffector_suctioncup(enable=True, on=True)
    print("Suction ON:", result)
    return result is True


def suction_off():
    result = m_lite.set_endeffector_suctioncup(enable=True, on=False)
    print("Suction OFF:", result)
    return result is True


# ==========================================
# AUTOMATED PART RETRIEVAL
# ==========================================

def retrieve_part(part_id):
    part = PARTS[part_id]

    pickup_x, pickup_y, pickup_z, pickup_r = part["pickup"]

    print("\nRETRIEVING:", part["name"])
    print("Part ID:", part_id)
    print("Colour:", part["color"])

    print("STEP 1: Approaching storage")
    if not move_to(pickup_x, pickup_y, TRAVEL_Z, pickup_r):
        return False

    print("STEP 2: Lowering to block")
    if not move_axis("z", pickup_z):
        return False

    print("STEP 3: Activating suction")
    if not suction_on():
        return False

    print("STEP 4: Lifting block")
    if not move_axis("z", TRAVEL_Z):
        return False

    print("STEP 5: Moving to delivery area")
    if not move_axis("x", DELIVERY_X):
        return False
    if not move_axis("y", DELIVERY_Y):
        return False

    print("STEP 6: Lowering for delivery")
    if not move_axis("z", DELIVERY_Z):
        return False

    print("STEP 7: Releasing block")
    if not suction_off():
        return False

    print("STEP 8: Retreating")
    if not move_axis("z", TRAVEL_Z):
        return False

    print("RETRIEVAL SEQUENCE COMPLETED")
    return True


# ==========================================
# MAIN PROGRAM
# ==========================================

def main():
    print("================================")
    print("SMART MAINTENANCE PARTS ASSISTANT")
    print("AI-ASSISTED VOICE CONTROL")
    print("================================")

    try:
        recognised_text = recognise_voice()

        print("\nRecognised command:", recognised_text)

        if not recognised_text:
            print("ERROR: No speech recognised.")
            return

        selected = identify_request(recognised_text)

        if selected is None:
            print("Please request one valid part.")
            return

        print("\nPART IDENTIFIED")
        print("ID:", selected)
        print("Name:", PARTS[selected]["name"])
        print("Colour:", PARTS[selected]["color"])

        start = get_position()

        if (
            abs(start["x"] - 240.0) > 2
            or abs(start["y"]) > 2
            or abs(start["z"] - 145.0) > 2
        ):
            print("STOP: Reset virtual robot to home.")
            return

        if not suction_off():
            print("STOP: Suction initialisation failed.")
            return

        success = retrieve_part(selected)

        print("\n=== FINAL REPORT ===")
        print("Recognised command:", recognised_text)
        print("Requested part:", selected)
        print("Sequence completed:", success)
        print("Final position:", get_position())

        if success:
            print("Check the delivered block visually.")
        else:
            print("Retrieval failed. Inspect the robot.")

    except Exception as error:
        print("ERROR:", type(error).__name__, str(error))


main()
