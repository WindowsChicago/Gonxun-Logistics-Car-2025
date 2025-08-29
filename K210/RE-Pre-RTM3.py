import sensor,image,lcd,time
from machine import UART        #创建UART对象
from board import board_info
from fpioa_manager import fm    #用于引脚重映射

fm.register(24, fm.fpioa.UART1_TX, force=True)    #24脚映射为TX位接到RX
fm.register(25, fm.fpioa.UART1_RX, force=True)    #25脚映射为RX位接到TX


#色块颜色阈值范围定义（红，绿，蓝，灰）# 可以使用 工具-> 机器视觉 -> 阈值编辑器 来调整阈值.# (0,100,0,100,0,100) L A B
color_thr_old = [(0, 60, 41, 5, 0, 65),(20,60,-70,-10,-0,30),(0, 61, 0, 52, 0, -44),(100,255)]
color_thr = [(0, 60, 41, 5, 0, 65),(20, 57, -62, -13, 3, 31),(0, 61, 0, 52, -23, -43),(100,255)]
#color_thr = [(0, 60, 41, 5, 0, 65),(20,60,-70,-10,-0,30),(0, 61, 0, 52, -23, -43),(100,255)]
#色环颜色阈值范围定义（红，绿，蓝）
ring_col_bin= [(0, 76, 7, 63, 42, -11),(0,80,-70,-10,-0,30),(0, 76, -2, 30, -6, -73)]

ring_col_bin1 = [(0, 76, 7, 63, 42, -11),(0, 85, -70, -4, 0, 28),(0, 80, 0, 30, -4, -72)]

#初始化串口
uart_A = UART(UART.UART1, baudrate=115200, bits=8, parity=None, stop=1, timeout=1000, read_buf_len=4096)

#串口信息发送函数
def sending_data(a,x,y,b,c):
        AXYBC = bytearray([a,x,y,b,c])
        uart_A.write(AXYBC)


# 初始化摄像头
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)#240×320
sensor.skip_frames(time=2000)

# 启动LCD屏幕
lcd.init()
mode =21
modebuf =0
rty = 0
rtx = 0

gty =0
gtx = 0

bty =0
btx = 0


while True:

    #从串口接收数据
    modes = uart_A.read(2) #6字节，每个字节为16进制数据，串口发送端示例：5A 11(5A为检验包是否正确的校验码，包尾部数据无所谓，也可以填有效数据)
    if modes is not None and len(modes) == 2 and modes[0] == 0x5A and modes[1]!=modebuf:
        mode = int(modes[1])
        rty = 0
        rtx = 0
        gty =0
        gtx = 0
        bty =0
        btx = 0
    #获取图像
    img = sensor.snapshot()
    sensor.set_hmirror(1) #图像传感器左右翻转
    sensor.set_vflip(1)   #图像传感器上下翻转

    #自适应物块识别
    if mode == 21:# 0x15，串口发送端示例：5A 15

        r_blobs = img.find_blobs([color_thr[0]], pixels_threshold=200, area_threshold=1000,roi=(0,0,320,240))#提取所有红色像素
        g_blobs = img.find_blobs([color_thr[1]], pixels_threshold=200, area_threshold=1000,roi=(0,0,320,240))
        b_blobs = img.find_blobs([color_thr[2]], pixels_threshold=200, area_threshold=1000,roi=(0,0,320,240))

        r_detected = False
        g_detected = False
        b_detected = False

        r_detected = False
        for r_blob in r_blobs:
            r_blob = max(r_blobs, key=lambda b: b.pixels())     #选出最大色块

            #per = r_blob.pixels()/57600*100
            #per = per*0.7+rfper*0.3
            #rfper = per

            cx = r_blob.cx() - 160   #获取物块中心点与摄像头中心点坐标偏差值
            sx = cx*0.7+rtx*0.3
            rtx = cx
            gx = sx*120/160

            cy = r_blob.cy() - img.height() // 2
            sy = -cy*0.7+rty*0.3
            rty = sy

            img.draw_rectangle(r_blob.rect())                     #在图像上框住色块

            print("red block (", int(sy), ",", int(gx), ",",int(0), ")")      #在缓存区展示偏差值（用于调试）

            sending_data(1,int(sy),int(gx),int(0),0x6b);                   #通过串口发送数据给STM32

            img.draw_string(200,2, ("red"), color=(128,0,0), scale=3)     #在屏幕上展示要识别色块序号
            r_detected = True

        g_detected = False
        for g_blob in g_blobs:
            g_blob = max(g_blobs, key=lambda b: b.pixels())     #选出最大色块

            #gper = g_blob.pixels()/57600*100
            #gper = gper*0.7+gfper*0.3
            #gfper = gper

            gcx = g_blob.cx() - 160   #获取物块中心点与摄像头中心点坐标偏差值
            gsx = gcx*0.7+gtx*0.3
            gtx = gcx
            ggx = gsx*120/160

            gcy = g_blob.cy() - img.height() // 2
            gsy = -gcy*0.7+gty*0.3
            gty = gsy

            img.draw_rectangle(g_blob.rect())                     #在图像上框住色块

            print("green block (", int(gsy), ",", int(ggx), ",",int(0), ")")      #在缓存区展示偏差值（用于调试）

            sending_data(2,int(gsy),int(ggx),int(0),0x6b);                   #通过串口发送数据给STM32

            img.draw_string(100,2, ("green"), color=(0,128,0), scale=3)     #在屏幕上展示要识别色块序号
            g_detected = True

        b_detected = False
        for b_blob in b_blobs:
            b_blob = max(b_blobs, key=lambda b: b.pixels())     #选出最大色块

            #bper = b_blob.pixels()/57600*100
            #bper = bper*0.7+bfper*0.3
            #bfper = bper

            bcx = b_blob.cx() - 160   #获取物块中心点与摄像头中心点坐标偏差值
            bsx = bcx*0.7+btx*0.3
            btx = bcx
            bgx = bsx*120/160

            bcy = b_blob.cy() - img.height() // 2
            bsy = -bcy*0.7+bty*0.3
            bty = bsy

            img.draw_rectangle(b_blob.rect())                     #在图像上框住色块

            print("blue block (", int(bsy), ",", int(bgx), ",",int(0), ")")      #在缓存区展示偏差值（用于调试）

            sending_data(3,int(bsy),int(bgx),int(0),0x6b);                   #通过串口发送数据给STM32

            img.draw_string(2,200, ("blue"), color=(0,0,128), scale=3)     #在屏幕上展示要识别色块序号
            b_detected = True
        if not r_detected and not g_detected and not b_detected:
            print("No detected")
        # 延时，避免程序过快执行
        time.sleep(0.1)
        modebuf=mode

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

            sending_data(1,int(sy),int(gx),0,0x5a);                   #通过串口发送数据给STM32

        else:
            sending_data(0,0,0,0,0x5a)
            print("No Rings Detected")
        modebuf=mode
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

            sending_data(2,int(sy),int(gx),0,0x5b);                   #通过串口发送数据给STM32

        else:
            sending_data(0,0,0,0,0x5b)
            print("No Rings Detected")
        modebuf=mode
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

            sending_data(3,int(sy),int(gx),0,0x5c);                   #通过串口发送数据给STM32

        else:
            sending_data(0,0,0,0,0x5c)
            print("No Rings Detected")
        modebuf=mode

    lcd.display(img)

