import cv2
import numpy as np

import mss
import pyautogui

import os
import sys
import time
import datetime as dt

import base64
from tmps import *

from ui import TrackWindow, CursorPosition, LamellaePositions, ParameterWindow


def take_screenshot():
    with mss.mss() as sct:
        screenshot_name = sct.shot(mon=-1, output="screenshot.png")
    screenshot = cv2.imread(screenshot_name, 0)

    return screenshot


def click(position, clicks=1):
    attempt = 0
    pyautogui.moveTo(*position)

    while not position == pyautogui.position():
        confirm = pyautogui.confirm(text='Error mouse movement detected.\nPress "OK" to continue. (10s timeout)',
                                    title="Autolos - Lamella Setup", buttons=["OK", "Cancel"], timeout=10000)
        if confirm == "Cancel" or (attempt == 5 and confirm == "Timeout"):
            sys.exit(1)
        attempt += 1
        time.sleep(1)
        pyautogui.moveTo(*position)

    pyautogui.click(clicks=clicks)
    time.sleep(0.1)


def setup_screen():
    tw_ui = TrackWindow('Draw a box around the area you wish to track. "Enter" to confirm. "ESC" to cancel.')
    track_window = tw_ui.box_position
    cp_ui = CursorPosition('Click the center of the crosshair on the ion beam. "Enter" to confirm. "ESC" to cancel.')
    center_position = cp_ui.cursor_pos
    lp_ui = LamellaePositions('Click each lamella location on the left panel of MAPS. "CTRL-Z" to undo. '
                              '"Enter" to confirm. "ESC" to cancel.')
    lamellae_positions = lp_ui.lamellae_positions

    return track_window, center_position, lamellae_positions


def setup_inputs():
    pw_ui = ParameterWindow()
    if not pw_ui.ok:
        sys.exit(1)

    save_dir = pw_ui.save_dir
    run_time = pw_ui.run_time
    voltage_idx = pw_ui.voltage_idx
    current_imaging_idx = pw_ui.current_imaging_idx
    current_milling_idx = pw_ui.current_milling_idx

    return save_dir, run_time, voltage_idx, current_imaging_idx, current_milling_idx


def get_ref(i, lamella_position, center_position, save_dir, track_window):
    click(lamella_position)
    detect_position("driveto")
    time.sleep(5)
    click(center_position)
    pyautogui.keyDown("f6")
    pyautogui.keyDown("f6")
    confirm = pyautogui.confirm(text='Press "OK" when crosshair is at the proper location',
                                title="Autolos - Lamella Setup", buttons=["OK", "Cancel"])
    if confirm == "Cancel":
        sys.exit(1)

    ss_name = check_dir(save_dir, f"lamella{i}_ref.png")
    orig = np.asarray(pyautogui.screenshot(ss_name, region=track_window))
    gray = cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY)

    return gray


def detect_position(detect_object, idx=0):
    detect_dict = {
        "driveto": [tmp4, (218, 405), (190, 195)],
        "play": [tmp5, (45, 83), (22, 18)],
        "stop": [tmp5, (45, 83), (60, 20)],
        "patterning_icon": [tmp6, (37, 26), (13, 18)],
        "patterning_selectall": [tmp7, (621, 337), (275, 155)],
        "patterning_properties": [tmp7, (621, 337), (30, 330)],
        "patterning_scroll": [tmp7, (621, 337), (315, 400)],
        "patterning_zsize": [tmp7, (621, 337), (210, 440)],
        "patterning_hide": [tmp7, (621, 337), (245, 45)],
        "contrast": [tmp3, (45, 78), (23, 23)],
        "focus": [tmp3, (45, 78), (60, 23)],
        "beam_icon": [tmp0, (38, 27), (14, 19)],
        "beam_onoff": [tmp1, (919, 339), (64, 240)],
        "beam_wake": [tmp1, (919, 339), (90, 168)],
        "beam_sleep": [tmp1, (919, 339), (250, 168)],
        "voltage": [tmp2, (50, 480), (282, 24), (282, 24)],
        "current": [tmp2, (50, 480), (390, 24), (350, 24)]
    }

    screenshot = take_screenshot()
    encoded = detect_dict[detect_object][0].encode("utf-8")
    temp = np.frombuffer(base64.decodebytes(encoded), dtype=np.uint8).reshape(detect_dict[detect_object][1])
    pixel_diff = detect_dict[detect_object][2]
    match = cv2.matchTemplate(screenshot, temp, cv2.TM_CCOEFF_NORMED)
    locate = np.where(match == np.max(match))
    x = locate[1][0] + pixel_diff[0]
    y = locate[0][0] + pixel_diff[1]

    click((x, y))

    if detect_object == "patterning_scroll":
        for _ in range(2):
            click((x, y))

    if detect_object in ["voltage", "current"]:
        diff_x = detect_dict[detect_object][3][0] - detect_dict[detect_object][2][0]
        diff_y = detect_dict[detect_object][3][1] - detect_dict[detect_object][2][1] + (idx + 1) * 23

        click((x + diff_x, y + diff_y))
        time.sleep(5)


