# _*_ coding:utf-8 _*_
import codecs
import urllib2
import urllib
import urlparse
import operator
import re
import sys
import time
from bs4 import BeautifulSoup


# 获取指定url的页面内容
def GetContents(url,iTime):
    strCon = ""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11'}
    try:
        req = urllib2.Request(url,headers=headers)
        page = urllib2.urlopen(req,timeout=10)
        strCon = page.read()
    except Exception:
        # 尝试次数并未为0
        if iTime > 0:
            return GetContents(url,iTime-1)
        else:
            print "Failure"+'\t'+url
            strCon = "Failure"
            return strCon
    else:
        print "Success"+'\t'+url
        # print strCon
        return strCon

  
# 从目录页面下载所有仪器信息url
def GetItemList(strRoot,strUrl,strAppendix,urlPast):
    # 分析下一页href的正则
    patternNext = u"(下页|下一页|下一翻页)"
    patternMatchName = u"(仪器名称|中文名称|设备名称|名称)"
    patternMatchPlace = u"(所在单位|所属单位|依托单位|单位)"

    iNum = 1
    iDownloadLimit = 1
    arrUrlItem = {}
    # 拼接url及查询字段
    strParse = urlparse.urlparse(strUrl)
    # 判断是否已有查询字段
    if len(strAppendix) > 0:
        bQuery = False
        if len(strParse.query) > 0:
            bQuery = True
        if bQuery:
            strQuery = strParse.query+"&"+urllib.urlencode({strAppendix:str(iNum)})
        else:
            strQuery = urllib.urlencode({strAppendix:str(iNum)})
        strFullUrl = urlparse.urlunparse((strParse[0],strParse[1],strParse[2],strParse[3],strQuery,''))
    else:
        strFullUrl = strUrl
    strCon = GetContents(strFullUrl,3)
    # 判断是否为重复页面
    iItemInstru = 0
    iItemRepeat = 0
    bRepeat = False
    while iNum <= iDownloadLimit and (not bRepeat) and (not cmp(strCon,"Failure") == 0):
        soup = BeautifulSoup(strCon)    # bs
        # 解析是否为目录页
        soupTable = GetSoupTable(strUrl,soup)
        arrTr = soupTable('tr')
        if len(arrTr) > 1:
            # 生成默认仪器名称
            iName = -1
            iPlace = -1
            arrFirstTr = arrTr[0](re.compile("(th|td)"))
            for iTd in xrange(len(arrFirstTr)):
                if re.search(patternMatchName,arrFirstTr[iTd].get_text()) and iName == -1:
                    iName = iTd
                elif re.search(patternMatchPlace,arrFirstTr[iTd].get_text()) and iPlace == -1:
                    iPlace = iTd
            # 是否有超链接 
            iLenTd = len(arrTr[1](re.compile("(th|td)"))) # len(arrTr[0]('td'))
            for i in xrange(1,len(arrTr)):
                arrTempTd = arrTr[i](re.compile("(th|td)"))
                if len(arrTempTd) == iLenTd and iLenTd >= iName and iLenTd >= iPlace:
                    arrA = arrTr[i].findAll('a',href=re.compile('\S+'))
                    if len(arrA) > 0:
                        iItemInstru += 1
                        # 拼接url
                        strFullHrefUrl = UrlConnect(soup,strRoot,arrA[0]['href'])
                        if strFullHrefUrl not in urlPast:
                            arrUrlItem[strFullHrefUrl] = ["",""]
                            if iName >= 0:
                                arrUrlItem[strFullHrefUrl][0] = ''.join(re.findall("\S+",arrTempTd[iName].get_text()))
                            if iPlace >= 0:
                                arrUrlItem[strFullHrefUrl][1] = ''.join(re.findall("\S+",arrTempTd[iPlace].get_text()))
                            urlPast.append(strFullHrefUrl)
                            print arrA[0]['href']
                        else:
                            iItemRepeat += 1
        # 当出现有一页重复的时候退出循环
        if iItemInstru == iItemRepeat:
            bRepeat = True
        else:
            iItemRepeat = 0
            iItemInstru = 0
            # 判断是否有下一页的链接
            strUrl = ""
            for item in soup('a'):
                if re.search(patternNext,item.get_text()):
                    strUrl = item['href']
                    if not re.search("=",strUrl):
                        strUrl = ""
            # 增加标号，读取下一个页面
            if len(strUrl) > 0:
                iNum += 1
                strFullUrl = UrlConnect(soup,strRoot,strUrl)
                strCon = GetContents(strFullUrl,3)
            elif len(strAppendix) > 0:
                iNum += 1
                if bQuery:
                    if not re.search("&$",strParse.query):
                        strQuery = strParse.query+"&"+urllib.urlencode({strAppendix:str(iNum)})
                    else:
                        strQuery = strParse.query+urllib.urlencode({strAppendix:str(iNum)})
                else:
                    strQuery = urllib.urlencode({strAppendix:str(iNum)})
                strFullUrl = urlparse.urlunparse((strParse[0],strParse[1],strParse[2],strParse[3],strQuery,''))
                strCon = GetContents(strFullUrl,3)
            else:
                strCon = "Failure"
    return arrUrlItem
            
        
