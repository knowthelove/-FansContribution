import requests
import zlib
import json
import base64
import time
from appran.myStructure import Project, Record
from apscheduler.scheduler import Scheduler

# Create your models here.
post_data_template = '{{"ismore":{3},"limit":15,"id":"{0}","offset":{2},"requestTime":{1},"pf":"h5"}}'

founder_list = []
project_info = None

sched = Scheduler()

def get_crawl_detail(pro_id: int):
    # 缓存订单数据，避免每次请求show页面都触发爬虫
    # if len(time_to_found) == 0 or list(time_to_found.keys())[0] - time.time() > 5 * 60 * 100:
    #     found_list = GetPurchaseList(pro_id)
    #     time_to_found.clear()
    #     time_to_found[time.time()] = found_list
    # return list(time_to_found.values())[0]
    return founder_list


def get_crawl_project_info(pro_id: int):
    # if len(time_to_prd_info) == 0 or list(time_to_prd_info.keys())[0] - time.time() > 5 * 60 * 100:
    #     prd_info = GetDetail(pro_id)
    #     time_to_prd_info.clear()
    #     time_to_prd_info[time.time()] = prd_info
    # return list(time_to_prd_info.values())[0]
    return project_info


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

    global project_info
    project_info = Project(int(Response['datas']['id']),
                   Response['datas']['title'],
                   int(Response['datas']['start']),
                   int(Response['datas']['expire']),
                   float(Response['datas']['donation']),
                   int(Response['datas']['sellstats'])
                   )


def GetPurchaseList(pro_id: int):
    # 获得所有人购买的数据，以list形式返回
    data = post_data_template.format(pro_id, int(time.time() * 1000), 0)
    response = SendRequest('https://www.tao-ba.club/idols/join', data)

    global founder_list  # 接口返回的数据
    cleared = False  # 是否爬完的bool标志

    pages = 0
    while not cleared:
        for thisRecord in response['list']:
            founder_list.append(Record(pro_id,
                                       int(thisRecord['userid']),
                                       thisRecord['nick'],
                                       float(thisRecord['money']),
                                       ))
        if 0 < len(response['list']) <= 15:
            pages += 1
            data = post_data_template.format(pro_id, int(time.time() * 1000), pages * 15, True)
            response = SendRequest('https://www.tao-ba.club/idols/join', data)
        else:
            cleared = True
    #return founder_list


@sched.interval_schedule(seconds=60 * 5)
def scheduler_crawl():
    GetPurchaseList(3271)
    GetDetail(3271)