def check_dir(save_dir, file_name):
    if os.path.exists(save_dir):
        return os.path.join(save_dir, file_name)
    return None


def write_log(save_dir, log_message):
    if os.path.exists(save_dir):
        with open(os.path.join(save_dir, "run.log"), "a+") as f:
            f.write(f"[{dt.datetime.now().strftime('%x %X')}]: {log_message}\n")


def main():
    track_window, center_position, lamellae_positions = setup_screen()
    save_dir, run_time, voltage_idx, current_imaging_idx, current_milling_idx = setup_inputs()
    time.sleep(1)
    detect_position("voltage", voltage_idx)
    detect_position("current", current_imaging_idx)

    lamellae_init = []
    for i, lamella_position in enumerate(lamellae_positions, 1):
        ref_img = get_ref(i, lamella_position, center_position, save_dir, track_window)
        lamellae_init.append(ref_img)
        time.sleep(1)

    for i, (lamella_position, orig_image) in enumerate(zip(lamellae_positions, lamellae_init), 1):
        write_log(save_dir, f"Starting lamella {i}...")
        click(lamella_position)
        detect_position("driveto")
        time.sleep(5)
        detect_position("contrast")
        time.sleep(5)
        click(center_position)
        pyautogui.keyDown("f6")
        pyautogui.keyDown("f6")
        time.sleep(5)

        try:
            ss_name = check_dir(save_dir, f"lamella{i}_premill.png")
            new_image = np.asarray(pyautogui.screenshot(ss_name, region=track_window))
            gray_image = cv2.cvtColor(new_image, cv2.COLOR_BGR2GRAY)

            orb = cv2.ORB_create()
            kp1, des1 = orb.detectAndCompute(orig_image, None)
            kp2, des2 = orb.detectAndCompute(gray_image, None)

            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(des1, des2)
            x_shifts = []
            y_shifts = []
            for m in matches:
                x1 = kp1[m.queryIdx].pt[0]
                y1 = kp1[m.queryIdx].pt[1]
                x2 = kp2[m.trainIdx].pt[0]
                y2 = kp2[m.trainIdx].pt[1]

                x_shift = int(x2 - x1)
                y_shift = int(y2 - y1)

                x_shifts.append(x_shift)
                y_shifts.append(y_shift)

            x_shift = max(set(x_shifts), key=x_shifts.count)
            y_shift = max(set(y_shifts), key=y_shifts.count)

            write_log(save_dir, f"Shifted by: {x_shift}px {y_shift}px.")

            click((center_position[0] + x_shift, center_position[1] + y_shift), clicks=2)
            time.sleep(2)
            pyautogui.keyDown("f6")
            pyautogui.keyDown("f6")
            time.sleep(5)

            if i == 1:
                detect_position("patterning_icon")
                detect_position("patterning_selectall")
                detect_position("patterning_properties")
                detect_position("patterning_scroll")
                detect_position("patterning_zsize")
                pyautogui.write("10mm")
                pyautogui.press("enter")

            write_log(save_dir, f"Setting current index: {current_milling_idx}.")
            detect_position("current", current_milling_idx)
            write_log(save_dir, f"Start milling...")
            detect_position("play")
            time.sleep(run_time * 60)
        except KeyboardInterrupt:
            sys.exit(1)
        except:
            pass

        write_log(save_dir, f"Finished milling.")
        detect_position("stop")
        detect_position("current", current_imaging_idx)
        pyautogui.keyDown("f6")
        pyautogui.keyDown("f6")
        time.sleep(5)
        ss_name = check_dir(save_dir, f"lamella{i}_postmill.png")
        pyautogui.screenshot(ss_name, region=track_window)
        write_log(save_dir, f"Finished lamella {i}.\n")

    detect_position("beam_icon")
    detect_position("beam_onoff")


if __name__ == '__main__':
    main()
