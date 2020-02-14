#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys
import easygui
from yoloOpencv import opencvYOLO
import cv2
import imutils
import time
from libPOS import desktop
from libPOS import weight_HX711
from configparser import ConfigParser
import ast
#from playsound import playsound
import numpy as np
from subprocess import call
#import RPi.GPIO as GPIO 
#GPIO.setmode(GPIO.BCM)

#------------------------------------------------------------------------
cfg = ConfigParser()
cfg.read("pos.ini",encoding="utf-8")

cam_id = cfg.getint("camera", "cam_id")
idle_checkout = ast.literal_eval(cfg.get("operation", "idle_checkout"))
record_video = cfg.getboolean("camera", "record_video")
video_out = cfg.get("camera", "record_video")
frame_rate = cfg.getint("camera", "frame_rate")
dt = desktop(cfg.get("desktop", "bg"))
flipFrame = cfg.get("camera", "flipFrame") #(H, V)
weight_unit = cfg.get("checkout", "weight_unit")
lang = cfg.get("operation", "lang")

wait_for_next = cfg.getint("operation", "wait_for_next")
cart_list_size = ast.literal_eval(cfg.get("desktop", "cart_list_size"))

yolo = opencvYOLO(modeltype=cfg.get("yoloModel", "modeltype"), \
    objnames=cfg.get("yoloModel", "objnames"),\
    weights=cfg.get("yoloModel", "weights"),\
    cfg=cfg.get("yoloModel", "cfg"))

'''
labels_tw = {"v1":["蓮藕", 36, "twkg"], "v2":["小蕃茄", 25, "twkg"], "v3":["綠彩椒",30, "twkg"], "v4":["紅彩椒",30, "twkg"], \
    "v5":["黃彩椒",30, "twkg"], "v6":["茄子", 18, "twkg"], "v7":["老薑",21, "twkg"], "v8":["綠辣椒",8, "twkg"],\
    "v9":["紅辣椒",8, "twkg"], "v10":["黃椒",15, "twkg"], "v11":["青椒",15, "twkg"], "v12":["蒜頭",6, "twkg"],\
    "v13":["雞蛋",11, "twkg"], "v14":["紅蘿蔔",32, "twkg"], "v15":["馬玲薯",10, "twkg"], "v16":["洋菇",6, "twkg"], "v17":["大白菜",52, "twkg"], \
    "v18":["玉米",21, "twkg"], "v19":["小南瓜",60, "twkg"], "v20":["牛蕃茄",26, "twkg"], "v21":["紫地瓜",26, "twkg"]}

labels_tw = {"v1":["橘子", 42, "twkg"], "v2":["雞蛋", 10, "one"], "v3":["綠辣椒", 18, "twkg"], "v4":["玉米荀", 0.25, "gram"],\
    "v5":["小蕃茄", 12, "twkg"], "v6":["棗子", 30, "one"], "v7":["哈密瓜", 65, "kg"], "v8":["蘋果", 25, "one"], \
    "v20": ["紅蘿蔔", 8, "twkg"], "v22":["牛奶芭樂", 20, "one"], "v23":["帶殼玉米荀", 0.15, "gram"] }

labels_en = { "001":["Croissant", 36], "002":["Hot dog", 75], "003":["Big bag",40], "004":["Pineapple",32], \
    "005":["Sesame bun",25], "006":["Hamburger", 66],"007":["Danish Bread",38], "008":["Twist roll",55],\
    "009":["Donuts",22], "010":["Meal bag",28], "011":["Powdered milk",32], "012":["Long Fort",42],\
    "013":["Sandwich",18] }
'''
labels_tw = ast.literal_eval(cfg.get("products", "labels_tw"))

if(cfg.getboolean("system", "full_screen") is True):
    cv2.namedWindow(cfg.get("system", "name_win"), cv2.WND_PROP_FULLSCREEN)        # Create a named window
    cv2.setWindowProperty(cfg.get("system", "name_win"), cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)

detection = cfg.get("desktop", "detection_txt")
#-------------------------------------------------------------------

