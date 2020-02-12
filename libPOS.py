import time
from PIL import ImageFont, ImageDraw, Image
import imutils
import cv2
import numpy as np
from skimage.measure import compare_ssim

class desktop:
    def __init__(self, bg_path, click_bg_path):
        self.bg = bg_path
        self.click_bg = cv2.imread(click_bg_path)

    def weight_unit_name(self, weight_unit):
        if(weight_unit=='twkg'):
            unit_name = "台斤"
        elif(weight_unit=='kg'):
            unit_name = "公斤"
        else:
            unit_name = "公克"

        return unit_name

    def displayWeight(self, detect_type, camImg, txtStatus=None, itemList=None, weight_unit='gram', weight=0):
        itemList_pos = (60, 525)
        itemList_h = 60
        bg = cv2.imread(self.bg)
        resized = cv2.resize(camImg, (480, 360))
        bg[95:95+resized.shape[0],25:25+resized.shape[1]] = resized

        price_total = 0
        #if(itemList is not None):
        if(weight>0 and len(itemList)>0):
            y = itemList_pos[0]
            for id, item in enumerate(itemList):
                '''
                txtIMG = cv2.imread("images/products/" + item[0] + ".jpg")

                bg[y:y+txtIMG.shape[0], itemList_pos[1]:itemList_pos[1]+txtIMG.shape[1]] = txtIMG
                '''
                y += itemList_h
                bg = self.printText(item[1], bg=bg, color=(255,0,0,0), size=1.0, pos=(itemList_pos[1],y), type="Chinese")

                #cv2.putText(bg, str(id+1)+")", (itemList_pos[1]-30,y+17), cv2.FONT_HERSHEY_COMPLEX, 0.4, (0,0,0), 2)
                if(item[3]>1):
                    cv2.putText(bg, "x "+str(item[3]), (itemList_pos[1]+130,y+17), cv2.FONT_HERSHEY_COMPLEX, 0.6, (0,255,0), 2)

                #price = item[2]*item[3]
                #cv2.putText(bg, "$"+str(price), (itemList_pos[1]+180,y+13), cv2.FONT_HERSHEY_COMPLEX, 0.45, (255,0,0), 1)

                #price_total += price
            price_total = round(weight*float(itemList[0][2]),1)
            #total = cv2.imread("images/total.jpg")
            #bg[390:390+total.shape[0], 515:515+total.shape[1]] = total
            unit_name = self.weight_unit_name(weight_unit)

            bg = self.printText("每{} {}元".format(unit_name, itemList[0][2]), bg=bg, color=(0,0,0,0), size=0.65, pos=(525,250), type="Chinese")
            bg = self.printText("秤重 {}{}".format(weight, unit_name), bg=bg, color=(0,0,0,0), size=0.65, pos=(525,280), type="Chinese")
            bg = self.printText("小計:{}元".format(price_total), bg=bg, color=(0,0,255,0), size=0.85, pos=(525,330), type="Chinese")
            #cv2.putText(bg, "$"+str(round(price_total,2)), (720,375+total.shape[0]), cv2.FONT_HERSHEY_COMPLEX, 0.75, (255,0,0), 2)

        if(txtStatus is not None):
            cv2.putText(bg, txtStatus, (bg.shape[1]+20,bg.shape[0]-35), cv2.FONT_HERSHEY_COMPLEX, 0.45, (0,255,255), 1)
        '''
        else:
            if(not weight>0):
                 bg = self.printText("秤重盤重量為零", bg=bg, color=(0,255,0,0), size=1.0, pos=(525,200), type="Chinese")

            if(not len(itemList)>0):
                 bg = self.printText("秤重盤沒有東西", bg=bg, color=(0,255,0,0), size=1.0, pos=(525,200), type="Chinese")
        '''
        return bg
        #cv2.imshow(self.win, bg)
        #cv2.waitKey(1)

    def displayCart(self, cart_list, list_size=(160,250)):
        bg = np.zeros((list_size[0], list_size[1], 3), dtype = 'uint8')
        bg[:] = (255, 255, 255)
        #cart_id_now = self.cart_list_id

        itemList_pos = (30, 0)  #y,x
        itemList_h = 55
        sum_total = 0
        y = itemList_pos[0]
        for id, item in enumerate(cart_list):
            item_name, item_count, item_weight, item_unit, item_price = item[0], item[1], item[2], self.weight_unit_name(item[3]), item[4]

            if(item_count>1):
                txt_item = "{}){} {}個".format(id+1, item_name, item_count)
            else:
                txt_item = "{}){}".format(id+1, item_name)
            bg = self.printText(txt_item, bg=bg, color=(255,0,0,0), size=0.55, pos=(itemList_pos[1],y), type="Chinese")

            txt_item = "  {}{}x${}=${}".format(item_weight,item_unit,item_price, (item_weight*item_price))
            bg = self.printText(txt_item, bg=bg, color=(15,15,15,0), size=0.40, pos=(itemList_pos[1],y+25), type="Chinese")

            sum_total = sum_total + item_weight*item_price
            y += itemList_h

        #self.cart_list_id = cart_id_now + len(cart_list)

        txt_total = "總計 ${}".format(sum_total)
        bg = self.printText(txt_total, bg=bg, color=(0,0,0,0), size=0.75, pos=(0, list_size[0]-30), type="Chinese")

        return bg

    def getContours(self, img, minSize=1600):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (11, 11), 0)
        gray = cv2.Canny(gray, 75, 200)
        cnts = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        #cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:7]
        cv2.imshow("TEST", gray)
        #keeps = []
        # loop over the contours again
        counts = 0
        for (i, c) in enumerate(cnts):
            # compute the area and the perimeter of the contour
            area = cv2.contourArea(c)
            #print(area)
            if(area>minSize):
                counts += 1
                #print(area)
                #keeps.append(c)

        #cv2.drawContours(img, keeps, -1, (0, 255, 0), 2)
        print("Found {} contours".format(len(cnts)))

        #cv2.drawContours(img, [approx], -1, (0, 255, 0), 2)
        return counts

    def difference(self, img1, img2, minSize=1200):
        sensitive_th = 90

        img1 = img1[50:img1.shape[0]-50, 50:img1.shape[1]-50]
        img2 = img2[50:img2.shape[0]-50, 50:img2.shape[1]-50]
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        gray1 = cv2.GaussianBlur(gray1, (15, 15), 0)
        gray2 = cv2.GaussianBlur(gray2, (15, 15), 0)

        diff = cv2.subtract(gray1, gray2)
        #cv2.imshow("TEST", diff)
        thresh = cv2.threshold(diff, sensitive_th, 255, cv2.THRESH_BINARY_INV)[1]
        cnts = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        #(score, diff) = compare_ssim(gray1, gray2, full=True)
        #diff = (diff * 255).astype("uint8")
        #print("SSIM: {}".format(score))

        #thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        #cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        #cnts = imutils.grab_contours(cnts)

        # loop over the contours
        counts = 0
        for c in cnts:
            # compute the bounding box of the contour and then draw the
            # bounding box on both input images to represent where the two
            # images differ
            area = cv2.contourArea(c)
            if(area>minSize and area<(img1.shape[0]-20)*(img1.shape[1]-20)):
                counts += 1
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(img1, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.rectangle(img2, (x, y), (x + w, y + h), (0, 0, 255), 2)
 
        # show the output images
        #cv2.imshow("Original", img1)
        #cv2.imshow("Modified", img2)
        #cv2.imshow("Diff", diff)
        #cv2.imshow("Thresh", thresh)

        return counts

    def printText(self, txt, bg, color=(0,255,0,0), size=0.7, pos=(0,0), type="Chinese"):
        (b,g,r,a) = color

        if(type=="English"):
            ## Use cv2.FONT_HERSHEY_XXX to write English.
            cv2.putText(bg,  txt, pos, cv2.FONT_HERSHEY_SIMPLEX, size,  (b,g,r), 2, cv2.LINE_AA)

        else:
            ## Use simsum.ttf to write Chinese.
            fontpath = "fonts/wt009.ttf"
            font = ImageFont.truetype(fontpath, int(size*10*4))
            img_pil = Image.fromarray(bg)
            draw = ImageDraw.Draw(img_pil)
            draw.text(pos,  txt, font = font, fill = (b, g, r, a))
            bg = np.array(img_pil)

        return bg

class weight_HX711:
    def __init__(self, referenceUnit):
        import RPi.GPIO as GPIO
        from hx711 import HX711
        self.referenceUnit = referenceUnit
        hx = HX711(5, 6)
        hx.set_reading_format("MSB", "MSB")
        hx.set_reference_unit(referenceUnit)
        hx.reset()
        hx.tare()
        self.hx = hx

    def weight(self):
        hx = self.hx
        hx.power_down()
        hx.power_up()
        time.sleep(0.1)
        val = hx.get_weight(5)
        self.hx = hx

        return val

    def release(self):
        cleanAndExit()
