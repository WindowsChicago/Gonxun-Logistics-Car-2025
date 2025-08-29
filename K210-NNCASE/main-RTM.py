import sensor, image, lcd, time
import KPU as kpu
from machine import UART
import gc, sys
from fpioa_manager import fm
from board import board_info

fm.register(24, fm.fpioa.UART1_TX, force=True)    #TX映射到24引脚
fm.register(25, fm.fpioa.UART1_RX, force=True)    #RX映射到25引脚

#串口初始化
uart_A = UART(UART.UART1, baudrate=115200, bits=8, parity=None, stop=1, timeout=1000, read_buf_len=4096)

input_size = (224, 224)
labels = ['green', 'blue_r', 'green_r', 'red_r', 'blue', 'red']
anchors = [2.81, 2.72, 3.84, 3.63, 3.31, 3.28, 1.41, 1.97, 2.56, 2.56]

#串口信息发送函数
def sending_data(a,x,y,b,c):
        AXYBC = bytearray([a,x,y,b,c])
        uart_A.write(AXYBC)

def lcd_show_except(e):
    import uio
    err_str = uio.StringIO()
    sys.print_exception(e, err_str)
    err_str = err_str.getvalue()
    img = image.Image(size=input_size)
    img.draw_string(0, 10, err_str, scale=1, color=(0xff,0x00,0x00))
    lcd.display(img)