start_time = time.time()
dt.emptyBG = None
last_movetime = time.time()  #objects > 0
YOLO = False  # YOLO detect in this loop?
last_YOLO = False
txtStatus = ""
frozenScreen = False
cart_list = []

if(lang=="EN"):
    labels = labels_en
else:
    labels = labels_tw

def speak(wavfile):
    print("SPEAK:", wavfile)
    #playsound(wavfile)

def dollar_speak(num):
    strNum = str(num)

    if(lang=="TW"):
        if(num<=99):
            speak("wav.tw/number/" + str(num) + ".wav")
        elif(num<=999 and num>99):
            speak("wav.tw/number/" + strNum[-3] + "00.wav")
            speak("wav.tw/number/" + strNum[-2:] + ".wav")
        elif(num<=1999 and num>999):
            speak("wav.tw/number/1000.wav")
            speak("wav.tw/number/" + strNum[-3] + "00.wav")
            speak("wav.tw/number/" + strNum[-2:] + ".wav")

        speak("wav.tw/dollar_long.wav")

    elif(lang=="EN"):
        if('.' in strNum):
            str_num, float_num = strNum.split('.')
        else:
            int_num = num

        int_num = int(str_num)
        if(int_num<=20):
            speak("wav.en/number/" + str(int_num) + ".wav")
        elif(int_num>20 and int_num <100):
            speak("wav.en/number/" + str(int_num)[:1] + "0.wav")
            speak("wav.en/number/" + str(int_num)[1:2] + ".wav")
        elif(int_num>=100 and int_num <1000):
            speak("wav.en/number/" + str(int_num)[:1] + ".wav")
            speak("wav.en/number/hundred.wav")
            speak("wav.en/number/and.wav")
            speak("waven/number/" + str(int_num)[1:2] + "0.wav")
            speak("wav.en/number/" + str(int_num)[2:3] + ".wav")

        if('.' in strNum):
            speak("wav.en/number/point.wav")
            for f_num in float_num:
                speak("wav.en/number/" + f_num + ".wav")

        speak("wav.en/dollar_long.wav")

def speak_shoplist(itemList):
    totalPrice = 0.0
    for id, item in enumerate(itemList):
        itemID = item[0]
        itemName = item[1]
        itemNum = int(item[3])
        itemPrice = float(item[2])
        totalPrice += itemNum*itemPrice
        print("totalPrice:", totalPrice)

        if(lang=="TW"):
            if(itemID == "b01a"):
                if(itemNum==2):
                    unit = "2_slice.wav"
                else:
                    unit = "1_slice.wav"

            elif(itemID == "b01c"):
                unit = "1_pack.wav"

            else:
                if(itemNum==2):
                    unit = "2_item.wav"
                else:
                    unit = "1_item.wav"

            speak("wav.tw/menu/" + itemID + ".wav")
            #speak("wav/number/" + str(itemNum) + ".wav")
            speak("wav.tw/" + unit)
            speak("wav.tw/number/" + str(itemNum*itemPrice) + ".wav")
            speak("wav.tw/dollar.wav")

            speak("wav.tw/totalis.wav")
            dollar_speak(totalPrice)

        elif(lang=="EN"):
            if(itemNum==1):
                unit = "1_item.wav"
            else:
                unit = "2_item.wav"

            speak(unit)
            speak("wav.en/menu/" + itemID + ".wav")

            #speak("wav.en/totalis.wav")
            dollar_speak(itemNum*itemPrice)

    if(lang=="TW"):
        speak("wav.tw/totalis.wav")
    else:
        speak("wav.en/totalis.wav")

        dollar_speak(totalPrice)


def group(items):
    """
    groups a sorted list of integers into sublists based on the integer key
    """
    if len(items) == 0:
        return []

    items.sort()
    grouped_items = []
    prev_item, rest_items = items[0], items[1:]

    subgroup = [prev_item]
    for item in rest_items:
        if item != prev_item:
            grouped_items.append(subgroup)
            subgroup = []
        subgroup.append(item)
        prev_item = item

    grouped_items.append(subgroup)
    return grouped_items

