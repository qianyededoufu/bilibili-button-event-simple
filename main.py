from machine import TouchPad, Pin,SPI
import max7219,time
import machine,network
import urequests,ssd1306
from machine import Timer

#电容可用端口
#There are ten capacitive touch-enabled pins that 
#can be used on the ESP32: 0, 2, 4, 12, 13 14, 15, 27, 32, 33. 
#my broad is can be used: 2, 12, 13, 14, 15
#Trying to assign to any other pins will result in a ValueError


#输入用户自己的UID码
userId="27534330"
#连接wifi wifiSsid设置为自己家的WiFi名称
wifiSsid="Link To Mars"
#wifiPass设置为自己的wifi密码
wifiPass="12345678910"
#城市代码 默认为郑州市 城市代码为中国天气网内城市代码 请前往中国天气网查看
cityCode="101180101"
#设置数码管亮度亮度范围（0-15）默认为最大亮度15
bright=15
#定时刷新时间 默认为10s
timer_num=10
#WIFI连接失败后数码管会显示0000EEEE 务必wifi名称和密码填写正确
#ESP32无线模块不支持5G频段WIFI!!!5G路由器慎用
#请求返回值
backCode=200
#拼接URL
fansUrl="https://api.bilibili.com/x/relation/stat?vmid="+userId
weatherUrl="http://www.weather.com.cn/data/cityinfo/"+cityCode+".html"
#按键标志位数组
touchFlag=[1,0,0,0]
def connect(name,password):
    ssid = name
    password = password
    station = network.WLAN(network.STA_IF)
    #判断是否连接成功 成功后返回connectInfo 没有的话下一步
    if station.isconnected() == True:
      connectInfo="is online"
      return connectInfo
    #激活wifi
    station.active(True)
    #进行连接
    station.connect(ssid, password)
    #设置开始时间进行计时 单位ms
    start=time.ticks_ms()
    while station.isconnected() == False:
      #如果连接时间超过10s 跳出等待 返回connectInfo的值
      if time.ticks_diff(time.ticks_ms(),start)>=10000 :
          connectInfo="failed"
          return connectInfo
      pass
    connectInfo="successful"
    print(station.ifconfig())
    return connectInfo
#封装显示使用list列表进行传参 *textCon
def display_1306(*textCon):
    #日常定义
    i2c = machine.I2C(scl=machine.Pin(4), sda=machine.Pin(5))
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)
    #获取列表长度
    i=len(textCon)
    #计数用变量
    counter=0
    #.fill()内为0时清屏 大于0时填充屏幕
    oled.fill(0)
    #因为暂时看不懂python的for循环就用了while循环
    while counter<=(i-1):
        #根据类表内元素的个数生成相应的行
        oled.text(textCon[counter],0,counter*10)
        counter=counter+1
    oled.show()
    return
def connectWifi():
    #声明为全局变量
    global wifiSsid,wifiPass
    #连接wifi
    connectInfo=connect(wifiSsid,wifiPass)
    #显示wifi状态
    display_1306("wifi is connect",connectInfo)
    #若连接失败 向数码管写入0xEEEE
    if connectInfo=="failed" :
        display.write_hex(0xEEEE)
def fansNum():
    #声明为全局变量
    global fansUrl,backCode
    # 使用get方法 返回的值为对象 属于response类
    getInformation = urequests.get(fansUrl)
    # 获取getInformation的json类型
    informationDict = getInformation.json()
    # 打印information的类型为 dict(字典)类型
    print(type(informationDict))
    # 通过字典对象上的键来获取键所对应的值
    fansInfo = "You have " + str(informationDict["data"]["follower"])
    midInfo = "mid:" + str(informationDict["data"]["mid"])
    backCode=informationDict["code"]
    display_1306("ESP32 is online", "User api test", midInfo, "Now time", fansInfo, "fans On Bilibili")
    display.write_num(informationDict["data"]["follower"])
    print("adfakdmfkamdf")
