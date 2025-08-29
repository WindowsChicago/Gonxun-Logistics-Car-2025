import time, os, gc, sys, math

from media.sensor import *
from media.display import *
from media.media import *

DETECT_WIDTH = 800
DETECT_HEIGHT = 480

#thresholds = [(12, 100, -47, 14, -1, 58), # generic_red_thresholds -> index is 0 so code == (1 << 0)
 #             (30, 100, -64, -8, -32, 32)] # generic_green_thresholds -> index is 1 so code == (1 << 1)

#色块颜色阈值范围定义（红，绿，蓝，灰）# 可以使用 工具-> 机器视觉 -> 阈值编辑器 来调整阈值.# (0,100,0,100,0,100) L A B
color_thr_old = [(0, 60, 41, 5, 0, 65),(20,60,-70,-10,-0,30),(0, 61, 0, 52, 0, -44),(100,255)]
color_thr = [(0, 60, 41, 5, 0, 65),(20, 57, -62, -13, 3, 31),(0, 61, 0, 52, -23, -43),(100,255)]
#color_thr = [(0, 60, 41, 5, 0, 65),(20,60,-70,-10,-0,30),(0, 61, 0, 52, -23, -43),(100,255)]
#色环颜色阈值范围定义（红，绿，蓝）
ring_col_bin= [(0, 76, 7, 63, 42, -11),(0,80,-70,-10,-0,30),(0, 76, -2, 30, -6, -73)]

ring_col_bin1 = [(0, 76, 7, 63, 42, -11),(0, 85, -70, -4, 0, 28),(0, 80, 0, 30, -4, -72)]

sensor = None

