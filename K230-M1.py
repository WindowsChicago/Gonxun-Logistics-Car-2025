'''
实验名称：图像3种显示方式
实验平台：01Studio CanMV K230
说明：实现摄像头图像采集通过IDE、HDMI和MIPI屏显示
'''

import time, os, sys

from media.sensor import * #导入sensor模块，使用摄像头相关接口
from media.display import * #导入display模块，使用display相关接口
from media.media import * #导入media模块，使用meida相关接口

#色块颜色阈值范围定义（红，绿，蓝，灰）# 可以使用 工具-> 机器视觉 -> 阈值编辑器 来调整阈值.# (0,100,0,100,0,100) L A B
color_thr_old = [(0, 60, 41, 5, 0, 65),(20,60,-70,-10,-0,30),(0, 61, 0, 52, 0, -44),(100,255)]
color_thr = [(0, 60, 41, 5, 0, 65),(20, 57, -62, -13, 3, 31),(0, 61, 0, 52, -23, -43),(100,255)]
#color_thr = [(0, 60, 41, 5, 0, 65),(20,60,-70,-10,-0,30),(0, 61, 0, 52, -23, -43),(100,255)]
#色环颜色阈值范围定义（红，绿，蓝）
ring_col_bin= [(0, 76, 7, 63, 42, -11),(0,80,-70,-10,-0,30),(0, 76, -2, 30, -6, -73)]

ring_col_bin1 = [(0, 76, 7, 63, 42, -11),(0, 85, -70, -4, 0, 28),(0, 80, 0, 30, -4, -72)]

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

try:

    sensor = Sensor() #构建摄像头对象
    sensor.reset() #复位和初始化摄像头
    #sensor.set_framesize(Sensor.FHD) #设置帧大小FHD(1920x1080)，缓冲区和HDMI用,默认通道0
    sensor.set_framesize(width=800,height=480) #设置帧大小800x480,LCD专用,默认通道0
    sensor.set_pixformat(Sensor.RGB565) #设置输出图像格式，默认通道0

    #################################
    ## 图像3种不同显示方式（修改注释实现）
    #################################

    #Display.init(Display.VIRT, sensor.width(), sensor.height()) #通过IDE缓冲区显示图像
    #Display.init(Display.LT9611, to_ide=True) #通过HDMI显示图像
    Display.init(Display.ST7701, to_ide=True) #通过01Studio 3.5寸mipi显示屏显示图像

    MediaManager.init() #初始化media资源管理器

    sensor.run() #启动sensor

    clock = time.clock()

    while True:


        os.exitpoint() #检测IDE中断

        #获取图像
        img = sensor.snapshot()
        #sensor.set_hmirror(1) #图像传感器左右翻转
        #sensor.set_vflip(1)   #图像传感器上下翻转
        Display.show_image(img) #显示图片
        #img.draw_rectangle([0,0,80,240],thickness=4) #死区

        #自适应物块识别
        if mode == 21:# 0x15，串口发送端示例：5A 15 15 15 15 15

            r_blobs = img.find_blobs([color_thr[0]], pixels_threshold=200, area_threshold=1000,roi=(0,0,320,240))#提取所有红色像素
            g_blobs = img.find_blobs([color_thr[1]], pixels_threshold=200, area_threshold=1000,roi=(0,0,320,240))
            b_blobs = img.find_blobs([color_thr[2]], pixels_threshold=200, area_threshold=1000,roi=(0,0,320,240))

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

                #sending_data(2,int(gsy),int(ggx),int(gper),0x6b);                   #通过串口发送数据给STM32

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

        #指定颜色圆环识别
        if mode == 33:  # 0x21 识别红色圆环，6字节，每个字节为16进制数据，串口发送端示例：5A 21 21 21 21 21

            img.binary([ring_col_bin[0]])           #将图像根据阈值进行二值化处理

            img.dilate(2);                                  #将图像进行膨胀 使得色环糊成整体
            r_blobs = img.find_blobs([color_thr[3]],area_threshold=150,pixels_threshold=3000,merge=True,roi=(0,0,320,240))  #寻找二值化后的色环 #roi=(60,0,260,240) 规定目标识别区域，避免车轮以及车身阴影的影响
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
            g_blobs = img.find_blobs([color_thr[3]],area_threshold=150,pixels_threshold=3000,merge=True,roi=(0,0,320,240))  #寻找二值化后的色环 #roi=(60,0,260,240) 规定目标识别区域，避免车轮以及车身阴影的影响
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
            b_blobs = img.find_blobs([color_thr[3]],area_threshold=150,pixels_threshold=3000,merge=True,roi=(0,0,320,240))  #寻找二值化后的色环 #roi=(60,0,260,240) 规定目标识别区域，避免车轮以及车身阴影的影响
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
        #clock.tick()

        #img = sensor.snapshot() #拍摄一张图

       #Display.show_image(img) #显示图片

        print(clock.fps()) #打印FPS


###################
# IDE中断释放资源代码
###################
except KeyboardInterrupt as e:
    print("user stop: ", e)
except BaseException as e:
    print(f"Exception {e}")
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
