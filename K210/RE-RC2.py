import sensor,image,lcd,time
from machine import UART        #创建UART对象
from board import board_info
from fpioa_manager import fm    #用于引脚重映射

fm.register(24, fm.fpioa.UART1_TX, force=True)    #24脚映射为TX位接到RX
fm.register(25, fm.fpioa.UART1_RX, force=True)    #25脚映射为RX位接到TX


#色块颜色阈值范围定义（红，绿，蓝，灰）
color_thr_old = [(0, 60, 41, 5, 0, 65),(20,60,-70,-10,-0,30),(0, 61, 0, 52, 0, -44),(100,255)]
color_thr_test = [(0, 60, 41, 5, 0, 65),(20,60,-70,-10,-0,30),(8, 45, -13, 28, -56, -23),(100,255)]
color_thr = [(0, 60, 41, 5, 0, 65),(20,60,-70,-10,-0,30),(0, 61, 0, 52, -23, -43),(100,255)]
#色环颜色阈值范围定义（红，绿，蓝）
#ring_color_thr = [(30, 100, 15, 127, 15, 127),(30, 100, 0, 127, -64, 64),(0, 76, -2, 30, -6, -73)]

#初始化串口
uart_A = UART(UART.UART1, baudrate=115200, bits=8, parity=None, stop=1, timeout=1000, read_buf_len=4096)

#串口信息发送函数
def sending_data(a,x,y,b,c):
        AXYBC = bytearray([a,x,y,b,c])
        uart_A.write(AXYBC)
#新版串口发送函数
# def send_data(cx,cy):
#     global uart;
#     data = ustruct.pack("<bbhhb",0x2C,0x12,int(cx),int(cy),0x5B)
#     uart.write(data)

# 初始化摄像头
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)#240×320
sensor.skip_frames(time=2000)

# 启动LCD屏幕
lcd.init()
mode = 21
ty = 0
tx = 0
fper = 0
gty =0
gtx = 0
gfper =0
bty =0
btx = 0
bfper =0
while True:

