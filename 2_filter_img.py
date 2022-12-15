from collections import Counter
import cv2
import numpy as np
import glob, os
import shutil
from PIL import Image


def is_dark_ui(large_img):
    try:
        image = Image.open(large_img)
        cols = image.getcolors(maxcolors=2**16)
        if cols:
            most_common = sorted(cols, key=lambda t: t[0], reverse=True)[0:5]
            openai_grey_present = False
            valuesRBG = (68, 70, 84)
            openai_darkgrey_present = False
            valuesDarkRBG = (53, 53, 65)
            for count, rgb in most_common:
                if type(rgb) is int:
                    continue
                openai_grey_present += np.allclose(valuesRBG, rgb[:3], atol=3)
                openai_darkgrey_present += np.allclose(valuesDarkRBG, rgb[:3], atol=3)
            return openai_grey_present and openai_darkgrey_present
        return False
    except:
        return False # when in doubt return false

def is_light_ui(large_img):
    try:
        image = Image.open(large_img)
        cols = image.getcolors(maxcolors=2**16)
        if cols:
            most_common = sorted(cols, key=lambda t: t[0], reverse=True)[0:5]
            openai_grey_present = False
            valuesRBG = (255, 255, 255)
            openai_darkgrey_present = False
            valuesDarkRBG = (247, 247, 247)
            for count, rgb in most_common:
                if type(rgb) is int:
                    continue
                openai_grey_present += np.allclose(valuesRBG, rgb[:3], atol=2)
                openai_darkgrey_present += np.allclose(valuesDarkRBG, rgb[:3], atol=2)
            return openai_grey_present and openai_darkgrey_present
        return False
    except:
        return False # when in doubt return false

    
# create the filterted_img folders
if not os.path.exists('filtered_img/'):
    os.makedirs('filtered_img')
if not os.path.exists('filtered_img/dark_ui'):
   os.makedirs('filtered_img/dark_ui')
if not os.path.exists('filtered_img/light_ui'):
   os.makedirs('filtered_img/light_ui')
if not os.path.exists('filtered_img/other'):
   os.makedirs('filtered_img/other')

# assign directory
directory = 'downloaded_img'
cnt_dark = 0
cnt_light = 0
cnt_other = 0
for filename in os.listdir(directory):
    # get the file
    f = os.path.join(directory, filename)
    if os.path.isfile(f):
        # if it is dark
        if is_dark_ui(f):
            dst_path = os.path.join("filtered_img/dark_ui", filename)
            shutil.copy(f, dst_path)
            cnt_dark += 1
        elif is_light_ui(f):
            dst_path = os.path.join("filtered_img/light_ui", filename)
            shutil.copy(f, dst_path)
            cnt_light += 1
        else:
            dst_path = os.path.join("filtered_img/other", filename)
            shutil.copy(f, dst_path)
            cnt_other += 1

        if (cnt_other+cnt_dark+cnt_light) % 20 == 0 : print(cnt_other+cnt_dark+cnt_light,"...")

print("Finished:", cnt_dark, cnt_light, cnt_other)