try:
    sensor = Sensor(width = DETECT_WIDTH, height = DETECT_HEIGHT)
    # sensor reset
    sensor.reset()
    # set hmirror
    # sensor.set_hmirror(False)
    # sensor vflip
    # sensor.set_vflip(False)
    # set chn0 output size
    sensor.set_framesize(width = DETECT_WIDTH, height = DETECT_HEIGHT)
    # set chn0 output format
    sensor.set_pixformat(Sensor.RGB565)

    # use lcd as display output
    Display.init(Display.ST7701, to_ide = True)

    # use IDE as output
    Display.init(Display.VIRT, width = DETECT_WIDTH, height = DETECT_HEIGHT, fps = 100)

    # init media manager
    MediaManager.init()

    mode =21
    rty = 0
    rtx = 0
    rfper = 0
    gty =0
    gtx = 0
    gfper =0
    bty =0
    btx = 0
    bfper =0

    # sensor start run
    sensor.run()

    fps = time.clock()

    while True:
        fps.tick()

        # check if should exit.
        os.exitpoint()
        img = sensor.snapshot()
        if mode == 33:  # 0x21 识别红色圆环，6字节，每个字节为16进制数据，串口发送端示例：5A 21 21 21 21 21

            img.binary([ring_col_bin[0]])           #将图像根据阈值进行二值化处理

            img.dilate(2);                                  #将图像进行膨胀 使得色环糊成整体
            r_blobs = img.find_blobs([color_thr[3]],area_threshold=150,pixels_threshold=3000,merge=True)  #寻找二值化后的色环 #roi=(60,0,260,240) 规定目标识别区域，避免车轮以及车身阴影的影响
            #img.draw_rectangle([0,0,60,240],thickness=2)            #框线画出不识别区域
            if r_blobs:
                r_blobs = max(r_blobs, key=lambda b: b.pixels())

                # per = r_blobs.pixels()/57600*100
                # per = per*0.7+fper*0.3
                # fper = per

                cx = r_blobs.cx() - 160   #获取物块中心点与摄像头中心点坐标偏差值
                sx = cx*0.7+rtx*0.3
                rtx = cx
                gx = sx*120/160

                cy = r_blobs.cy() - img.height() // 2
                sy = -cy*0.7+rty*0.3
                rty = sy

                #img.draw_rectangle(r_blobs.rect())
                print("red ring (", int(sy), ",", int(gx), ",",4, ")")      #在缓存区展示偏差值（用于调试）

                #sending_data(1,int(sy),int(gx),0,0x5a);                   #通过串口发送数据给STM32

            else:
                #sending_data(0,0,0,0,0x5a);
                print("No Rings Detected")
        if mode == 34:  # 0x22 识别绿色圆环，串口发送端示例：5A 22 22 22 22 22

            img.binary([ring_col_bin[1]])
            img.dilate(2);                                  #将图像进行膨胀 使得色环糊成整体
            g_blobs = img.find_blobs([color_thr[3]],area_threshold=150,pixels_threshold=3000,merge=True)  #寻找二值化后的色环 #roi=(60,0,260,240) 规定目标识别区域，避免车轮以及车身阴影的影响
            #img.draw_rectangle([0,0,60,240],thickness=2)            #框线画出不识别区域
            if g_blobs:
                g_blobs = max(g_blobs, key=lambda b: b.pixels())

                # per = r_blobs.pixels()/57600*100
                # per = per*0.7+fper*0.3
                # fper = per

                cx = g_blobs.cx() - 160   #获取物块中心点与摄像头中心点坐标偏差值
                sx = cx*0.7+rtx*0.3
                rtx = cx
                gx = sx*120/160

                cy = g_blobs.cy() - img.height() // 2
                sy = -cy*0.7+rty*0.3
                rty = sy

                #img.draw_rectangle(r_blobs.rect())
                print("green ring (", int(sy), ",", int(gx), ",",4, ")")      #在缓存区展示偏差值（用于调试）

                #sending_data(2,int(sy),int(gx),0,0x5b);                   #通过串口发送数据给STM32

            else:
                #sending_data(0,0,0,0,0x5b);
                print("No Rings Detected")

        if mode == 35:  # 0x23 识别蓝色圆环，串口发送端示例：5A 22 22 22 22 22

            img.binary([ring_col_bin[2]])           #将图像根据阈值进行二值化处理
            img.dilate(2);                                  #将图像进行膨胀 使得色环糊成整体
            b_blobs = img.find_blobs([color_thr[3]],area_threshold=150,pixels_threshold=3000,merge=True)  #寻找二值化后的色环 #roi=(60,0,260,240) 规定目标识别区域，避免车轮以及车身阴影的影响
            #img.draw_rectangle([0,0,60,240],thickness=2)            #框线画出不识别区域
            if b_blobs:
                b_blobs = max(b_blobs, key=lambda b: b.pixels())

                # per = r_blobs.pixels()/57600*100
                # per = per*0.7+fper*0.3
                # fper = per

                cx = b_blobs.cx() - 160   #获取物块中心点与摄像头中心点坐标偏差值
                sx = cx*0.7+rtx*0.3
                rtx = cx
                gx = sx*120/160

                cy = b_blobs.cy() - img.height() // 2
                sy = -cy*0.7+rty*0.3
                rty = sy

                #img.draw_rectangle(r_blobs.rect())
                print("red ring (", int(sy), ",", int(gx), ",",4, ")")      #在缓存区展示偏差值（用于调试）

                #sending_data(3,int(sy),int(gx),0,0x5c);                   #通过串口发送数据给STM32

            else:
                #sending_data(0,0,0,0,0x5c);
                print("No Rings Detected")

        #自适应物块识别
        if mode == 21:# 0x15，串口发送端示例：5A 15 15 15 15 15

            r_blobs = img.find_blobs([color_thr[0]], pixels_threshold=200, area_threshold=1000)#提取所有红色像素
            g_blobs = img.find_blobs([color_thr[1]], pixels_threshold=200, area_threshold=1000)
            b_blobs = img.find_blobs([color_thr[2]], pixels_threshold=200, area_threshold=1000)

            r_detected = False
            g_detected = False
            b_detected = False

            r_detected = False
            for r_blob in r_blobs:
                r_blob = max(r_blobs, key=lambda b: b.pixels())     #选出最大色块

                per = r_blob.pixels()/57600*100
                per = per*0.7+rfper*0.3
                rfper = per

                cx = r_blob.cx() - 160   #获取物块中心点与摄像头中心点坐标偏差值
                sx = cx*0.7+rtx*0.3
                rtx = cx
                gx = sx*120/160

                cy = r_blob.cy() - img.height() // 2
                sy = -cy*0.7+rty*0.3
                rty = sy

                img.draw_rectangle(r_blob.rect())                     #在图像上框住色块

                print("red block (", int(sy), ",", int(gx), ",",int(per), ")")      #在缓存区展示偏差值（用于调试）

                #sending_data(1,int(sy),int(gx),int(per),0x6b);                   #通过串口发送数据给STM32

                img.draw_string(200,2, ("red"), color=(128,0,0), scale=3)     #在屏幕上展示要识别色块序号
                r_detected = True

            g_detected = False
            for g_blob in g_blobs:
                g_blob = max(g_blobs, key=lambda b: b.pixels())     #选出最大色块

                gper = g_blob.pixels()/57600*100
                gper = gper*0.7+gfper*0.3
                gfper = gper

                gcx = g_blob.cx() - 160   #获取物块中心点与摄像头中心点坐标偏差值
                gsx = gcx*0.7+gtx*0.3
                gtx = gcx
                ggx = gsx*120/160

                gcy = g_blob.cy() - img.height() // 2
                gsy = -gcy*0.7+gty*0.3
                gty = gsy

                img.draw_rectangle(g_blob.rect())                     #在图像上框住色块

                print("green block (", int(gsy), ",", int(ggx), ",",int(gper), ")")      #在缓存区展示偏差值（用于调试）

               # sending_data(2,int(gsy),int(ggx),int(gper),0x6b);                   #通过串口发送数据给STM32

                img.draw_string(100,2, ("green"), color=(0,128,0), scale=3)     #在屏幕上展示要识别色块序号
                g_detected = True

            b_detected = False
            for b_blob in b_blobs:
                b_blob = max(b_blobs, key=lambda b: b.pixels())     #选出最大色块

                bper = b_blob.pixels()/57600*100
                bper = bper*0.7+bfper*0.3
                bfper = bper

                bcx = b_blob.cx() - 160   #获取物块中心点与摄像头中心点坐标偏差值
                bsx = bcx*0.7+btx*0.3
                btx = bcx
                bgx = bsx*120/160

                bcy = b_blob.cy() - img.height() // 2
                bsy = -bcy*0.7+bty*0.3
                bty = bsy

                img.draw_rectangle(b_blob.rect())                     #在图像上框住色块

                print("blue block (", int(bsy), ",", int(bgx), ",",int(bper), ")")      #在缓存区展示偏差值（用于调试）

                #sending_data(3,int(bsy),int(bgx),int(bper),0x6b);                   #通过串口发送数据给STM32

                img.draw_string(2,200, ("blue"), color=(0,0,128), scale=3)     #在屏幕上展示要识别色块序号
                b_detected = True
            if not r_detected and not g_detected and not b_detected:
                print("No detected")
            # 延时，避免程序过快执行
            time.sleep(0.1)



        # draw result to screen
        Display.show_image(img)
        gc.collect()

        print(fps.fps())
except KeyboardInterrupt as e:
    print(f"user stop")
except BaseException as e:
    print(f"Exception '{e}'")
finally:
    # sensor stop run
    if isinstance(sensor, Sensor):
        sensor.stop()
    # deinit display
    Display.deinit()

    os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
    time.sleep_ms(100)

    # release media buffer
    MediaManager.deinit()
