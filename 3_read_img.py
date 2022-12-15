import cv2
import numpy as np
from PIL import Image
import os
import itertools
import pytesseract
from autocorrect import Speller
from langdetect import detect
import json

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def split_image(img_file, theme):
    """ Input image, returns series of images with split on prompt/response"""

    img = Image.open(img_file)
    img = np.array(img)
    imageRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(imageRGB)
    img = np.array(img)


    THRESHOLD = 200

    # Define the color ranges for each color of interest for creating masks.
    if theme == "dark":
        valuesRBG = [68, 70, 84][::1]
        margin = 30
    elif theme == "light":
        valuesRBG = [255, 255, 255]
        margin = 3
    else:
        raise Exception("Unknown theme")
    
    
    COLOR1_RANGE = [[v - margin for v in valuesRBG], [v + margin for v in valuesRBG]]  # Blue in BGR, [(low), (high)].
    COLOR1_RANGE = [np.array(COLOR1_RANGE[0]), np.array(COLOR1_RANGE[1])]



    # Create masks:
    color1_mask = cv2.inRange(img, COLOR1_RANGE[0], COLOR1_RANGE[1])

    # try to detect horizontal lines
    gray = color1_mask
    blur = cv2.GaussianBlur(gray, (3,3), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Detect horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50,1))
    horizontal_mask = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)

    # cv2.imshow("Mask", horizontal_mask)
    # cv2.imshow("original" , img)
    # cv2.waitKey(0)

    # to split the image, look only at the first 10 pixels from the left to the right (the whole column)
    split_criteria = horizontal_mask[:, :1]

    if len(np.unique(split_criteria)) == 2:
        # get the changes
        change_indeces = np.where(split_criteria[:-1] != split_criteria[1:])[0]
        # add 0 and len-1 change_indeces
        change_indeces = itertools.chain([0], list(change_indeces), [img.shape[0]])
        change_indeces = list(change_indeces)
        # perform the split
        img_parts = []
        for i in range(len(change_indeces)-1):
            imgPart = img[change_indeces[i]:change_indeces[i+1], :]
            # only want ones that are large enough for text
            if imgPart.shape[0] > 70: # 70 pixels
                img_parts.append(imgPart)
                # cv2.imshow("Part",imgPart)
                # cv2.waitKey(0)

        # return the list
        return img_parts
    else:
        return []


def is_there_green_square(img):
    # the colors are in BGR
    open_ai_green_BGR = [32, 138, 115][::-1]
    margin = 50

    # check if it is in there
    GREEN_RANGE = [[v - margin for v in open_ai_green_BGR], [v + margin for v in open_ai_green_BGR]]
    GREEN_RANGE = [np.array(GREEN_RANGE[0]), np.array(GREEN_RANGE[1])]
    green_mask = cv2.inRange(img, GREEN_RANGE[0], GREEN_RANGE[1])
    
    # blur it out a bit and focus on horizontal lines
    gray = green_mask
    blur = cv2.GaussianBlur(gray, (3,3), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    # Detect horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50,1))
    horizontal_mask = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)

    # lets try to find a square
    img2 = img.copy()
    contours,hierarchy = cv2.findContours(horizontal_mask, 1, 2)
    for cnt in contours:
        x1,y1 = cnt[0][0]
        approx = cv2.approxPolyDP(cnt, 0.01*cv2.arcLength(cnt, True), True)
        if len(approx) == 4 or len(approx) == 5 or len(approx) == 6:
            x, y, w, h = cv2.boundingRect(cnt)
            ratio = float(w)/h
            img2 = cv2.drawContours(img2, [cnt], -1, (0,255,255), 3)
            if ratio >= 0.9 and ratio <= 1.1:
                # cv2.imshow(img2)
                # cv2.waitKey(0)
                return True
    return False

def read_text(img):
    # check whether the OpenAI green is present -> Answer
    green_square = is_there_green_square(img)
    if green_square:
        text_type = "response"
    else:
        text_type = "prompt"

    #
    # Get the text and clean it up
    #
    body = pytesseract.image_to_string(img)
    body = body.replace('\n', ' ').replace('\r', '')
    body = body.replace("|","I")

    if len(body)>2:
        language = detect(body)
        if not language == "en": # for now just english
            return None

        spell = Speller(language)
        body = spell.autocorrect_sentence(body)

        return {
            "type": text_type,
            "body": pytesseract.image_to_string(img)
        }
    else:
        return None

def quality_conversation(conversation):
    # QA
    if None in conversation:
        return False
    if len(conversation) == 0:
        return False
    if len(conversation) % 2 == 1:
        return False
    # check that it is prompt -> response
    looking_for = "prompt"
    other_type = "response"
    for text in conversation:
        if looking_for == text["data"]['type']:
            looking_for, other_type = other_type, looking_for
        else:
            return False
    
    return True

def save_conversations(conversations):
    # convert into json
    data = json.dumps(conversations, indent=2)
    with open("conversations.json", "w") as final:
        json.dump(data, final)


def get_all(already_downloaded=None):

    if already_downloaded:
        skip_ids = [conv[0]["id"] for conv in already_downloaded]
        conversations = already_downloaded
    else:
        conversations = []

    
    all_ids = []
    for theme in ["light", "dark"]:
        directory = f"""filtered_img/{theme}_ui"""
        all_files = list(os.listdir(directory))
        all_ids += [ filename.split(".")[0] for filename in all_files ]

        ids_to_search = all_ids

        if already_downloaded:
            go_to_next_theme = False
            # find starting index as you have already seen a lot
            starting_index = 0
            for seen_id in skip_ids:
                try:
                    tmp_index = all_ids.index(seen_id)
                    starting_index = max(starting_index, tmp_index)
                except:
                    # if we cannot find the index is because we already moved on to the next theme, aka finished this one
                    go_to_next_theme = True
                    break
            if go_to_next_theme:
                print("Skipping theme...")
                continue
            print("Starting at index", starting_index,"out of",len(all_ids))
            ids_to_search = all_ids[starting_index:]


        for filename in all_files:
            f = os.path.join(directory, filename)
            conv_id = filename.split(".")[0]

            # only move forward if I want to search the idea, if I am adding to a doc
            if already_downloaded and not conv_id in ids_to_search:
                continue

            img_parts = split_image(f, theme)
            # get convo from images
            conversation = []
            for img in img_parts:
                try:
                    data = read_text(img)
                except:
                    data = None
                if data:
                    conversation.append( {"data":data, "id":conv_id} )
                else:
                    conversation.append(None)
                    break
            # QA
            if quality_conversation(conversation):
                #print("Accepted:", filename)
                # save
                conversations.append(conversation)
                # status update and save to csv
                if len(conversations) % 10 == 0: 
                    print("Detected",len(conversations), "conversations...")
                    save_conversations(conversations)
            else:
                #print("Rejected:", filename)
                continue


    print("Conversations Count: ", len(conversations))
    save_conversations(conversations)



with open("conversations.json", "r") as f:
    old_conversations = json.load(f)
    old_conversations = json.loads(old_conversations)
get_all(old_conversations)