import time, os, gc, sys, math
from machine import Pin,Timer
from media.sensor import *
from media.display import *
from media.media import *
#导入串口模块
from machine import UART
from machine import FPIOA
import time

DETECT_WIDTH = 640
DETECT_HEIGHT = 480

fpioa = FPIOA()

# UART1代码
fpioa.set_function(3,FPIOA.UART1_TXD)
fpioa.set_function(4,FPIOA.UART1_RXD)

uart=UART(UART.UART1,baudrate=115200) #设置串口号1和波特率

#串口信息发送函数
def sending_data(a,x,y,b,c):
        AXYBC = bytearray([a,x,y,b,c])
        uart.write(AXYBC)

#色块颜色阈值范围定义（红，绿，蓝，灰）# 可以使用 工具-> 机器视觉 -> 阈值编辑器 来调整阈值.# (0,100,0,100,0,100) L A B
color_thr_old = [(0, 60, 41, 5, 0, 65),(20,60,-70,-10,-0,30),(0, 61, 0, 52, 0, -44),(100,255)]
color_thr = [(0, 60, 41, 5, 0, 65),(20, 57, -62, -13, 3, 31),(0, 61, 0, 52, -23, -43),(100,255)]
#color_thr = [(0, 60, 41, 5, 0, 65),(20,60,-70,-10,-0,30),(0, 61, 0, 52, -23, -43),(100,255)]

#色环颜色阈值范围定义（红，绿，蓝）
ring_col_bin= [(0, 76, 7, 63, 42, -11),(0,80,-70,-10,-0,30),(0, 76, 0, 30, -14, -73)]

#ring_col_bin1 = [(0, 76, 7, 63, 42, -11),(0, 85, -70, -4, 0, 28),(0, 80, 0, 30, -4, -72)]
sensor = None

