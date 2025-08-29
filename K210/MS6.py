
import sensor,image,lcd,time
from machine import UART        #创建UART对象
from board import board_info
from fpioa_manager import fm    #用于引脚重映射
from Maix import GPIO
import utime
#fm.register(10, fm.fpioa.UART1_TX, force=True)    #TX映射到24引脚
#fm.register(9, fm.fpioa.UART1_RX, force=True)    #RX映射到25引脚

#映射UART2的两个引脚
fm.register(GPIO.GPIOHS9,fm.fpioa.UART2_TX)
fm.register(GPIO.GPIOHS10,fm.fpioa.UART2_RX)


#颜色阈值范围定义
gray_thr = (100,255)
green_thr = (20,60,-70,-10,-0,30)
blue_thr = (0, 61, 0, 52, 0, -44)
red_thr = (0, 60, 41, 5, 0, 65)
#初始化串口
uart_A = UART(UART.UART1, baudrate=115200, bits=8, parity=None, stop=1, timeout=1000, read_buf_len=4096)
#uart_A = UART(UART.UART1, 115200, 8, 0, 1, timeout=1000, read_buf_len=4096)

#串口信息发送函数
def sending_signal(a,x,y):
        AXY = bytearray([a,x,y])
        uart_A.write(AXY);

# 初始化摄像头
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)

clock = time.clock()
# 启动LCD屏幕
lcd.init()
data = 10
while True:

    #read_str = uart_A.read(10)
    #utime.sleep_ms(100)
    #if read_str != None:
        #data=read_str

    #获取图像
    img = sensor.snapshot()
    sensor.set_hmirror(1)
    sensor.set_vflip(1)
    img.draw_rectangle([0,0,60,240],thickness=2)

    #物块识别
    if data == 10:  # 红色物块识别
        print('r');
        r_pix = img.find_blobs([red_thr], pixels_threshold=200, area_threshold=1000,roi=(60,0,260,240))#提取所有红色像素
        if r_pix:
            r_pix = max(r_pix, key=lambda b: b.pixels())     #选出最大色块
            x_offset = r_pix.cx() - img.width() // 2             #获取物块中心点与摄像头中心点坐标偏差值
            y_offset = r_pix.cy() - img.height() // 2
            img.draw_rectangle(r_pix.rect())                     #在图像上框住色块
            print("red block (", x_offset, ",", y_offset, ")")      #在缓存区展示偏差值（用于调试）
            sending_signal(1,y_offset,x_offset);                   #通过串口发送数据给STM32
            img.draw_string(200,2, ("%2d" %data), color=(128,0,0), scale=3)     #在屏幕上展示要识别色块序号
        else:
            sending_signal(0,0,0);
            print("No Detected")

    if data == 11:  # 绿色物块识别
        print('g');
        g_pix = img.find_blobs([green_thr], pixels_threshold=200, area_threshold=1000,roi=(60,0,260,240))
        if g_pix:
            g_pix = max(g_pix, key=lambda b: b.pixels())
            x_offset = g_pix.cx() - img.width() // 2
            y_offset = g_pix.cy() - img.height() // 2
            img.draw_rectangle(g_pix.rect())
            print("green block (",x_offset, ",", y_offset, ")")
            sending_signal(1,x_offset,y_offset);
            img.draw_string(200,2, ("%2d" %data), color=(128,0,0), scale=3)
        else:
            sending_signal(0,0,0);
            print("No detected")

    if data == 12: # 蓝色物块识别
        print('b');
        b_pix = img.find_blobs([(0, 39, 13, 63, -70, 0)], pixels_threshold=200, area_threshold=1000,roi=(60,0,260,240))
        if b_pix:
            b_pix = max(b_pix, key=lambda b: b.pixels())
            x_offset = b_pix.cx() - img.width() // 2
            y_offset = b_pix.cy() - img.height() // 2
            img.draw_rectangle(b_pix.rect())
            print("blue block (", x_offset, ",", y_offset, ")")
            sending_signal(1,x_offset,y_offset);
            img.draw_string(200,2, ("%2d" %data), color=(128,0,0), scale=3)
        else:
            sending_signal(0,0,0);
            print("No Detected")

    #圆环识别
    if data == 13:  # 识别红色圆环
        print('r-R');
        img.binary([(0, 76, 7, 63, 42, -11)])           #将图像根据阈值进行二值化处理
        img.dilate(2);                                  #将图像进行膨胀 使得色环糊成整体
        r_pix = img.find_blobs([gray_thr],area_threshold=150,pixels_threshold=3000,merge=True,roi=(60,0,260,240))  #寻找二值化后的色环
                                                                #roi=(60,0,260,240) 规定目标识别区域，避免车轮以及车身阴影的影响
        img.draw_rectangle([0,0,60,240],thickness=2)            #框线画出不识别区域
        if r_pix:
            r_pix = max(r_pix, key=lambda b: b.pixels())
            x_offset = r_pix.cx() - img.width() // 2
            y_offset = r_pix.cy() - img.height() // 2
            img.draw_rectangle(r_pix.rect())
            print("red H (", x_offset, ",", y_offset, ")")
            sending_signal(1,x_offset,y_offset);
        else:
            sending_signal(0,0,0);#未识别到
            print("No Detected")

    if data == 14:  # 绿色圆环识别
        print('g-R');
        img.binary([(0,80,-70,-10,-0,30)])
        img.dilate(2);
        g_pix = img.find_blobs([gray_thr],area_threshold=150,pixels_threshold=3000,merge=True,roi=(60,0,260,240))
        img.draw_rectangle([0,0,60,240],thickness=2)
        if g_pix:
            g_pix = max(g_pix, key=lambda b: b.pixels())
            x_offset = g_pix.cx() - img.width() // 2
            y_offset = g_pix.cy() - img.height() // 2
            img.draw_rectangle(g_pix.rect())
            print("green H (",x_offset, ",", y_offset, ")")
            sending_signal(1,x_offset,y_offset);
        else:
            sending_signal(0,0,0);
            print("No Detected")

    if data == 15: # 蓝色圆环识别
        print('b-R');
        img.binary([(0, 76, -2, 30, -6, -73)])
        img.dilate(2);
        b_pix = img.find_blobs([gray_thr],area_threshold=150,pixels_threshold=3000,merge=True,roi=(60,0,260,240))
        img.draw_rectangle([0,0,60,240],thickness=2)
        if b_pix:
            b_pix = max(b_pix, key=lambda b: b.pixels())
            x_offset = b_pix.cx() - img.width() // 2
            y_offset = b_pix.cy() - img.height() // 2
            img.draw_rectangle(b_pix.rect())
            print("blue H`1 (", x_offset, ",", y_offset, ")")
            sending_signal(1,x_offset,y_offset);
        else:
            sending_signal(0,0,0);
            print("No Detected")
    lcd.display(img)

