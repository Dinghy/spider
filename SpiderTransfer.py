# _*_ coding:utf-8 _*_
import codecs
from bs4 import BeautifulSoup
from store import *

# 读入文件
def ReadInFile(strFileName):
    # 返回数组
    arrList = []
    fileIn = codecs.open(strFileName,'r','utf8')
    strCon = ''.join([line.strip() for line in fileIn])
    fileIn.close()
    soup = BeautifulSoup(strCon)
    itemList = soup('item')
    for aitem in itemList:
        item = {}
        item['name'] = aitem('name')[0].get_text()
        item['category'] = ''
        item['place'] = aitem('place')[0].get_text()
        item['institute'] = aitem('institute')[0].get_text()
        item['admin'] = aitem('admin')[0].get_text()
        item['open'] = 1
        item['open2who'] = aitem('open')[0].get_text()
        item['orderway'] = aitem('orderway')[0].get_text()
        item['orderphone'] = aitem('orderphone')[0].get_text()
        item['orderemail'] = aitem('orderemail')[0].get_text()
        item['ordertime'] = ''
        item['des'] = aitem('des')[0].get_text()
        item['doc'] = ''
        item['img'] = ''
        item['deleted'] = 0
        item['orderwebsite'] = aitem('orderwebsite')[0].get_text()
        item['fee'] = aitem('fee')[0].get_text()
        item['author'] = 0
        arrList.append(item)
    return arrList

    
if __name__ == '__main__':
    # 文件存放地址 /home/dinghy/spider/save
    strFileName = r"/home/dinghy/spider/save/Data.txt"
    arrList = ReadInFile(strFileName)
    storeList(arrList)