try:
    sensor = Sensor(width = DETECT_WIDTH, height = DETECT_HEIGHT)
    sensor.reset()
    sensor.set_framesize(width = DETECT_WIDTH, height = DETECT_HEIGHT)
    sensor.set_pixformat(Sensor.RGB565)

    # use lcd as display output
    Display.init(Display.ST7701, to_ide = True)

    # use IDE as output
    Display.init(Display.VIRT, width = DETECT_WIDTH, height = DETECT_HEIGHT, fps = 100)

    # init media manager
    MediaManager.init()

    mode =21
    modebuf =0

    # sensor start run
    sensor.run()

    fps = time.clock()

    while True:
        fps.tick()
        #从串口接收数据
        modes=uart.read(2) #接收2个字符的bytes型数组，例如：b'5A 21'可以使用bytesarry或list函数转换为可操作序列,
        if modes != b'':       #验证是否为空
            b = list(modes)     #将字符数组转为序列，例：[90,33]
            if b[0] == 90:     #90即十六进制数5A对应的十进制数，起数据校验作用
                mode = b[1]
                rcx=0
                rcy=0
                gcx=0
                gxy=0
                bcx=0
                bcy=0

        # check if should exit.
        os.exitpoint()

        img = sensor.snapshot()

        if mode == 33:  # 0x21 识别红色圆环，2字节，每个字节为16进制数据，串口发送端示例：5A 21

            img.binary([ring_col_bin[0]])           #将图像根据阈值进行二值化处理

            img.dilate(2);                                  #将图像进行膨胀 使得色环糊成整体
            r_blobs = img.find_blobs([color_thr[3]],area_threshold=150,pixels_threshold=3000,merge=True)

            if r_blobs:
                r_blobs = max(r_blobs, key=lambda b: b.pixels())

                rcx = -(r_blobs.cx()-320)
                rcy = r_blobs.cy()-240
                rsx = rcx//2.6
                rsy = rcy//2

                #img.draw_rectangle(r_blobs.rect())
                print("red ring (", int(rsx), ",", int(rsy), ",",4, ")")      #在缓存区展示值（用于调试）

                sending_data(1,int(rsx),int(rsy),int(0),0x5a);                #通过串口发送数据给STM32

            else:
                sending_data(0,0,0,0,0x5a)
                print("No Rings Detected")
            modebuf=mode
        if mode == 34:  # 0x22 识别绿色圆环，串口发送端示例：5A 22

            img.binary([ring_col_bin[1]])
            img.dilate(2);                                  #将图像进行膨胀 使得色环糊成整体
            g_blobs = img.find_blobs([color_thr[3]],area_threshold=150,pixels_threshold=3000,merge=True)  #寻找二值化后的色环 #roi=(60,0,260,240) 规定目标识别区域，避免车轮以及车身阴影的影响

            if g_blobs:
                g_blobs = max(g_blobs, key=lambda b: b.pixels())

                gcx = -(g_blobs.cx()-320)
                gcy = g_blobs.cy()-240
                gsx = gcx//2.6
                gsy = gcy//2

                #img.draw_rectangle(r_blobs.rect())
                print("green ring (", int(gsx), ",", int(gsy), ",",4, ")")

                sending_data(2,int(gsx),int(gsy),int(0),0x5b);

            else:
                sending_data(0,0,0,0,0x5b)
                print("No Rings Detected")
            modebuf=mode

        if mode == 35:  # 0x23 识别蓝色圆环，串口发送端示例：5A 22

            img.binary([ring_col_bin[2]])           #将图像根据阈值进行二值化处理
            img.dilate(2);                                  #将图像进行膨胀 使得色环糊成整体
            b_blobs = img.find_blobs([color_thr[3]],area_threshold=150,pixels_threshold=3000,merge=True)  #寻找二值化后的色环 #roi=(60,0,260,240) 规定目标识别区域，避免车轮以及车身阴影的影响

            if b_blobs:
                b_blobs = max(b_blobs, key=lambda b: b.pixels())

                bcx = -(b_blobs.cx()-320)
                bcy = b_blobs.cy()-240
                bsx = bcx//2.6
                bsy = bcy//2

                #img.draw_rectangle(r_blobs.rect())
                print("blue ring (", int(bsx), ",", int(bsy), ",",4, ")")

                sending_data(3,int(bsx),int(bsy),0,0x5c);

            else:
                sending_data(0,0,0,0,0x5c)
                print("No Rings Detected")
            modebuf=mode

        #自适应物块识别
        if mode == 21:# 0x15，串口发送端示例：5A 15

            r_blobs = img.find_blobs([color_thr[0]], pixels_threshold=200, area_threshold=1000)#提取所有红色像素
            g_blobs = img.find_blobs([color_thr[1]], pixels_threshold=200, area_threshold=1000)
            b_blobs = img.find_blobs([color_thr[2]], pixels_threshold=200, area_threshold=1000)

            r_detected = False
            g_detected = False
            b_detected = False

            r_detected = False
            for r_blob in r_blobs:
                r_blob = max(r_blobs, key=lambda b: b.pixels())     #选出最大色块

                rcx = -(r_blob.cx()-320)
                rcy = r_blob.cy()-240
                rsx = rcx//2.6
                rsy = rcy//2


                img.draw_rectangle(r_blob.rect())                     #在图像上框住色块

                print("red block (", int(rsx), ",", int(rsy), ",",int(0), ")")      #在缓存区展示值（用于调试）

                sending_data(1,int(rsx),int(rsy),int(0),0x6b);                   #通过串口发送数据给STM32

                img.draw_string(200,2, ("red"), color=(128,0,0), scale=3)     #在屏幕上展示要识别色块序号
                r_detected = True

            g_detected = False
            for g_blob in g_blobs:
                g_blob = max(g_blobs, key=lambda b: b.pixels())

                gcx = -(g_blob.cx()-320)
                gcy = g_blob.cy()-240
                gsx = gcx//2.6
                gsy = gcy//2

                img.draw_rectangle(g_blob.rect())

                print("green block (", int(gsx), ",", int(gsy), ",",int(0), ")")      #在缓存区展示值（用于调试）

                sending_data(2,int(gsx),int(gsy),int(0),0x6b);

                img.draw_string(100,2, ("green"), color=(0,128,0), scale=3)
                g_detected = True

            b_detected = False
            for b_blob in b_blobs:
                b_blob = max(b_blobs, key=lambda b: b.pixels())

                bcx = -(b_blob.cx()-320)
                bcy = b_blob.cy()-240
                bsx = bcx//2.6
                bsy = bcy//2

                img.draw_rectangle(b_blob.rect())

                print("blue block (", int(bsx), ",", int(bsy), ",",int(0), ")")

                sending_data(3,int(bsx),int(bsy),int(0),0x6b);

                img.draw_string(2,200, ("blue"), color=(0,0,128), scale=3)
                b_detected = True
            if not r_detected and not g_detected and not b_detected:
                print("No detected")
                sending_data(0,0,0,0,0x6b);
            # 延时，避免程序过快执行
            time.sleep(0.1)
            modebuf=mode

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
