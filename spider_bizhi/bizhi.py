#完整代码(大家有兴趣的可以尝试一下，可以把爬取时间改长一点) time.sleep方法改时间
import ctypes
import random
import re
import time
import requests
from bs4 import BeautifulSoup
import os
os.environ['NO_PROXY'] = 'stackoverflow.com'

def set_img_as_wallpaper(filepath):
    ctypes.windll.user32.SystemParametersInfoW(20,0,filepath,0)
    ctypes.windll.user32.SystemParametersInfoW()

#获取网址的最大值
def get_pictures_nums(url,headers,cookies):
    try:
        req = requests.get(url=url,headers=headers,cookies=cookies)
    except AttributeError:
        print("AttributeError is a problem!")
    except Exception as e:
        print("OtherError!")
    print(req.status_code)
    req.encoding = "gbk"
    html = req.text
    souplist = BeautifulSoup(html,features="lxml")
    conslist = souplist.find(class_="page")
    cons_listes = conslist.find_all("a")
    max_nums = cons_listes[-2]
    max_nums = str(max_nums)
    max_num = re.findall("<.*?>(.*?)</a>",max_nums,re.S)
    nums = int(max_num[0])
    return nums

#获取所有存放壁纸的网址
def get_pictures_html(url,nums):
    list_pics = [url]
    for i in range(2,nums+1):
        html_path = url + "index_" + str(i) + ".htm"
        list_pics.append(html_path)
    return list_pics

#爬取某一页网址的每张壁纸
def get_pictures(pictures,headers):
    nums = 1
    img_save_path = r"C:/bizhi/"
    img_name = re.findall('.*?alt="(.*?)".*?', pictures, re.S)  # 获取每张壁纸的名字
    img_one_name = img_name[0]
    img_path = re.findall('.*?src="(.*?)".*?', pictures, re.S)  # 获取每张壁纸的网址
    img_one_path = img_path[0]
    if img_one_name == "4k壁纸":
        pass
    else:
        if os.path.exists(img_save_path):
            high_img = img_one_path[:38] + img_one_path[43:-14] + img_one_path[-4:]
            response = requests.get(url=high_img, headers=headers)
            img_paths = img_save_path + "壁纸.jpg"
            with open(img_paths, "wb") as f:
                f.write(response.content)
            time.sleep(1)   #设置爬取时间的间隔
            print("爬取第" + str(nums) + "张壁纸成功!!!")
            nums += 1
        else:
            os.mkdir(img_save_path)
            high_img = img_one_path[:38] + img_one_path[43:-14] + img_one_path[-4:]
            response = requests.get(url=high_img, headers=headers)
            img_paths = img_save_path + "壁纸.jpg"
            with open(img_paths, "wb") as f:
                f.write(response.content)
            time.sleep(1)  #设置爬取时间的间隔
            print("爬取第" + str(nums) + "张壁纸成功!!!")
            nums += 1
    filepath =  img_save_path + "壁纸.jpg"
    set_img_as_wallpaper(filepath)

#获取所有壁纸的函数
def get_pictures_all(list_htmls,headers):
    chance = random.choice(list_htmls)
    req = requests.get(chance, headers=headers)
    req.encoding = "gbk"
    html = req.text
    soup = BeautifulSoup(html, features="lxml")
    cons = soup.find(class_="list")
    cons_list = cons.find_all("img")
    list_img_path = []
    list_img_name = []
    for i in cons_list:
        i = str(i)
        img_name = re.findall('.*?alt="(.*?)".*?', i, re.S)  # 获取每张壁纸的名字
        img_one_name = img_name[0]
        img_path = re.findall('.*?src="(.*?)".*?', i, re.S)  # 获取每张壁纸的网址
        img_one_path = img_path[0]
        if img_name == "4k壁纸":
            pass
        else:
            list_img_name.append(img_one_name)
            list_img_path.append(img_one_path)
    counts = 0
    for img in list_img_path:
        if "newc" in img:
            counts += 1
        else:
            pass
    if counts > 5:
        pass
    else:
        picture = random.choice(cons_list)
        pictures = str(picture)
        get_pictures(pictures,headers)

#主函数
def main():
    url = "http://www.netbian.com/dongman/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-encoding":"gzip, deflate",
        "Accept-language":"zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-control":"max-age=0",
        "Connection":"keep-alive"
        }
    cookies = {
        "Cookie":"trenvecookieclassrecord=%2C19%2C; cf_clearance=bqtJUwdFcCiOTTDumKVK1ZkaHPmiK1xC8wErND38V1g-1739327100-1.2.1.1-CrJYPiIPvfqYeIpzuiazAFlqksI1rvFUrbOzlmY3GTSFNnV4dWkxwUMXd3wlcUuvK1do3p0.ev2i3MWjF6poIzVCcdACiHwKPkqO408vutIz5HlKqTyb8vlG6kQ9820hDgVqWgqQ4FMaVJRQEHBTyseqsnnky2.JC8CfzjWoYkkttwVh1qYxsZDgKeNk48Mv.W3lH_EvMBGQ7PZSxNBf8QSo.H0DOuXdBTkUJ21WWjLQQM77DC_pP1yz8A6jyXueE0XarYFrxsjh_NyKNHlfrp3Spv8lvhoIoOx8VCWaVjtQ5hQHnYM0lWY.viwC0pdWAZB1c2h0_kp0vQ7lW6fmzA"
    }
    nums = get_pictures_nums(url,headers,cookies)       #获取最大壁纸网站的值
    list_htmls = get_pictures_html(url,nums)    #获取所有壁纸网址的统一资源定位符url
    while(1):
        get_pictures_all(list_htmls,headers)        #获取某一网址的所有壁纸

if __name__ == "__main__":
    main()