#从串口接收数据
    mdstm = uart_A.read(6) #6字节，每个字节为16进制数据，串口发送端示例：5A 11 11 11 11 00(5A为检验包是否正确的校验码，包尾部数据无所谓，也可以填有效数据)
    if mdstm!=None:           #去除干扰无用数组
        if mdstm[0]==0x5A:    #判断包头是否正确
            ty = 0
            tx = 0
            fper = 0
            print(mdstm)
            mode=mdstm[1]
            mode= int(mode)
    #获取图像
    img = sensor.snapshot()
    sensor.set_hmirror(1) #图像传感器左右翻转
    sensor.set_vflip(1)   #图像传感器上下翻转
    #img.draw_rectangle([0,0,80,240],thickness=4) #死区

    #指定颜色物块识别
    if mode == 17:  # （stm32应发送十六进制的11（0x11），下面的依此类推） 红色物块识别
        #print('red');
        #r_blobs = img.find_blobs([color_thr[0]], pixels_threshold=200, area_threshold=1000,roi=(80,0,240,240))#提取roi内的所有红色像素
        r_blobs = img.find_blobs([color_thr[0]], pixels_threshold=200, area_threshold=1000,roi=(0,0,320,240))#提取所有红色像素
        if r_blobs:
            r_blobs = max(r_blobs, key=lambda b: b.pixels())     #选出最大色块

            per = r_blobs.pixels()/57600*100
            per = per*0.7+fper*0.3
            fper = per

            cx = r_blobs.cx() - 160   #获取物块中心点与摄像头中心点坐标偏差值
            sx = cx*0.7+tx*0.3
            tx = cx
            gx = sx*120/160

            cy = r_blobs.cy() - img.height() // 2
            sy = -cy*0.7+ty*0.3
            ty = sy

            img.draw_rectangle(r_blobs.rect())                     #在图像上框住色块

            print("red block (", int(sy), ",", int(gx), ",",int(per), ")")      #在缓存区展示偏差值（用于调试）

            sending_data(1,int(sy),int(gx),int(per),0x6b);                   #通过串口发送数据给STM32

            img.draw_string(200,2, ("red"), color=(128,0,0), scale=3)     #在屏幕上展示要识别色块序号
        else:
            sending_data(0,0,0,0,0x6b)
            print("No Detected")

    if mode == 18:  # stm发送的包中有效数应包含12（0x12） 绿色物块识别
        #print('green');
        g_blobs = img.find_blobs([color_thr[1]], pixels_threshold=200, area_threshold=1000,roi=(0,0,320,240))
        if g_blobs:
            g_blobs = max(g_blobs, key=lambda b: b.pixels())

            per = g_blobs.pixels()/57600*100
            per = per*0.7+fper*0.3
            fper = per

            cx = g_blobs.cx() - 160   #获取物块中心点与摄像头中心点坐标偏差值
            sx = cx*0.7+tx*0.3
            tx = cx
            gx = sx*120/160

            cy = g_blobs.cy() - img.height() // 2
            sy = -cy*0.7+ty*0.3
            ty = sy

            img.draw_rectangle(g_blobs.rect())
            print("green block (", int(sy), ",", int(gx), ",",int(per), ")")      #在缓存区展示偏差值（用于调试）
            sending_data(2,int(sy),int(gx),int(per),0x6b)
            img.draw_string(200,2, ("green"), color=(0,128,0), scale=3)
        else:
            sending_data(0,0,0,0,0x6b)
            print("No detected")

    if mode == 19: # 0x13 蓝色物块识别
        #print('blue');
        b_blobs = img.find_blobs([color_thr[2]], pixels_threshold=200, area_threshold=1000,roi=(0,0,320,240))
        if b_blobs:
            b_blobs = max(b_blobs, key=lambda b: b.pixels())

            per = b_blobs.pixels()/57600*100
            per = per*0.7+fper*0.3
            fper = per

            cx = b_blobs.cx() - 160   #获取物块中心点与摄像头中心点坐标偏差值
            sx = cx*0.7+tx*0.3
            tx = cx
            gx = sx*120/160

            cy = b_blobs.cy() - img.height() // 2
            sy = -cy*0.7+ty*0.3
            ty = sy

            img.draw_rectangle(b_blobs.rect())
            print("blue block (", int(sy), ",", int(gx), ",",int(per), ")")      #在缓存区展示偏差值（用于调试）
            sending_data(3,int(sy),int(gx),int(per),0x6b)
            img.draw_string(200,2, ("blue"), color=(0,0,128), scale=3)
        else:
            sending_data(0,0,0,0,0x6b)
            print("No Detected")

    if mode == 20:# 0x14 自适应色环识别，6字节，每个字节为16进制数据，串口发送端示例：5A 14 14 14 14 14

    # 查找红色环
        r_blobs = img.find_blobs([color_thr[0]], area_threshold=150,pixels_threshold=3000, merge=True)
    # 查找绿色环
        g_blobs = img.find_blobs([color_thr[1]], area_threshold=150,pixels_threshold=3000, merge=True)
    # 查找蓝色环
        b_blobs = img.find_blobs([color_thr[2]], area_threshold=150,pixels_threshold=3000, merge=True)

        r_detected = False
        g_detected = False
        b_detected = False

        # 标记红色环
        r_detected = False
        for blob in r_blobs:
            #blob = max(r_blobs, key=lambda b: b.pixels())


            cx = blob.cx() - 160   #获取物块中心点与摄像头中心点坐标偏差值
            sx = cx
            gx = sx*120/160

            cy = blob.cy() - img.height() // 2
            sy = -cy


            img.draw_rectangle(blob.rect())  # 绘制矩形框

            print("red ring (", int(sy), ",", int(gx), ",",4, ")")      #在缓存区展示偏差值（用于调试）

            sending_data(1,int(sy),int(gx),4,0x6b);                   #通过串口发送数据给STM32

            img.draw_cross(blob.cx(), blob.cy(),color=(128,0,0), scale=3)  # 绘制交叉线
            img.draw_string(100,2, ("r_ring"), color=(128,0,0), scale=3)     #在屏幕上展示要识别色块序号
            r_detected = True

        # 标记绿色环
        g_detected = False
        for blob in g_blobs:
            #blob = max(r_blobs, key=lambda b: b.pixels())


            cx = blob.cx() - 160   #获取物块中心点与摄像头中心点坐标偏差值
            sx = cx
            gx = sx*120/160

            cy = blob.cy() - img.height() // 2
            sy = -cy

            img.draw_rectangle(blob.rect())  # 绘制矩形框
            #img.draw_rectangle(r_blobs.rect())                     #在图像上框住色块

            print("green ring (", int(sy), ",", int(gx), ",",4, ")")      #在缓存区展示偏差值（用于调试）

            sending_data(2,int(sy),int(gx),4,0x6b);                   #通过串口发送数据给STM32

            img.draw_cross(blob.cx(), blob.cy(),color=(0,128,0), scale=3)  # 绘制交叉线
            img.draw_string(200,2, ("g_ring"), color=(0,128,0), scale=3)     #在屏幕上展示要识别色块序号
            g_detected = True

        # 标记蓝色环
        b_detected = False
        for blob in b_blobs:
            #blob = max(r_blobs, key=lambda b: b.pixels())


            cx = blob.cx() - 160   #获取物块中心点与摄像头中心点坐标偏差值
            sx = cx
            gx = sx*120/160

            cy = blob.cy() - img.height() // 2
            sy = -cy

            img.draw_rectangle(blob.rect())  # 绘制矩形框
            #img.draw_rectangle(r_blobs.rect())                     #在图像上框住色块

            print("blue ring (", int(sy), ",", int(gx), ",",4, ")")      #在缓存区展示偏差值（用于调试）

            sending_data(3,int(sy),int(gx),4,0x6b);                   #通过串口发送数据给STM32

            img.draw_cross(blob.cx(), blob.cy(),color=(0,0,128), scale=3)  # 绘制交叉线
            img.draw_string(2,200, ("b_ring"), color=(0,0,128), scale=3)     #在屏幕上展示要识别色块序号
            b_detected = True
        if not r_detected and not g_detected and not b_detected:
            print("No Ring detected")
        # 延时，避免程序过快执行
        time.sleep(0.1)



    #指定颜色圆环识别
    if mode == 33:  # 0x21 识别红色圆环

        img.binary([(0, 76, 7, 63, 42, -11)])           #将图像根据阈值进行二值化处理

        img.dilate(2);                                  #将图像进行膨胀 使得色环糊成整体
        r_blobs = img.find_blobs([color_thr[3]],area_threshold=150,pixels_threshold=3000,merge=True,roi=(0,0,320,240))  #寻找二值化后的色环 #roi=(60,0,260,240) 规定目标识别区域，避免车轮以及车身阴影的影响
        #img.draw_rectangle([0,0,60,240],thickness=2)            #框线画出不识别区域
        if r_blobs:
            r_blobs = max(r_blobs, key=lambda b: b.pixels())

            # per = r_blobs.pixels()/57600*100
            # per = per*0.7+fper*0.3
            # fper = per

            cx = r_blobs.cx() - 160   #获取物块中心点与摄像头中心点坐标偏差值
            sx = cx*0.7+tx*0.3
            tx = cx
            gx = sx*120/160

            cy = r_blobs.cy() - img.height() // 2
            sy = -cy*0.7+ty*0.3
            ty = sy

            #img.draw_rectangle(r_blobs.rect())
            print("red ring (", int(sy), ",", int(gx), ",",4, ")")      #在缓存区展示偏差值（用于调试）

            sending_data(1,int(sy),int(gx),0,0x5a);                   #通过串口发送数据给STM32

        else:
            sending_data(0,0,0,0,0x5a);
            print("No Rings Detected")

    #指定颜色圆环识别
    if mode == 34:  # 0x22 识别绿色圆环

        img.binary([(0,80,-70,-10,-0,30)])
        img.dilate(2);                                  #将图像进行膨胀 使得色环糊成整体
        g_blobs = img.find_blobs([color_thr[3]],area_threshold=150,pixels_threshold=3000,merge=True,roi=(0,0,320,240))  #寻找二值化后的色环 #roi=(60,0,260,240) 规定目标识别区域，避免车轮以及车身阴影的影响
        #img.draw_rectangle([0,0,60,240],thickness=2)            #框线画出不识别区域
        if g_blobs:
            g_blobs = max(g_blobs, key=lambda b: b.pixels())

            # per = r_blobs.pixels()/57600*100
            # per = per*0.7+fper*0.3
            # fper = per

            cx = g_blobs.cx() - 160   #获取物块中心点与摄像头中心点坐标偏差值
            sx = cx*0.7+tx*0.3
            tx = cx
            gx = sx*120/160

            cy = g_blobs.cy() - img.height() // 2
            sy = -cy*0.7+ty*0.3
            ty = sy

            #img.draw_rectangle(r_blobs.rect())
            print("green ring (", int(sy), ",", int(gx), ",",4, ")")      #在缓存区展示偏差值（用于调试）

            sending_data(2,int(sy),int(gx),0,0x5b);                   #通过串口发送数据给STM32

        else:
            sending_data(0,0,0,0,0x5b);
            print("No Rings Detected")

    #指定颜色圆环识别
    if mode == 35:  # 0x23 识别蓝色圆环

        img.binary([(0, 76, -2, 30, -6, -73)])           #将图像根据阈值进行二值化处理
        img.dilate(2);                                  #将图像进行膨胀 使得色环糊成整体
        b_blobs = img.find_blobs([color_thr[3]],area_threshold=150,pixels_threshold=3000,merge=True,roi=(0,0,320,240))  #寻找二值化后的色环 #roi=(60,0,260,240) 规定目标识别区域，避免车轮以及车身阴影的影响
        #img.draw_rectangle([0,0,60,240],thickness=2)            #框线画出不识别区域
        if b_blobs:
            b_blobs = max(b_blobs, key=lambda b: b.pixels())

            # per = r_blobs.pixels()/57600*100
            # per = per*0.7+fper*0.3
            # fper = per

            cx = b_blobs.cx() - 160   #获取物块中心点与摄像头中心点坐标偏差值
            sx = cx*0.7+tx*0.3
            tx = cx
            gx = sx*120/160

            cy = b_blobs.cy() - img.height() // 2
            sy = -cy*0.7+ty*0.3
            ty = sy

            #img.draw_rectangle(r_blobs.rect())
            print("red ring (", int(sy), ",", int(gx), ",",4, ")")      #在缓存区展示偏差值（用于调试）

            sending_data(3,int(sy),int(gx),0,0x5c);                   #通过串口发送数据给STM32

        else:
            sending_data(0,0,0,0,0x5c);
            print("No Rings Detected")

    #自适应物块识别
    if mode == 21:

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
            per = per*0.7+fper*0.3
            fper = per

            cx = r_blob.cx() - 160   #获取物块中心点与摄像头中心点坐标偏差值
            sx = cx*0.7+tx*0.3
            tx = cx
            gx = sx*120/160

            cy = r_blob.cy() - img.height() // 2
            sy = -cy*0.7+ty*0.3
            ty = sy

            img.draw_rectangle(r_blob.rect())                     #在图像上框住色块

            print("red block (", int(sy), ",", int(gx), ",",int(per), ")")      #在缓存区展示偏差值（用于调试）

            sending_data(1,int(sy),int(gx),int(per),0x6b);                   #通过串口发送数据给STM32

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

            sending_data(2,int(gsy),int(ggx),int(gper),0x6b);                   #通过串口发送数据给STM32

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

            sending_data(3,int(bsy),int(bgx),int(bper),0x6b);                   #通过串口发送数据给STM32

            img.draw_string(2,200, ("blue"), color=(0,0,128), scale=3)     #在屏幕上展示要识别色块序号
            b_detected = True
        if not r_detected and not g_detected and not b_detected:
            print("No detected")
        # 延时，避免程序过快执行
        time.sleep(0.1)

    lcd.display(img)