def img_padding(img, mLength):
    blank = np.zeros((mLength, mLength, 3), dtype="uint8")
    blank[0:img.shape[0], 0:img.shape[1]] = img    
    
    return blank

def click_caculate(event, x, y, flags, param):
    global YOLO, frozenScreen, cart_list

    if((x>=525 and x<=700) and (y>=20 and y<=700)):
        if event == cv2.EVENT_LBUTTONDOWN:
            if(frozenScreen is True):
                frozenScreen = False
            else:
                YOLO = True

    elif((x>=25 and x<=110) and (y>=10 and y<=70)):
        if(record_video is True and len(video_out)>0):
            out.release()

        sys.exit()
        #pass
        #call("sudo nohup shutdown -h now", shell=True)

    elif((x>=715 and x<=795) and (y>=10 and y<=70)):
        cart_list = []

cv2.namedWindow("BREADS_POS")
cv2.setMouseCallback("BREADS_POS", click_caculate)

if __name__ == "__main__":

    weightDevice = weight_HX711(referenceUnit=195)

    INPUT = cv2.VideoCapture(cam_id)

    width = int(INPUT.get(cv2.CAP_PROP_FRAME_WIDTH))   # float
    height = int(INPUT.get(cv2.CAP_PROP_FRAME_HEIGHT)) # float

    if(record_video is True and len(video_out)>0):
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(video_out,fourcc, frame_rate, (int(width),int(height)))


    frameID = 0
    hasFrame, frame_org = INPUT.read()

    while hasFrame:
        width, height = frame_org.shape[1], frame_org.shape[0]

        if(flipFrame[0] is True):
            frame_org = cv2.flip(frame_org, 1 , dst=None)
        elif(flipFrame[1] is True):
            frame_org = cv2.flip(frame_org, 0 , dst=None)

        if(dt.emptyBG is None or time.time()-dt.emptyBG_time>=0.5):
            dt.emptyBG = frame_org.copy()
            dt.emptyBG_time = time.time()
            #print("Update BG")

        objects = dt.difference(dt.emptyBG, frame_org, 800)
        if(objects>0):
            last_movetime = time.time()
            timeout_move = str(int(time.time()-last_movetime))
            txtStatus = "Idle:" + timeout_move
        else:
            waiting = time.time() - last_movetime
            timeout_move = str(int(time.time()-last_movetime))
            txtStatus = "Idle:" + timeout_move

            #if( (waiting > idle_checkout[0] and waiting<idle_checkout[1]) ):
            #    txtStatus = "Caculate"
            #    YOLO = True

        #frame = img_padding(frame_org, width)
        #print("resize:", frame.shape)
        #cv2.imshow("test", frame)
        frame = frame_org.copy()
        imgDisplay = dt.displayWeight(detection, frame, txtStatus, weight_unit, 0)

        if(YOLO is True):
            yoloStart = time.time()
            #print("YOLO start...")
            #cv2.imwrite("labeling/"+str(time.time())+".jpg", frame)

            if(lang=="TW"):
                speak("wav.tw/start_pos.wav")
            else:
                speak("wav.en/start_pos.wav")

            last_YOLO = YOLO
            YOLO = False
            yolo.getObject(frame, labelWant="", drawBox=False, bold=1, textsize=0.35, bcolor=(0,0,255), tcolor=(255,255,255))
            #print("TEST:", yolo.labelNames)
            for id, label in enumerate(yolo.labelNames):
                x = yolo.bbox[id][0]
                y = yolo.bbox[id][1]
                w = yolo.bbox[id][2]
                h = yolo.bbox[id][3]
                cx = int(x+w/6)
                cy = int(y+h/6)
                if(lang == "EN"):
                    frame = desktop.printText(desktop, txt=labels[label][0], bg=frame, color=(0,255,0,0), size=0.75, pos=(cx,cy), type="English")
                else:
                    print(labels[label][0], (cx,cy))
                    frame = desktop.printText(desktop, txt=labels[label][0], bg=frame, color=(0,255,0,0), size=0.55, pos=(cx,cy), type="Chinese")
                    weight_unit = labels[label][2]

            if(len(yolo.labelNames)>0):
                types = group(yolo.labelNames)
                shoplist = []
                itemname_list = ""
                count_total_item = 0
                for i, items in enumerate(types):
                    shoplist.append([items[0], labels[items[0]][0], labels[items[0]][1], len(items)])
                    itemname = labels[items[0]][0]
                    if(i>0): itemname = ","+labels[items[0]][0]
                    itemname_list = itemname_list + itemname
                    count_total_item += len(items)

                weight_gross = weightDevice.weight()
                if(weight_gross<0):
                    weight_clean = 0
                else:
                    if(weight_unit=='twkg'):
                        weight_gross = weight_gross / 600
                        weight_clean = round(weight_gross,1)
                    elif(weight_unit=='kg'):
                        weight_gross = weight_gross / 1000
                        weight_clean = round(weight_gross,1)
                    elif(weight_unit=='gram'):
                        weight_clean = int(weight_gross)
                    elif(weight_unit=='one'):
                        weight_clean = count_total_item


                print("Weight:", weight_unit, weight_gross, weight_clean)

                if(not weight_clean>0):
                    continue
                '''
                types = group(yolo.labelNames)
                shoplist = []
                itemname_list = ""
                count_total_item = 0
                for i, items in enumerate(types):
                    shoplist.append([items[0], labels[items[0]][0], labels[items[0]][1], len(items)])
                    itemname = labels[items[0]][0]
                    if(i>0): itemname = ","+labels[items[0]][0]
                    itemname_list = itemname_list + itemname
                    count_total_item += len(items)
                    #cart_list.append( (labels[items[0]][0], len(items), weight_clean, weight_unit, labels[items[0]][1]) )
                    #print("Append --->", labels[items[0]][0], len(items), weight_clean, weight_unit, labels[items[0]][1])
                    #desktop.printText(labels[items[0]][0], frame, color=(255,255,0,0), size=0.6, pos=(0,0), type="Chinese")
                '''
                cart_list.append( (itemname_list, count_total_item, weight_clean, weight_unit, labels[types[0][0]][1]) )
                print("Append --->", (itemname_list, count_total_item, weight_clean, weight_unit, labels[types[0][0]][1]))
                txtStatus = "checkout"
                #print(shoplist)

                imgDisplay = dt.displayWeight(detection, frame, txtStatus, shoplist, weight_unit, weight_clean)
                cv2.imshow("BREADS_POS", imgDisplay)
                cv2.waitKey(1)
                if(len(shoplist)>0):
                    print("YOLO used:" + str(round(time.time()-yoloStart, 3)))
                    print("Shop list:", shoplist)
                    
                    #frozenScreen = True
                    #while frozenScreen is True:
                    cv2.waitKey(wait_for_next*1000)

                #cv2.imshow("BREADS_POS", imgDisplay)
                #cv2.waitKey(1)
                #time.sleep(0)
        else:
            last_YOLO = YOLO

        if(last_YOLO is True):
            last_YOLO = False

        else:
            if(len(cart_list)>0):
                img_listCart = dt.displayCart(cart_list, list_size=cart_list_size)
                print("img_listCart :", img_listCart.shape)
                print("cart_list:", cart_list)
                #imgDisplay = dt.displayWeight(detection, frame, txtStatus, weight_unit, 0)
                imgDisplay[90:90+img_listCart.shape[0], 530:530+img_listCart.shape[1]] = img_listCart

        cv2.imshow("BREADS_POS", imgDisplay)
        cv2.waitKey(1)


        #dt.emptyBG = frame.copy()
        #dt.emptyBG_time = time.time()
        if(record_video is True and len(video_out)>0):
            out.write(imgDisplay)
        
        #k = cv2.waitKey(1)
        #if k == 0xFF & ord("q"):
        #    sys.exit()
        hasFrame, frame_org = INPUT.read()
