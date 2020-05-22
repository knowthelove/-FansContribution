from django.shortcuts import render

# Create your views here.
from wordcloud import WordCloud, ImageColorGenerator
from PIL import Image
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import io
import base64
import random
from appran.models import get_crawl_detail,get_crawl_project_info


# 解决窗口关闭时的报错问题
matplotlib.use('Agg')

def show(request):
    # 柱状图数据
    data = get_crawl_detail()
    project = get_crawl_project_info()
    list_username = []
    list_money = []
    mydict = {}
    dictproject = {}
    dictproject['title'] = str(project.title)
    dictproject['current'] = str(project.current)
    for i in data:
        if i.amount >= 300:
            mydict[i.nickname] = int(i.amount)
    a = sorted(mydict.items(), key=lambda x: x[1], reverse=True)
    for i in a:
        list_username.append(i[0])
        list_money.append(i[1])

    # scatter数据
    all = []
    for i in data:
        id = random.randint(1, 40)
        list1 = []
        list1.append(id)
        list1.append(i.amount)
        list1.append(i.nickname)
        all.append(list1)

    # 获取用户昵称与金额坐权重
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

    return render(request, 'ranran.html',
                  {'list_username': list_username, 'list_money': list_money, 'dictproject': dictproject, 'all': all,
                   'ciyunimage': image})

