import sensor,image,lcd,time
from machine import UART        #创建UART对象
from board import board_info
from fpioa_manager import fm    #用于引脚重映射

fm.register(24, fm.fpioa.UART1_TX, force=True)    #24脚映射为TX位接到RX
fm.register(25, fm.fpioa.UART1_RX, force=True)    #25脚映射为RX位接到TX


#颜色阈值范围定义（红，绿，蓝，灰）
color_thr = [(0, 60, 41, 5, 0, 65),(20,60,-70,-10,-0,30),(0, 61, 0, 52, 0, -44),(100,255)]

#初始化串口
uart_A = UART(UART.UART1, baudrate=115200, bits=8, parity=None, stop=1, timeout=1000, read_buf_len=4096)

#串口信息发送函数
def sending_signal(a,x,y,b,c):
        AXY = bytearray([a,x,y,b,c])
        uart_A.write(AXY);
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
data = 17
fx = 0
fy = 0
fper = 0
while True:

#从串口接收数据
    datas = uart_A.read(6) #6字节，每个字节为16进制数据，串口发送端示例：5A 11 11 11 11 00(5A为检验包是否正确的校验码，包尾部数据无所谓，也可以填有效数据)
    if datas!=None:           #去除干扰无用数组
        if datas[0]==0x5A:    #判断包头是否正确
            fx = 0
            fy = 0
            fper = 0
            print(datas);
            data=datas[1];
            data= int(data);
    #获取图像
    img = sensor.snapshot()
    sensor.set_hmirror(1) #图像传感器左右翻转
    sensor.set_vflip(1)   #图像传感器上下翻转
    #img.draw_rectangle([0,0,80,240],thickness=4) #砍掉一部分接近正方形

    #物块识别
    if data == 17:  # （stm32应发送十六进制的11（0x11），下面的依此类推） 红色物块识别
        #print('red');
        #r_blobs = img.find_blobs([color_thr[0]], pixels_threshold=200, area_threshold=1000,roi=(80,0,240,240))#提取roi内的所有红色像素
        r_blobs = img.find_blobs([color_thr[0]], pixels_threshold=200, area_threshold=1000,roi=(0,0,320,240))#提取所有红色像素
        if r_blobs:
            r_blobs = max(r_blobs, key=lambda b: b.pixels())     #选出最大色块
            per = r_blobs.pixels()/57600*100
            per = per*0.7+fper*0.3
            fper = per
            cx = r_blobs.cx()
            #cy = r_blobs.cy()
            dx = cx-160             #获取物块中心点与摄像头中心点坐标偏差值
            dy = r_blobs.cy() - img.height() // 2
            ex = dx*0.7+fy*0.3
            gx = ex*120/160
            ey = -dy*0.7+fx*0.3
            fx = ey
            fy = dx
            img.draw_rectangle(r_blobs.rect())                     #在图像上框住色块
            print("red block (", int(ey), ",", int(gx), ",",int(per), ")")      #在缓存区展示偏差值（用于调试）
            sending_signal(1,int(ey),int(gx),int(per),0x6b);                   #通过串口发送数据给STM32
            #send_data(dx,dy)
            img.draw_string(200,2, ("red"), color=(128,0,0), scale=3)     #在屏幕上展示要识别色块序号
        else:
            sending_signal(0,0,0,0,0x6b);
            print("No Detected")

    if data == 18:  # stm发送的包中有效数应包含12（0x12） 绿色物块识别
        #print('green');
        g_blobs = img.find_blobs([color_thr[1]], pixels_threshold=200, area_threshold=1000,roi=(0,0,320,240))
        if g_blobs:
            g_blobs = max(g_blobs, key=lambda b: b.pixels())
            per = g_blobs.pixels()/57600*100
            per = per*0.7+fper*0.3
            fper = per
            cx = g_blobs.cx()
            dx = cx-160             #获取物块中心点与摄像头中心点坐标偏差值
            dy = g_blobs.cy() - img.height() // 2
            ex = dx*0.7+fy*0.3
            gx = ex*120/160
            ey = -dy*0.7+fx*0.3
            fx = ey
            fy = dx
            img.draw_rectangle(g_blobs.rect())
            print("green block (", int(ey), ",", int(gx), ",",int(per), ")")      #在缓存区展示偏差值（用于调试）
            sending_signal(2,int(ey),int(gx),int(per),0x6b);
            img.draw_string(200,2, ("green"), color=(0,128,0), scale=3)
        else:
            sending_signal(0,0,0,0,0x6b);
            print("No detected")

    if data == 19: # 0x13 蓝色物块识别
        #print('blue');
        b_blobs = img.find_blobs([color_thr[2]], pixels_threshold=200, area_threshold=1000,roi=(0,0,320,240))
        if b_blobs:
            b_blobs = max(b_blobs, key=lambda b: b.pixels())
            per = b_blobs.pixels()/57600*100
            per = per*0.7+fper*0.3
            fper = per
            cx = b_blobs.cx()
            dx = cx-160             #获取物块中心点与摄像头中心点坐标偏差值
            dy = b_blobs.cy() - img.height() // 2
            ex = dx*0.7+fy*0.3
            gx = ex*120/160
            ey = -dy*0.7+fx*0.3
            fx = ey
            fy = dx
            img.draw_rectangle(b_blobs.rect())
            print("blue block (", int(ey), ",", int(gx), ",",int(per), ")")      #在缓存区展示偏差值（用于调试）
            sending_signal(3,int(ey),int(gx),int(per),0x6b);
            img.draw_string(200,2, ("green"), color=(0,0,128), scale=3)
        else:
            sending_signal(0,0,0,0,0x6b);
            print("No Detected")

    #圆环识别
    if data == 33:  # 0x21 识别红色圆环
        #print('r-R');
        img.binary([(0, 76, 7, 63, 42, -11)])           #将图像根据阈值进行二值化处理
        img.dilate(2);                                  #将图像进行膨胀 使得色环糊成整体
        r_blobs = img.find_blobs([gray_thr],area_threshold=150,pixels_threshold=3000,merge=True,roi=(60,0,260,240))  #寻找二值化后的色环
                                                                #roi=(60,0,260,240) 规定目标识别区域，避免车轮以及车身阴影的影响
        img.draw_rectangle([0,0,60,240],thickness=2)            #框线画出不识别区域
        if r_blobs:
            r_blobs = max(r_blobs, key=lambda b: b.pixels())
            dx = r_blobs.cx() - img.width() // 2
            dy = r_blobs.cy() - img.height() // 2
            img.draw_rectangle(r_blobs.rect())
            print("red H (", dx, ",", dy, ")")
            sending_signal(1,dx,dy);
        else:
            sending_signal(0,0,0);#未识别到
            print("No Detected")

    if data == 34:  # 0x34 绿色圆环识别
        #print('g-R');
        img.binary([(0,80,-70,-10,-0,30)])
        img.dilate(2);
        g_blobs = img.find_blobs([gray_thr],area_threshold=150,pixels_threshold=3000,merge=True,roi=(60,0,260,240))
        img.draw_rectangle([0,0,60,240],thickness=2)
        if g_blobs:
            g_blobs = max(g_blobs, key=lambda b: b.pixels())
            dx = g_blobs.cx() - img.width() // 2
            dy = g_blobs.cy() - img.height() // 2
            img.draw_rectangle(g_blobs.rect())
            print("green H (",dx, ",", dy, ")")
            sending_signal(1,dx,dy);
        else:
            sending_signal(0,0,0);
            print("No Detected")

    if data == 35: # 0x35 蓝色圆环识别
        #print('b-R');
        img.binary([(0, 76, -2, 30, -6, -73)])
        img.dilate(2);
        b_blob = img.find_blobs([gray_thr],area_threshold=150,pixels_threshold=3000,merge=True,roi=(60,0,260,240))
        img.draw_rectangle([0,0,60,240],thickness=2)
        if b_blob:
            b_blob = max(b_blob, key=lambda b: b.pixels())
            dx = b_blob.cx() - img.width() // 2
            dy = b_blob.cy() - img.height() // 2
            img.draw_rectangle(b_blob.rect())
            print("blue H (", dx, ",", dy, ")")
            sending_signal(1,dx,dy);
        else:
            sending_signal(0,0,0);
            print("No Detected")
    lcd.display(img)

