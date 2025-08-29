#按键相机模式，按一下K230的key按键即拍一张照片，程序开始运行时会读取照片目录的文件，追加保存新照片而不会覆盖老照片

import time, os, sys
from media.sensor import * #导入sensor模块，使用摄像头相关接口
from media.display import * #导入display模块，使用display相关接口
from media.media import * #导入media模块，使用meida相关接口
from machine import Pin
from machine import FPIOA
import time

#将GPIO52、GPIO21配置为普通GPIO模式
fpioa = FPIOA()
fpioa.set_function(52,FPIOA.GPIO52)
fpioa.set_function(21,FPIOA.GPIO21)
DETECT_WIDTH = 640
DETECT_HEIGHT = 480
LED=Pin(52,Pin.OUT) #构建LED对象,开始熄灭
KEY=Pin(21,Pin.IN,Pin.PULL_UP) #构建KEY对象

state=0 #LED引脚状态
count = 0
try:
    
    sensor = Sensor(width = DETECT_WIDTH, height = DETECT_HEIGHT)
    sensor.reset()
    sensor.set_framesize(width = DETECT_WIDTH, height = DETECT_HEIGHT)
    sensor.set_pixformat(Sensor.RGB565)


# use lcd as display output
    Display.init(Display.ST7701, to_ide = True)

# use IDE as output
    Display.init(Display.VIRT, width = DETECT_WIDTH, height = DETECT_HEIGHT, fps = 100)


    MediaManager.init() #初始化media资源管理器

    sensor.run() #启动sensor

    clock = time.clock()
    # 检查SD卡是否挂载
    if 'sdcard' in os.listdir('/'):
        # 列出SD卡中图片目录下的所有文件
        image_files = [f for f in os.listdir('/sdcard/pic') if f.endswith('.jpg')]
        # 计算图片文件数量
        count = len(image_files)
        print("Number of images:", count)
    else:
        print("SD card not mounted")

    while True:


        os.exitpoint() #检测IDE中断
        clock.tick()

        img = sensor.snapshot() #拍摄一张图

        if KEY.value()==0:   #按键被按下
            time.sleep_ms(10) #消除抖动
            if KEY.value()==0: #确认按键被按下

                state=not state  #使用not语句而非~语句
                img.save("/sdcard/pic/img{}.jpg".format(count))  # 保存图片到SD卡
                print('OUYE~')
                count+=1

                while not KEY.value(): #检测按键是否松开
                    pass

        Display.show_image(img) #显示图片

        #time.sleep(0.1)
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