################################
## 这三个部分需要进一步分析聚类
# 获取index的soup
def GetSoupTable(strUrl,soup):
    # 匹配索引页的规则
    strMatchPattern = u"(是否|类别|序号|名称|型号|单位|操作|详情|比较|分类|查看|描述|目前状态|中文名|编号)"
    strDismissPattern = u"(查询|搜索|办法|方针|政策)"
    soupTable = []
    table = soup('table')
    if len(table) > 0:
        for item in table:
            # 格式上：如果有嵌套表格则无视，如果有input无视
            if len(item('table')) > 1 or len(item.findAll('input',type='text')) > 0:
                continue
            # 内容上: 找到标签数目,查找每一个tr
            arrTr = item('tr')
            if len(arrTr) > 1:
                strFullFirstTr = ''.join((re.findall("\S+",arrTr[0].get_text())))
                strFullSeconTr = ''.join((re.findall("\S+",arrTr[1].get_text())))
                arrTrFirst = arrTr[0](re.compile("(th|td)"))
                arrTrSecon = arrTr[1](re.compile("(th|td)"))
                iMatch = max(len(re.findall(strMatchPattern,strFullFirstTr)),len(re.findall(strMatchPattern,strFullSeconTr)))                 # 匹配列表
                iDismiss = len(re.findall(strDismissPattern,strFullFirstTr))             # 忽略列表
                if iMatch >= 3 and iDismiss == 0 and len(arrTr) > 3 and len(arrTrFirst) == len(arrTrSecon):
                    soupTable = item
    return soupTable


