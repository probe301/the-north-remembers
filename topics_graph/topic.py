#  -*- coding:utf-8 -*-

# decode、替换重复节点、保证文件同步、减少文件操作、多线程加速

import gzip
import re
import http.cookiejar
import urllib.request
import urllib.parse
import time

def ungzip(data):
    try:        # 尝试解压
        # print('正在解压.....')
        data = gzip.decompress(data)
        # print('解压完毕!')
    except:
        pass
        # print('未经压缩, 无需解压')
    return data

def getXSRF(data):
    cer = re.compile('name=\"_xsrf\" value=\"(.*)\"', flags = 0)
    strlist = cer.findall(data)
    if strlist:
        return strlist[0]
    else:
        printLog("找不到_xsrf")
        exit()


def getOpener(head):
    # deal with the Cookies
    cj = http.cookiejar.CookieJar()
    pro = urllib.request.HTTPCookieProcessor(cj)
    opener = urllib.request.build_opener(pro)
    header = []
    for key, value in head.items():
        elem = (key, value)
        header.append(elem)
    opener.addheaders = header
    return opener


def judgeRepeat(urlChild, urlParent):
    urlParent = int(urlParent)
    if urlChild:
        urlChild = int(urlChild)
        for index in doubleMatrix:
            if index[0]==urlChild and index[1]==urlParent:
                return True
        doubleMatrix.append([urlChild, urlParent])
        return False
    else:
        listIndex = int(urlParent/31)
        posOffset = int(urlParent%31)
        if (singleMatrix[listIndex]>>posOffset)&1:
            return True
        else:
            singleMatrix[listIndex]|=(1<<posOffset)
            return False



def requestContent(opener, url, postData=""):
    if postData:
        try:
            openObject = opener.open(url, postData)
        except:
            printLog("POST请求出错")
            exit()

    else:
        try:
            openObject = opener.open(url)
        except:
            printLog("GET请求出错")
            exit()

    loadContent = openObject.read()
    loadContent = ungzip(loadContent)
    loadContent = loadContent.decode()

    return [loadContent, opener]

def dealDataBefore(data):
    return data[8:-9]


def jsonYN(data):
    try:
        if type(eval(data))==list:
            return True
        else:
            printLog("不是Json格式")
            return False
    except:
        printLog("不是Json格式")
        return False



def findRE(compileRE, source):
    findData = compileRE.findall(source)
    if findData:
        return findData[0]
    else:
        return False



def printLog(printContent):
    timeCurr = time.strftime('%y-%m-%d %H:%M:%S      ',time.localtime(time.time()))
    content = timeCurr+printContent
    dealAppendIO("log.txt", content+"\n")
    print(content)


def dealReadIO(fileName):
    try:
        file = open(fileName, "r")
        fileContent = file.read()
        file.close()
    except IOError:
        printLog("读取文件出错")
        exit()
    return fileContent

def dealWriteIO(fileName, writeContent):
    try:
        file = open(fileName, "w")
        file.write(writeContent)
        file.close()
    except IOError:
        printLog("写入文件出错")
        exit()

def dealAppendIO(fileName, writeContent):
    try:
        file = open(fileName, "a")
        file.write(writeContent)
        file.close()
    except IOError:
        printLog("追加文件出错")
        exit()







header = {
    'Connection': 'Keep-Alive',
    'Accept': 'text/html, application/xhtml+xml, */*',
    'Accept-Language': 'en-US,en;q=0.8,zh-Hans-CN;q=0.5,zh-Hans;q=0.3',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2334.0 Safari/537.36',
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'www.zhihu.com',
    'DNT': '1'
}

opener = getOpener(header)

url = 'http://www.zhihu.com/'
[pageContent, opener] = requestContent(opener, url)
_xsrf = getXSRF(pageContent)

id = re.compile('id:[ ]*(.*)')
password = re.compile('password:[ ]*(.*)')
config = dealReadIO('config')
postDict = {
        '_xsrf':_xsrf,
        'email': findRE(id, config),
        'password': findRE(password, config),
        'rememberme': 'y'
}
postData = urllib.parse.urlencode(postDict).encode()

url += 'login'
[temp, opener] = requestContent(opener, url, postData)



url="http://www.zhihu.com/topic/19776749/organize/entire"
[pageContent, opener] = requestContent(opener, url)
_xsrf = getXSRF(pageContent)



postDict = {
    '_xsrf':_xsrf
}
postData = urllib.parse.urlencode(postDict).encode()


singleMatrix = dealReadIO('judgeRepeatSingle.txt')
doubleMatrix = dealReadIO('judgeRepeatDouble.txt')
crawlResult = dealReadIO('crawlResult.json')


if crawlResult == "" or singleMatrix=="" or doubleMatrix=="":
    singleMatrix=[0]*int((100000000+30)/31)
    doubleMatrix=[]
    [crawlResult, opener] = requestContent(opener, url, postData)
    crawlResult = dealDataBefore(crawlResult)
    dealWriteIO('judgeRepeatSingle.txt','')
    dealWriteIO('judgeRepeatDouble.txt','')
    dealWriteIO('crawlResult.json','')
else:
    singleMatrix = eval(singleMatrix)
    doubleMatrix = eval(doubleMatrix)











getUrlNodeRE = re.compile('\[\["load"[^\]]*"([^"]*)", "(\d{8})"\], \[\]\]')
replaceSonRE = re.compile('\[\["topic"[^\]]*\], \[\[\["load", [^\]]*\], \[\]\]\]\]')
dealLoadMoreRE = re.compile('\[\["topic"[^\]]*\], \[(.*)\]\]$')
replaceLoadMoreRE = re.compile('\[\["load"[^\]]*\], \[\]\]')

urlNode = findRE(getUrlNodeRE, crawlResult)

while urlNode:
    urlChild = urlNode[0]
    urlParent = urlNode[1]

    if judgeRepeat(urlChild, urlParent):
        crawlResult = re.sub(replaceSonRE,"[]",crawlResult,1)
    else:
        time.sleep(0.2)
        printLog(str(urlNode))
        [loadContent, opener] = requestContent(opener, url+"?child=" + urlChild + "&parent=" + urlParent, postData)
        loadContent = dealDataBefore(loadContent)
        # print(loadContent)
        if urlChild:
            replaceLoadMore = findRE(dealLoadMoreRE, loadContent)
            print(replaceLoadMore)
            if replaceLoadMore:
                crawlResult = re.sub(replaceLoadMoreRE,replaceLoadMore,crawlResult,1)
            else:
                printLog("加载更多的处理是出错")
                exit()
        else:
            crawlResult = re.sub(replaceSonRE,loadContent,crawlResult,1)

    if jsonYN(crawlResult):
        dealWriteIO('judgeRepeatSingle.txt', str(singleMatrix))
        dealWriteIO('judgeRepeatDouble.txt', str(doubleMatrix))
        # print(crawlResult)
        dealWriteIO('crawlResult.json', crawlResult)
    else:
        dealWriteIO('bugInf.txt', '')
        dealAppendIO('bugInf.txt', loadContent+'\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n')
        dealAppendIO('bugInf.txt', crawlResult)
        break

    urlNode = findRE(getUrlNodeRE, crawlResult)
