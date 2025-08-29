import sensor,image,lcd  # 导入相关库
from board import board_info  # 导入开发板信息
import os
from Maix import FPIOA,GPIO   # 导入FPIOA和GPIO库
from fpioa_manager import fm  # 导入fpioa_manager库
import time
import utime

# 按键配置
fm.register(board_info.BOOT_KEY, fm.fpioa.GPIOHS0)  # 注册按键GPIO
key_gpio = GPIO(GPIO.GPIOHS0, GPIO.IN)  # 初始化按键GPIO为输入
start_processing = False  # 按键按下标志

BOUNCE_PROTECTION = 50  # 按键抖动保护时间（毫秒）
# 按键中断服务程序
def set_key_state(*_):
    global start_processing  #告诉函数start_processing是全局变量
    start_processing = True  # 设置按键按下标志为True
    utime.sleep_ms(BOUNCE_PROTECTION)# 等待以消除按键抖动

key_gpio.irq(set_key_state, GPIO.IRQ_RISING, GPIO.WAKEUP_NOT_SUPPORT)# 设置按键中断
clock = time.clock()  # 初始化系统时钟，计算帧率
lcd.init() # 初始化lcd
sensor.reset() #初始化sensor 摄像头
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_hmirror(1) #设置摄像头镜像Q
sensor.set_vflip(1)   #设置摄像头翻转
lcd.rotation()
sensor.run(1) #使能摄像头
count = 0
# 检查SD卡是否挂载
if 'sd' in os.listdir('/'):
    # 列出SD卡中图片目录下的所有文件
    image_files = [f for f in os.listdir('/sd/pic') if f.endswith('.jpg')]
    # 计算图片文件数量
    count = len(image_files)
    print("Number of images:", count)
else:
    print("SD card not mounted")
while(1): # 主循环
    img = sensor.snapshot()#从摄像头获取一张图片
    clock.tick() #记录时刻，用于计算帧率
    #img.draw_string(0, 200, "%d" %(count), scale=1, color=(255, 0, 0))
    #识别到按键按下
    img.save("/sd/pic/img{}.jpg".format(count))  # 保存图片到SD卡
    count+=1
    time.sleep(0.9)
    a = lcd.display(img) #刷屏显示