# 下载仪器信息
def GetItemDetail(arrUrlItem,strObmit):
    global strFileData
    #名称、机构、管理员、联系方式、网址、是否开放、收费标准的匹配规则
    dicCheckCha = {u"(?:仪器|中文|设备)名称":"Name",
                   u"(?:单位名称|所在单位|所属单位|依托单位)(?!内)":"Place",
                   u"(?:地址|所在城市|安放地点|所在省市)":"Addr",
                   u"(?:负责人|联系人|联络员)":"Contact",
                   u"(?:Tel|电话)":"Tel",
                   u"(?:mail|邮箱|邮件|信箱)(?!\.com)":"Email",
                   u"(?:使用方式|共享方式|共享状态|共享级别|开放形式)":"Open",
                   u"(?:收费标准|占用费\(元\))":"Cost"}
    # 电话及邮箱的正则表达式
    patternTel = u"[0-9\-\+×]{6,20}"
    patternMail = "\w+@\w+\.\w+"
    patternDivide = u"(?:：|\:)"
    # 输出文件
    fileOut = codecs.open(strFileData, "a", "utf-8")
    strOutput = ""

    for strUrlItem in arrUrlItem:
        # 存储字典
        dicItem = {}
        for itemCheck in dicCheckCha:
            dicItem[dicCheckCha[itemCheck]] = ""
        dicItem["Name"] = arrUrlItem[strUrlItem][0]
        dicItem["Place"] = arrUrlItem[strUrlItem][1]
        # 获取需要的soup
        strCon = GetContents(strUrlItem,3)
        if not cmp(strCon,"Failure") == 0:
            soup = BeautifulSoup(strCon)    # bs
            soupTable = soup('table')
            if len(soupTable) > 0:
                for itemTable in soupTable:
                    # 提取单个表格
                    arrTd = itemTable(re.compile('(th|td)'))
                    for iCount in xrange(0,len(arrTd)):
                        # 格式上：如果有超过一个的嵌套表格或者单个嵌套表格中元素过多则无视
                        if len(arrTd[iCount]('table')) > 1 or len(arrTd[iCount]('td')) > 2:
                            continue
                        # 提取当前Td的所有信息
                        strItemTd = ''.join((re.findall("\S+",arrTd[iCount].get_text())))
                        # 提取下一个Td的所有信息
                        if iCount+1 < len(arrTd):
                            # 格式上：如果有超过一个的嵌套表格或者单个嵌套表格中元素过多则无视
                            if len(arrTd[iCount+1]('table')) > 1 or len(arrTd[iCount+1]('td')) > 2:
                                continue
                            strItemTdNext = ''.join((re.findall("\S+",arrTd[iCount+1].get_text())))
                            # 内容上：筛选信息
                            for itemCheck in dicCheckCha:
                                if re.search(itemCheck,strItemTd):
                                    if re.search("\.\.\.",dicItem[dicCheckCha[itemCheck]]) or len(dicItem[dicCheckCha[itemCheck]]) == 0:
                                        dicItem[dicCheckCha[itemCheck]] = strItemTdNext
                                        break
                
        # 如果有名称信息
        if len(dicItem['Name']) > 0:
            # 电话及邮箱信息的正则表达式检测
            arrTel = re.findall(patternTel,dicItem["Tel"])
            arrMail = re.findall(patternMail,dicItem["Email"])
            if len(arrTel) > 0:
                dicItem["Tel"] = "\t".join(arrTel)
            else:
                dicItem["Tel"] = ""
            if len(arrMail) > 0:
                dicItem["Email"] = "\t".join(arrMail)
            else:
                dicItem["Tel"] = ""
            # 纯文本匹配筛选
            for itemCheck in dicCheckCha:
                # 是否为空，是否含有冒号
                if (len(dicItem[dicCheckCha[itemCheck]]) == 0 or re.search(patternDivide,dicItem[dicCheckCha[itemCheck]])) and not cmp(strCon,"Failure") == 0:
                    patternTemp = itemCheck+patternDivide+u"([^\s&]+)"
                    if len(strObmit) > 0:
                        strAllPoss = re.findall(u"([\s\S]+)(?<="+strObmit+")",soup.get_text())[0]
                    else:
                        strAllPoss = soup.get_text()
                    arrResult = re.findall(patternTemp,strAllPoss)
                    if len(arrResult) > 0 and not re.search(patternDivide,arrResult[0]):
                        dicItem[dicCheckCha[itemCheck]] = arrResult[0]
            # 加入输出字符串
            strOutputItem = 'url:'+strUrlItem+'\t'
            for itemCheck in dicCheckCha:    
                if dicCheckCha[itemCheck] not in dicItem:
                    strOutputItem += dicCheckCha[itemCheck]+":"+"NULL\t"
                else:
                    strOutputItem += dicCheckCha[itemCheck]+":"+dicItem[dicCheckCha[itemCheck]]+'\t'
            strOutput += strOutputItem+"\n"
            
    fileOut.write(strOutput)
    fileOut.close()
    
                           
