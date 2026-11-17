# version: Python3
from DobotEDU import *
from DobotEDU import *
import base64
import io
import wave
import re
import numpy as np

HOME = (200.0, 0.0, 0.0)
HOME_TOLERANCE = 2.0
INPUT_MODE = 'voice'       # 'voice' or 'manual'
MANUAL_REQUEST = 'P01'     # Change to P02 or P03 if voice fails
RECORD_SECONDS = 5
ENABLE_MOTION = True       # Only enable after entering verified physical poses

# Enter positions measured with the PHYSICAL robot, not simulator positions.
# Pose format: (x, y, z, r)
PARTS = {
    'P01': {'name': 'Bearing', 'color': 'Blue', 'approach': None, 'pickup': None},
    'P02': {'name': 'Bolt', 'color': 'Green', 'approach': None, 'pickup': None},
    'P03': {'name': 'Gear', 'color': 'Red', 'approach': None, 'pickup': None},
}
DELIVERY_APPROACH = None
DELIVERY_RELEASE = None
DELIVERY_RETREAT = None


def log(*values):
    message = ' '.join(str(v).encode('ascii', 'backslashreplace').decode('ascii') for v in values)
    print(message)

def recognise_voice():
    log('Listening for a maintenance request...')
    recorded = util.record(timeout=RECORD_SECONDS)
    if recorded is None:
        raise ValueError('No audio returned')
    samples = np.asarray(recorded, dtype=np.float32).reshape(-1)
    if samples.size == 0:
        raise ValueError('Empty audio recording')
    samples = np.clip(samples, -1.0, 1.0)
    pcm = (samples * 32767).astype('<i2').tobytes()
    output = io.BytesIO()
    with wave.open(output, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(pcm)
    log('Recognising speech...')
    response = speech.asr(voice=base64.b64encode(output.getvalue()))
    if isinstance(response, dict):
        response = response.get('text', response.get('result', ''))
    if isinstance(response, bytes):
        response = response.decode('utf-8', errors='replace')
    return str(response).strip()


def identify_part(command):
    if not command:
        return None
    words = re.findall(r'[a-z0-9]+', command.lower())
    found = []
    for part_id, part in PARTS.items():
        if part_id.lower() in words or part['name'].lower() in words:
            found.append(part_id)
    return found[0] if len(found) == 1 else None


def position():
    pose = m_lite.get_pose()
    if isinstance(pose, dict):
        return (float(pose['x']), float(pose['y']), float(pose['z']))
    if isinstance(pose, (tuple, list)) and len(pose) >= 3:
        return (float(pose[0]), float(pose[1]), float(pose[2]))
    raise ValueError('Unexpected robot position response')


def checked_pose(label, pose):
    if not isinstance(pose, (tuple, list)) or len(pose) != 4:
        raise ValueError('Missing verified physical pose: ' + label)
    return pose


def move(label, pose):
    x, y, z, r = checked_pose(label, pose)
    log('Moving to', label)
    result = m_lite.set_ptpcmd(ptp_mode=0, x=x, y=y, z=z, r=r)
    if result is False:
        raise RuntimeError('Movement command failed at ' + label)


def suction(on):
    result = m_lite.set_endeffector_suctioncup(enable=True, on=on)
    if result is False:
        raise RuntimeError('Suction command failed')


def retrieve(part_id):
    if not ENABLE_MOTION:
        log('Movement disabled: part identification succeeded.')
        return False
    part = PARTS[part_id]
    poses = [part['approach'], part['pickup'], DELIVERY_APPROACH,
             DELIVERY_RELEASE, DELIVERY_RETREAT]
    labels = ['approach', 'pickup', 'delivery approach', 'release', 'retreat']
    for label, pose in zip(labels, poses):
        checked_pose(label, pose)
    current = position()
    if any(abs(current[i] - HOME[i]) > HOME_TOLERANCE for i in range(3)):
        log('STOP: Robot is not at home (200, 0, 0). Actual:', current)
        return False
    move('approach', part['approach'])
    move('pickup', part['pickup'])
    suction(True)
    move('lift', part['approach'])
    move('delivery approach', DELIVERY_APPROACH)
    move('release', DELIVERY_RELEASE)
    suction(False)
    move('retreat', DELIVERY_RETREAT)
    return True


def main():
    log('=== SMART MAINTENANCE PARTS ASSISTANT ===')
    if INPUT_MODE == 'manual':
        command = MANUAL_REQUEST
        log('Manual mode:', command)
    else:
        try:
            command = recognise_voice()
            log('Recognised:', command)
        except Exception as error:
            log('Speech error:', repr(error))
            command = ''
        if identify_part(command) is None:
            log('Speech not recognised. Using manual fallback:', MANUAL_REQUEST)
            command = MANUAL_REQUEST
    part_id = identify_part(command)
    if part_id is None:
        log('Invalid part. No robot movement.')
        return
    log('Selected:', part_id, PARTS[part_id]['name'], PARTS[part_id]['color'])
    try:
        success = retrieve(part_id)
        log('Movement completed:', success)
    except Exception as error:
        log('Robot error:', repr(error))


if __name__ == '__main__':
    main()
