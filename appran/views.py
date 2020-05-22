from django.shortcuts import render

# Create your views here.
import requests
import zlib
import json
import base64
import time
from appran.myStructure import  Project,Record
from wordcloud import WordCloud, ImageColorGenerator
from PIL import Image
import numpy as np
import  matplotlib
import matplotlib.pyplot as plt
import jieba.analyse
import matplotlib.colors as colors
import random
import io
import base64
#解决窗口关闭时的报错问题
matplotlib.use('Agg')

def AddSalt(ori: bytearray):
    # 从网页JS当中提取到的混淆盐值，每隔一位做一次异或运算
    Salt = '%#54$^%&SDF^A*52#@7'
    i = 0
    for ch in ori:
        if i % 2 == 0:
            ch = ch ^ ord(Salt[(i // 2) % len(Salt)])
        ori[i] = ch
        i += 1
    return ori


def EncodeData(ori: str):
    # 开头的数字是原始报文长度
    Length = len(ori)
    Message = str.encode(ori)
    # 首先用zlib进行压缩
    Compressed = bytearray(zlib.compress(Message))
    # 然后加盐混淆
    Salted = AddSalt(Compressed)
    # 最后将结果转化为base64编码
    Result = base64.b64encode(Salted).decode('utf-8')
    # 将长度头和base64编码的报文组合起来
    return str(Length) + '$' + Result


def DecodeData(ori: str):
    # 分离报文长度头
    # TODO: 增加报文头长度的验证
    Source = ori.split('$')[1]
    # base64解码
    B64back = bytearray(base64.b64decode(Source))
    # 重新进行加盐计算，恢复原始结果
    Decompressed = AddSalt(B64back)
    # zlib解压
    Result = zlib.decompress(Decompressed).decode('utf-8')
    # 提取json
    return json.loads(Result)


def SendRequest(url: str, data: str):
    Headers = {
        'Content-Type': 'application/json',
        'Origin': 'https://www.tao-ba.club',
        'Cookie': 'l10n=zh-cn',
        'Accept-Language': 'zh-cn',
        'Host': 'www.tao-ba.club',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/605.1.15',
        'Referer': 'https://www.tao-ba.club/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    Data = EncodeData(data)
    Res = requests.post(url=url, data=Data, headers=Headers)
    ResText = Res.text
    return DecodeData(ResText)


def GetDetail(pro_id: int):
    # 获得项目基本信息
    Data = '{{"id":"{0}","requestTime":{1},"pf":"h5"}}'.format(pro_id, int(time.time() * 1000))
    Response = SendRequest('https://www.tao-ba.club/idols/detail', Data)
    return Project(int(Response['datas']['id']),
                   Response['datas']['title'],
                   int(Response['datas']['start']),
                   int(Response['datas']['expire']),
                   float(Response['datas']['donation']),
                   int(Response['datas']['sellstats'])
                   )


def GetPurchaseList(pro_id: int):
    # 获得所有人购买的数据，以list形式返回
    Data = '{{"ismore":false,"limit":15,"id":"{0}","offset":0,"requestTime":{1},"pf":"h5"}}'.format(pro_id, int(
        time.time() * 1000))
    Response = SendRequest('https://www.tao-ba.club/idols/join', Data)
    Founderlist = []
    Cleared = False
    pages = 0
    while not Cleared:
        for thisRecord in Response['list']:
            Founderlist.append(Record(pro_id,
                                      int(thisRecord['userid']),
                                      thisRecord['nick'],
                                      float(thisRecord['money']),
                                      ))
        if len(Response['list']) == 15:
            pages += 1
            Data = '{{"ismore":true,"limit":15,"id":"{0}","offset":{2},"requestTime":{1},"pf":"h5"}}'.format(pro_id,
                                                                                                             int(
                                                                                                                 time.time() * 1000),
                                                                                                             pages * 15)
            Response = SendRequest('https://www.tao-ba.club/idols/join', Data)
        else:
            Cleared = True
    return Founderlist
import random
def ranranshow(request):
    #柱状图数据
    data = GetPurchaseList(3271)
    project = GetDetail(3271)
    list_username=[]
    list_money=[]
    mydict={}
    dictproject = {}
    dictproject['title'] = str(project.title)
    dictproject['current'] =str(project.current)
    for i in data:
        if i.amount>=300:
            mydict[i.nickname]=int(i.amount)
    a = sorted(mydict.items(), key=lambda x: x[1], reverse=True)
    for i in a:
        list_username.append(i[0])
        list_money.append(i[1])

    #scatter数据
    all = []
    for i in data:
        id = random.randint(1, 40)
        list1 = []
        list1.append(id)
        list1.append(i.amount)
        list1.append(i.nickname)
        all.append(list1)

   #获取用户昵称与金额坐权重
    freq = {}
    for i in all:
        freq[i[2]] = i[1]


    colormaps = colors.ListedColormap(['#0000FF', '#00FF00', '#FF4500', '#FF00FF'])
    # 生成对象
    font = r'C:\\Windows\\Fonts\\STFANGSO.ttf'
    mask = np.array(Image.open(r"static/imgs/出道.jpg"))
    wc = WordCloud(mask=mask,
                   colormap=colormaps,
                   mode='RGBA',
                   collocations=False,
                   font_path=font,
                   background_color=None,
                   max_font_size=1000,
                   width=400,
                   height=200).generate_from_frequencies(freq)
    fig = plt.figure(dpi=100)
    # 从图片中生成颜色
    image_colors = ImageColorGenerator(mask)
    # wc.recolor(color_func=image_colors)
    plt.rcParams['font.sans-serif'] = ['SimHei']
    # 显示词云
    plt.imshow(wc, interpolation='bilinear')
    plt.axis("off")
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    image = base64.encodebytes(buf.getvalue()).decode()

    return render(request,'ranran.html',{'list_username':list_username,'list_money':list_money,'dictproject':dictproject,'all':all,'ciyunimage':image})