# 检查是否需要继续爬取
def CheckUrlName(strName):
    # 匹配仪器页面的规则
    strMatch = u"(仪器|设备|电镜)"
    strDisMatch = u"(查询|搜索|办法|方针|政策|召开)"
    bCheck = False
    if re.search(strMatch,strName) and not re.search(strDisMatch,strName):
        bCheck = True
    return bCheck
    
################################


# url连接
def UrlConnect(soup,strRoot,strHref):
    strHref = re.sub("&amp;","&",strHref)
    # 判断是否指定base href
    if len(soup('base')) == 1:
        strFullHref = urlparse.urljoin(soup('base')[0]['href'],strHref)
    # 没有则直接拼接
    else:
        strFullHref = urlparse.urljoin(strRoot,strHref)
    return strFullHref


#################################
# 临时文件存档
def SaveTempFile(strSeedUrl,urlPast,urlInSite,urlOutSite):
    global strFileTempSave
    fileOut = codecs.open(strFileTempSave,'w','utf-8')
    fileOut.write(strSeedUrl+'\n')# 站点名称
    fileOut.write("Past\n")       # 标号
    for item in urlPast:
        fileOut.write(item+'\n')
    fileOut.write("Inlink\n")
    for item in urlInSite:
        fileOut.write(item+'\n')
    fileOut.write("Outlink\n")
    for item in urlOutSite:
        fileOut.write(item+'\t'+urlOutSite[item]+'\n')
    fileOut.close()

    
# 临时文件读档
def LoadTempFile(urlPast,urlInSite,urlOutSite):
    global strFileTempSave
    iTag = 0

    fileIn = codecs.open(strFileTempSave,'r','utf-8')
    strAllLine = [line.strip() for line in fileIn]
    for iLine in xrange(1,len(strAllLine)):
        # 判断定位符
        if cmp(strAllLine[iLine],"Past") == 0:
            iTag = 1
            continue
        elif cmp(strAllLine[iLine],"Inlink") == 0:
            iTag = 2
            continue
        elif cmp(strAllLine[iLine],"Outlink") == 0:
            iTag = 3
            continue
        # 进行存储
        if iTag == 1:
            urlPast.append(strAllLine[iLine])
        elif iTag == 2:
            urlInSite.append(strAllLine[iLine])
        elif iTag == 3:
            strSplit = re.split('\t',strAllLine[iLine])
            if len(strSplit) == 2:
                urlOutSite[strSplit[0]] = strSplit[1]
            elif len(strSplit) > 0:
                urlOutSite[strSplit[0]] = ''
    fileIn.close()
           
#################################