def weatherUtilTemp():
    # 声明为全局变量
    global weatherUrl
    # 使用get方法 返回的值为对象 属于response类
    getWeatherInformation = urequests.get(weatherUrl)
    # 获取getInformation的json类型
    weatherInformationDict = getWeatherInformation.json()
    print(weatherInformationDict)
    #根据键值获取参数 最小温度
    minTemp=weatherInformationDict["weatherinfo"]["temp1"]
    minTemp_num=int(minTemp.split('℃',1)[0])
    #最大温度
    maxTemp = weatherInformationDict["weatherinfo"]["temp2"]
    maxTemp_num = int(maxTemp.split('℃', 1)[0])
    #天气信息
    weatherToday=weatherInformationDict["weatherinfo"]["weather"]
    #尝试打印
    display.write_num(minTemp_num*1000000+maxTemp_num)
    display_1306(str(minTemp_num),str(maxTemp_num))
    return
def weatherUtilInfo():
    # 声明为全局变量
    global weatherUrl
    # 使用get方法 返回的值为对象 属于response类
    getWeatherInformation = urequests.get(weatherUrl)
    # 获取getInformation的json类型
    weatherInformationDict = getWeatherInformation.json()
    #天气信息
    weatherToday=weatherInformationDict["weatherinfo"]["weather"]
    #尝试打印
    #提取字符当中的单个字符 '-'表示从后向前取字符
    weatherFlag=weatherToday[-1:]
    if weatherFlag=="晴":
        display.write_hex(0xAAAA)
    elif weatherFlag=="云":
        display.write_hex(0xBBBB)
    elif weatherFlag=="阴":
        display.write_hex(0xCCCC)
    elif weatherFlag=="雨":
        display.write_hex(0xDDDD)
    else:
        display.write_hex(0xFFFF)
    print(weatherFlag)
    return
def callbackFunInterrupt(timer):
    global touchFlag
    if touchFlag[0]==1:
        fansNum()
    elif touchFlag[1]==1:
        weatherUtilTemp()
    elif touchFlag[2]==1:
        weatherUtilInfo()
    elif touchFlag[3]==1:
        fansNum()
    else:
        pass
    print(touchFlag)
    return

#MAX7219软SPI实现
vspi = SPI(2, sck=Pin(16), mosi=Pin(26), miso=Pin(25), baudrate=10000000)
display = max7219.Max7219(vspi, Pin(25))
#连接WIFI
connectWifi()
#清空屏幕
display.clear()
# 设置亮度
display.brightness(bright)
#新建定时器
timer = Timer(0)
#启动定时器
timer.init(period=timer_num*1000, mode=machine.Timer.PERIODIC, callback=callbackFunInterrupt)
while True:
    touchOne = TouchPad(Pin(12))
    touchTwo = TouchPad(Pin(13))
    touchThr = TouchPad(Pin(14))
    touchFou = TouchPad(Pin(15))

    if touchOne.read() <= 300:
        time.sleep_ms(10)
        if touchOne.read() <= 300:
            touchFlag[0] = 1
            touchFlag[1] = 0
            touchFlag[2] = 0
            touchFlag[3] = 0
            display.write_hex(0xA005)
        else:
            touchFlag[0] = 0
    else:
        pass

    if touchTwo.read() <= 300:
        time.sleep_ms(10)
        if touchTwo.read() <= 300:
            touchFlag[0] = 0
            touchFlag[1] = 1
            touchFlag[2] = 0
            touchFlag[3] = 0
            display.write_hex(0xB005)
        else:
            touchFlag[1] = 0
    else:
        pass

    if touchThr.read() <= 300:
        time.sleep_ms(10)
        if touchThr.read() <= 300:
            touchFlag[0] = 0
            touchFlag[1] = 0
            touchFlag[2] = 1
            touchFlag[3] = 0
            display.write_hex(0xC005)
        else:
            touchFlag[2] = 0
    else:
        pass

    if touchFou.read() <= 300:
        time.sleep_ms(10)
        if touchFou.read() <= 300:
            touchFlag[0] = 0
            touchFlag[1] = 0
            touchFlag[2] = 0
            touchFlag[3] = 1
            display.write_hex(0xD005)
        else:
            touchFlag[3] = 0
    else:
        pass