def main(anchors, labels = None, model_addr="/sd/m.kmodel", sensor_window=input_size, lcd_rotation=0, sensor_hmirror=True, sensor_vflip=True):
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.skip_frames(time=2000)  # 跳过初始帧以稳定摄像头
    sensor.set_windowing(sensor_window)
    sensor.set_hmirror(sensor_hmirror)
    sensor.set_vflip(sensor_vflip)
    sensor.run(1)

    lcd.init(type=1)
    lcd.clear(lcd.WHITE)
    lcd.rotation(3)

    try:
        img = image.Image("startup.jpg")
        lcd.display(img)
    except Exception:
        img = image.Image(size=(320, 240))
        img.draw_string(90, 110, "loading model...", color=(255, 255, 255), scale=2)
        lcd.display(img)


    try:
        task = None
        task = kpu.load(model_addr)
        kpu.init_yolo2(task, 0.85, 0.2, 5, anchors) # threshold:[0,1], nms_value: [0, 1]
        mode = None # 初始化data为None或某个无效值

        while(True):
            t = time.ticks_ms()
            #从串口接收数据
            modes = uart_A.read(6) #6字节，每个字节为16进制数据，串口发送端示例：5A 11(5A为检验包是否正确的校验码，包尾部数据无所谓，也可以填有效数据)
            if modes is not None and len(modes) == 6 and modes[0] == 0x5A:
                mode = int(modes[1])  # 确保datas有足够的长度

            #modes = uart_A.read(6) #6字节，每个字节为16进制数据，串口发送端示例：5A 11(5A为检验包是否正确的校验码，包尾部数据无所谓，也可以填有效数据)
            #if modes!=None:           #去除干扰无用数组
            #    if modes[0]==0x5A:    #判断包头是否正确
            #       print(modes)
            #       mode=modes[1]
            #       mode= int(mode)

            img = sensor.snapshot()
            if mode is not None:
                # 自适应色块识别
                if mode == 21:  # 收到信号0x15
                    objects = kpu.run_yolo2(task, img)  # 识别物体
                    if objects:
                        r_detected = False
                        g_detected = False
                        b_detected = False

                        r_detected = False
                        for robj in objects:
                            rpos = robj.rect()
                            img.draw_rectangle(rpos)
                            img.draw_string(rpos[0], rpos[1], "%s : %.2f" % (labels[robj.classid()], robj.value()), scale=2,color=(255, 0, 0))  # 检测识别物体是否是所训练的模型
                            rx, ry, rw, rh = robj.rect() #识别色块
                            if labels[robj.classid()] == 'red':  #labels 是保存色块色环标签的列表，当识别到绿色色块时
                                rcx = rx + rw // 2  # 用识别物体矩形框中心点代替物体中心点
                                rcy = ry + rh // 2

                                rxoff = rcx-112
                                ryoff = rcy-112

                                print("red block (", rxoff, ",", ryoff, ")")
                                sending_data(1,rxoff,ryoff,0,0x6b);
                                img.draw_string(20, 2, ("%2d" % mode), color=(128, 0, 0), scale=3)
                                r_detected = True

                        g_detected = False
                        for gobj in objects:
                            gpos = gobj.rect()
                            img.draw_rectangle(gpos)
                            img.draw_string(gpos[0], gpos[1], "%s : %.2f" % (labels[gobj.classid()], gobj.value()), scale=2,color=(255, 0, 0))  # 检测识别物体是否是所训练的模型
                            gx, gy, gw, gh = gobj.rect() #识别色块
                            if labels[gobj.classid()] == 'green':  #labels 是保存色块色环标签的列表，当识别到绿色色块时
                                gcx = gx + gw // 2  # 用识别物体矩形框中心点代替物体中心点
                                gcy = gy + gh // 2

                                gxoff = gcx-112
                                gyoff = gcy-112

                                print("green block (", gxoff, ",", gyoff, ")")
                                sending_data(2,gxoff,gyoff,0,0x6b);
                                img.draw_string(20, 2, ("%2d" % mode), color=(0, 128, 0), scale=3)
                                g_detected = True

                        b_detected = False
                        for bobj in objects:
                            bpos = bobj.rect()
                            img.draw_rectangle(bpos)
                            img.draw_string(bpos[0], bpos[1], "%s : %.2f" % (labels[bobj.classid()], bobj.value()), scale=2,color=(255, 0, 0))  # 检测识别物体是否是所训练的模型
                            bx, by, bw, bh = bobj.rect() #识别色块
                            if labels[bobj.classid()] == 'blue':  #labels 是保存色块色环标签的列表，当识别到绿色色块时
                                bcx = bx + bw // 2  # 用识别物体矩形框中心点代替物体中心点
                                bcy = by + bh // 2

                                bxoff = bcx-112
                                byoff = bcy-112

                                print("green block (", bxoff, ",", byoff, ")")
                                sending_data(3,bxoff,byoff,0,0x6b);
                                img.draw_string(20, 2, ("%2d" % mode), color=(0, 0, 128), scale=3)
                                b_detected = True

                        if not r_detected and not g_detected and not b_detected:
                            print("No detected")
                    else:
                        print("No Detected")

                # 色环识别
                if mode == 33:# 收到信号0x21，识别红色色环
                    objects = kpu.run_yolo2(task, img)  # 识别物体
                    if objects:
                        for obj in objects:
                            pos = obj.rect()
                            img.draw_rectangle(pos)
                            img.draw_string(pos[0], pos[1], "%s : %.2f" % (labels[obj.classid()], obj.value()), scale=2,color=(255, 0, 0))  # 检测识别物体是否是所训练的模型
                            x, y, width, height = obj.rect()
                            cx = x + width // 2  # 用识别物体矩形框中心点代替物体中心点
                            cy = y + height // 2
                            x_offset = cx - 112
                            y_offset = cy - 112
                            if labels[obj.classid()] == 'red_r':  #labels 是保存色块色环标签的列表，当识别到绿色色块时
                                sending_data(1,x_offset,y_offset,0,0x5a)
                                img.draw_string(20, 2, ("%2d" % mode), color=(128, 0, 0), scale=3)
                    else:
                        sending_data(0,0,0,0,0x5a)
                        print("No Rings Detected")

                if mode == 34:  # 收到信号0x22，识别绿色色环
                    objects = kpu.run_yolo2(task, img)  # 识别物体
                    if objects:
                        for obj in objects:
                            pos = obj.rect()  # 获取对象边界框
                            print(pos)
                            img.draw_rectangle(pos)
                            img.draw_string(pos[0], pos[1], "%s : %.2f" % (labels[obj.classid()], obj.value()), scale=2,color=(255, 0, 0))
                            x, y, width, height = obj.rect()
                            cx = x + width // 2  # 用识别物体矩形框中心点代替物体中心点
                            cy = y + height // 2
                            x_offset = cx - 112
                            y_offset = cy - 112
                            if labels[obj.classid()] == 'green_r':  #labels 是保存色块色环标签的列表，当识别到绿色色块时
                                sending_data(2,x_offset,y_offset,0,0x5b)
                                img.draw_string(20, 2, ("%2d" % mode), color=(128, 0, 0), scale=3)
                    else:
                        sending_data(0,0,0,0,0x5b)  # 未识别到反馈
                        print("No Rings Detected")

                if mode == 35:  # 收到信号0x23，识别蓝色色环
                    objects = kpu.run_yolo2(task, img)  # 识别物体
                    if objects:
                        for obj in objects:
                            pos = obj.rect()
                            img.draw_rectangle(pos)
                            img.draw_string(pos[0], pos[1], "%s : %.2f" % (labels[obj.classid()], obj.value()), scale=2,color=(255, 0, 0))  # 检测识别物体是否是所训练的模型
                            x, y, width, height = obj.rect()
                            cx = x + width // 2  # 用识别物体矩形框中心点代替物体中心点
                            cy = y + height // 2
                            x_offset = cx - 154
                            y_offset = cy - 120

                            if labels[obj.classid()] == 'blue_r':  #labels 是保存色块色环标签的列表，当识别到绿色色块时
                                sending_data(3,x_offset,x_offset,0,0x5c)
                                img.draw_string(20, 2, ("%2d" % mode), color=(128, 0, 0), scale=3)
                    else:
                        sending_data(0,0,0,0,0x5c)
                        print("No Rings Detected")
                    # 显示图像
                lcd.display(img)

    except Exception as e:
        sys.print_exception(e)
        lcd_show_except(e)
    finally:
        if not task is None:
            kpu.deinit(task)

if __name__ == "__main__":
    try:
        main(anchors = anchors, labels=labels, model_addr="/sd/model-164102.kmodel")
    except Exception as e:
        sys.print_exception(e)
        lcd_show_except(e)
    finally:
        gc.collect()