# 给定一个url地址，抓取所有站内url
# 返回站外链接url
def Crawler(strSeedUrl,strAppendix,strObmit):
    urlPast = []    # 该站点访问过的url
    urlInSite = []  # 该站点的url
    urlOutSite = {} # 链接出的url 
    global iTempSave
    global bTempLoad
    iInstrument = 0       # 爬取过的仪器页面

    # 判断是否需要读取临时文件，否则入栈
    if bTempLoad:
        LoadTempFile(urlPast,urlInSite,urlOutSite)
    else:
        urlInSite.append(strSeedUrl)

    # 主循环
    while len(urlInSite) > 0:
        iInstrumentOld = iInstrument
        # 每下载一个仪器目录页面后进行存储
        if iInstrument > iInstrumentOld:
            print "Temporary Saving..."
            SaveTempFile(strSeedUrl,urlPast,urlInSite,urlOutSite)
        # 获取当前根路径
        strUrl = urlInSite[0]
        arrRoot = re.findall("(^[\w\.\:/]+/)",strUrl)
        if len(arrRoot) > 0:
            strRoot = arrRoot[0]
        else:
            strRoot = strSeedUrl
        strCon = GetContents(strUrl,3)      # 获取源代码
        del urlInSite[0]
        if not cmp(strCon,"Failure") == 0:
            soup = BeautifulSoup(strCon)    # bs
            # 解析是否为目录页
            soupTable = GetSoupTable(strUrl,soup)
            if len(soupTable) > 0:
                print "Index Page:"+strUrl
                # 从目录页的仪器页面的下载
                arrUrlItem = GetItemList(strRoot,strUrl,strAppendix,urlPast)
                # 下载页面
                GetItemDetail(arrUrlItem,strObmit)
                iInstrument += 1
                # 忽略目录页上的内部链接（不忽略会引起重复，但对结果没有影响；忽略有一定问题）
                # continue
            # 如果没有目录或者仪器特征则解析其他的超链接
            for tag in soup.find_all('a'):  # 解析url网页上的href
                arrHref = re.findall(r'href="([\S]+)"',str(tag))
                # 是否有超链接
                if len(arrHref) > 0:        
                    strHref = arrHref[0]
                    # 是否是外部站点(链接是否有效)
                    if re.match(u"http://",strHref) and cmp(re.split("\.",strHref)[1],re.split("\.",strSeedUrl)[1]) != 0:
                        parseResult = urlparse.urlparse(strHref)
                        strOutSite = u"http://"+parseResult[1]+'/'
                        if strOutSite not in urlOutSite:
                            urlOutSite[strOutSite] = tag.get_text()
                    # 是否是内部站点
                    else:
                        # 判断该url前面是否是".."，即回到上级目录
                        strFullHref = UrlConnect(soup,strRoot,strHref)
                        strNameHref = tag.get_text()
                        # 检查是否重复，检查是否有仪器目录页信息可能
                        if strFullHref not in urlPast and CheckUrlName(strNameHref):     
                            urlPast.append(strFullHref)
                            urlInSite.append(strFullHref)
    return urlOutSite
                   
        

if __name__ == '__main__':
    # 数据存储及读取地址
    strFileData = r"save\Data.txt"
    strFileOutSite = r"save\Outlink.txt"
    strFileSeedInput = r"Seed.txt"
    strFileTempSave = r"save\SpiderTempSave.txt"
    iTempSave = 2
    bTempLoad = False
    strSeedNow = ""
    # 根据输入参数判断是否是需要进行临时文件加载
    if len(sys.argv) > 1:
        if cmp(sys.argv[1],'r') == 0:
            bTempLoad = True
            fileIn = open(strFileTempSave)
            strAllLine = [line.strip() for line in fileIn]
            strSeedNow = strAllLine[0]
            fileIn.close()
    # 读入种子
    biSeed = []
    fileIn = open(strFileSeedInput)
    for line in fileIn.readlines():
        line = line.strip()
        
        arrSplit = re.split('\t',line)
        # 根据读入行的大小
        if cmp(arrSplit[1],"null") == 0:
            arrSplit[1] = ""
        if cmp(arrSplit[2],"null") == 0:
            arrSplit[2] = ""
        else:
            arrSplit[2] = arrSplit[2].decode('gbk')
        if (arrSplit[0],arrSplit[1],arrSplit[2]) not in biSeed:
            biSeed.append((arrSplit[0],arrSplit[1],arrSplit[2]))
    fileIn.close()
    # 对目标排序
    # 测试网站
    print biSeed
    for iIter in xrange(len(biSeed)):
        strSeed = biSeed[iIter][0]
        strAppendix = biSeed[iIter][1]
        strObmit = biSeed[iIter][2]
        # 如果是要读取临时存档
        if bTempLoad:
            if not cmp(strSeed,strSeedNow) == 0:
                continue
        urlOutSite = Crawler(strSeed,strAppendix,strObmit)
        # 每爬取完一个网站后存储一次外链
        fileOut = codecs.open(strFileOutSite, "a", "utf-8")
        for item in urlOutSite:
            fileOut.write(item+'\t'+urlOutSite[item]+'\n')
        fileOut.close()
