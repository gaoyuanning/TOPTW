# -*- coding: UTF-8 -*-
import networkx as nx
import random
import copy
import os
import math
import BigPoint
import time

# 3条最优路径,且同时产生
# 在slack允许的情况下找等待时间最长的点进行插入
# 对待插入的点，随机选择一天插入
# 对每一条数据进行测试
# 加入shake过程
# 将内部点合并到外部形成一个大图

def createGraph(myGraph, fileName, ll):
    categoryMap = {1:70, 2:40, 3:20, 4:10, 5:5}

    file = open(fileName)
    # 略过两行注释
    file.readline()
    file.readline()
    lists = file.readline().strip().split(';')
    # print(lists)
    G.graph['nb_nodes'] = int(lists[0])
    G.graph['RouteMaxDuration'] = int(lists[1])
    G.graph['TotalMaxDuration'] = int(lists[2])
    print(G.graph)

    maxNodeId = -1

    # 略过两行注释
    file.readline()
    file.readline()
    for i in range(G.graph['nb_nodes']):
        lists = file.readline().strip().split(';')
        node = int(lists[0])
        maxNodeId = max(maxNodeId, node)
        G.add_node(node)
        G.nodes[node]['ID'] = node
        G.nodes[node]['ServiceTime'] = categoryMap[int(lists[1])]
        G.nodes[node]['Priority'] = int(lists[2])
        G.nodes[node]['Profit'] = int(lists[3])
        G.nodes[node]['Probability'] = float(lists[4])
        if int(lists[1] == 1):
            if tmpP <= 0:
                tmpP = 5000
            if tmpP < 1000:
                tmpP = tmpP * 10
            G.nodes[node]['Profit'] = tmpP
        TWS = lists[5].split(',')
        # for TW in TWS:
        timeWindows = [{} for _ in range(4)]
        for TW in TWS:
            window = {}
            params = TW.split(':')
            window['day'] = int(params[0])
            window['opentime'] = int(params[1].split('-')[0])
            window['closetime'] = int(params[1].split('-')[1])
            index = int(params[0])
            if timeWindows[index].get('day', False) == False:
                timeWindows[index] = window
            else:
                timeWindows[index]['closetime'] = window['opentime']
        for index, TW in enumerate(timeWindows):
            if TW == {}:
                opentime = random.randrange(0, 600)
                closetime = random.randrange(0, 600)
                if opentime > closetime:
                    opentime, closetime = closetime, opentime
                while closetime - opentime < 200:
                    opentime = random.randrange(0, 600)
                    closetime = random.randrange(0, 600)
                    if opentime > closetime:
                        opentime, closetime = closetime, opentime
                TW['day'] = index
                TW['opentime'] = opentime
                TW['closetime'] = closetime
        G.nodes[node]['TimeWindows'] = tuple(timeWindows[:])
    # print(G.nodes.data())    
    
    # 略过两行注释
    file.readline()
    file.readline()
    arcs = file.readlines()
    for line in arcs:
        lists = line.strip().split(';')
        s = int(lists[0]); t = int(lists[1]); duration = int(lists[2])
        G.add_edge(s, t)
        G.edges[s, t]['duration'] = duration
    # print(G.edges.data())
    file.close()

    # 将BigPoint合并到大图中
    mergeGraph(G, f.split('.')[0], maxNodeId + 1)

def mergeGraph(myGraph, bigPointDir, startNodeId):
    bigPointPaths = os.listdir(bigPointDir)
    innerToOutDictList = []
    for index, fileName in enumerate(bigPointPaths):
        originNodeId = int(fileName)
        smallG = nx.read_gml(bigPointDir + '\\' + fileName)
        smallG = nx.convert_node_labels_to_integers(smallG)
        innerToOutDict = {}
        for node in smallG.nodes.data():
            innerToOutDict[node[0]] = startNodeId
            innerToOutDictList.append(startNodeId)
            myGraph.add_node(startNodeId)
            myGraph.nodes[startNodeId]['ID'] = startNodeId
            myGraph.nodes[startNodeId]['Profit'] = node[1]['Profit']
            myGraph.nodes[startNodeId]['ServiceTime'] = node[1]['ServiceTime']
            myGraph.nodes[startNodeId]['TimeWindows'] = node[1]['TimeWindows'] 
            startNodeId = startNodeId + 1          

        for edge in smallG.edges.data():
            p1 = innerToOutDict[edge[0]]
            p2 = innerToOutDict[edge[1]]
            myGraph.add_edge(p1, p2)
            myGraph.edges[p1, p2]['duration'] = edge[2]['duration']
            myGraph.add_edge(p2, p1)
            myGraph.edges[p2, p1]['duration'] = edge[2]['duration']

        for node0 in smallG.nodes.data():
            for node1 in smallG.nodes.data():
                n0 = innerToOutDict[node0[0]]; n1 = innerToOutDict[node1[0]] 
                if  n0 == n1:
                    myGraph.add_edge(n0, n0)
                    myGraph.edges[n0, n0]['duration'] = 0
                elif (n0, n1) not in myGraph.edges():
                    myGraph.add_edge(n0, n1)
                    myGraph.edges[n0, n1]['duration'] = 1000000
                    myGraph.add_edge(n1, n0)
                    myGraph.edges[n1, n0]['duration'] = 1000000
                elif (n1, n0) not in myGraph.edges():
                    myGraph.add_edge(n1, n0)
                    myGraph.edges[n1, n0]['duration'] = 1000000
                    myGraph.add_edge(n0, n1)
                    myGraph.edges[n0, n1]['duration'] = 1000000
                     

        # print(innerToOutDict.values())
        for innerNode in smallG.nodes.data():
            for node in myGraph.nodes.data():
                if (node[0], originNodeId) not in myGraph.edges:
                    duration = random.randrange(10, 40)
                else:
                    duration = myGraph.edges[node[0], originNodeId]['duration']
                myGraph.add_edge(node[0], innerToOutDict[innerNode[0]])
                myGraph.edges[node[0], innerToOutDict[innerNode[0]]]['duration'] = max(0, random.randrange(duration - 5, duration + 5))  
                myGraph.add_edge(innerToOutDict[innerNode[0]], node[0])
                myGraph.edges[innerToOutDict[innerNode[0]], node[0]]['duration'] = max(0, random.randrange(duration - 5, duration + 5))  

    for fileName in bigPointPaths:
        originNodeId = int(fileName)
        myGraph.remove_node(originNodeId) 

    return  

def isCompleteGraph(G):
    nodeNum = len(G.nodes)
    edgeNum = len(G.edges)
    print(nodeNum * (nodeNum - 1) / 2)
    print(edgeNum)

def calcuSlack(myGraph, travelPath, node, insertLocation, timeParamDict):
    # 插入到insertLocation之前
    travelPath.insert(insertLocation, {'ID':node['ID']})
    travelPath[insertLocation]['aTime'] = timeParamDict['arriveTimeToCandiNode']
    travelPath[insertLocation]['dTime'] = timeParamDict['deparTimeOnCandiNode']
    travelPath[insertLocation]['closetime'] = node['TimeWindows'][timeParamDict['day']]['closetime']
    preComponentID = node['ID']
    nextComponentID = -1

    # 对插入点之后的点进行时间更新
    for index, pathComponent in enumerate(travelPath[insertLocation+1:]):
        # !!!注意index的值!!!
        index = index + insertLocation + 1

        nextComponentID = pathComponent['ID']
        duration = myGraph.edges[preComponentID, nextComponentID]['duration']
        arriveToNextComponent = travelPath[index-1]['dTime'] + duration
        window = myGraph.nodes[nextComponentID]['TimeWindows'][timeParamDict['day']]
        deparTimeOnNextComponent = max(arriveToNextComponent, window['opentime']) + myGraph.nodes[nextComponentID]['ServiceTime']
        travelPath[index]['aTime'] = arriveToNextComponent
        travelPath[index]['dTime'] = deparTimeOnNextComponent
        travelPath[index]['closetime'] = window['closetime']
        preComponentID = nextComponentID

    # 计算终点的slack值
    tmpSlack = travelPath[-1]['slack'] = myGraph.graph['RouteMaxDuration'] - travelPath[-1]['aTime']
    totalSlack = tmpSlack
    # 全体slack更新
    travelPath[0]['closetime'] = 10000000
    for pathComponent in travelPath[-2::-1]:
        pathComponent['slack'] = min(pathComponent['closetime']-pathComponent['dTime'], tmpSlack)        
        tmpSlack = pathComponent['slack']
        totalSlack = totalSlack + tmpSlack

    return totalSlack, travelPath

# 从头重新计算各自的时间
def calcuSlack2(myGraph, travelPath, node, insertLocation, timeParamDict):
    # 插入到insertLocation之前
    travelPath.insert(insertLocation, {'ID':node['ID']})
    # travelPath[insertLocation]['aTime'] = timeParamDict['arriveTimeToCandiNode']
    # travelPath[insertLocation]['dTime'] = timeParamDict['deparTimeOnCandiNode']
    # travelPath[insertLocation]['closetime'] = node['TimeWindows'][timeParamDict['day']]['closetime']
    preComponentID = travelPath[0]['ID']
    nextComponentID = -1



    # 对插入点之后的点进行时间更新
    for index, pathComponent in enumerate(travelPath[1:]):
        # !!!注意index的值!!!
        index = index + 1

        nextComponentID = pathComponent['ID']
        duration = myGraph.edges[preComponentID, nextComponentID]['duration']
        # if index == 1:
        #     print(travelPath[index-1]['dTime'], duration)
        arriveToNextComponent = travelPath[index-1]['dTime'] + duration
        window = myGraph.nodes[nextComponentID]['TimeWindows'][timeParamDict['day']]
        deparTimeOnNextComponent = max(arriveToNextComponent, window['opentime']) + myGraph.nodes[nextComponentID]['ServiceTime']
        travelPath[index]['aTime'] = arriveToNextComponent
        travelPath[index]['dTime'] = deparTimeOnNextComponent
        travelPath[index]['closetime'] = window['closetime']
        travelPath[index]['waitTime'] = window['opentime'] - arriveToNextComponent
        if travelPath[index]['waitTime'] < 0:
            travelPath[index]['waitTime'] = 0
        preComponentID = nextComponentID

    # 计算终点的slack值
    tmpSlack = travelPath[-1]['slack'] = myGraph.graph['RouteMaxDuration'] - travelPath[-1]['aTime']
    totalSlack = tmpSlack
    # 全体slack更新
    travelPath[0]['closetime'] = 10000000
    for pathComponent in travelPath[-2::-1]:
        # print(pathComponent)
        pathComponent['slack'] = min(pathComponent['closetime'] - pathComponent['dTime'], tmpSlack)        
        tmpSlack = pathComponent['slack']
        totalSlack = totalSlack + tmpSlack

    return totalSlack, travelPath

def toptw(startDestList, myGraph):
    # 用来记录加入到路径中的点
    existList = []
    routeMaxDuration = myGraph.graph['RouteMaxDuration']
    threeDayPath = []
    threeDayProfitList = [0, 0, 0]
    threeDayBestRatioList = [-1, -1, -1]
    for i, val in enumerate(startDestList):
        s = val['s']
        t = val['t']
        existList.append(s)
        existList.append(t)
        tP = [{'ID':s}, {'ID':t}]
        duration = myGraph.edges[s, t]['duration']
        startSlack = 0
        destSlack = routeMaxDuration - duration
        tP[0]['slack'] = startSlack
        tP[0]['aTime'] = 0
        tP[0]['dTime'] = 0
        tP[0]['waitTime'] = 0
        tP[1]['slack'] = destSlack
        tP[1]['aTime'] = duration
        tP[1]['dTime'] = duration
        # 终点的等待时间，如何确定呢
        tP[1]['waitTime'] = myGraph.nodes[t]['TimeWindows'][i+1]['opentime'] - duration
        if tP[1]['waitTime'] < 0:
            tP[1]['waitTime'] = 40
        threeDayPath.append(tP)


    finish = False
    while finish == False:
        finish = True
        # top-k最优路径
        # k = 5
        # bestKPath = []
        # bestKRatio = []
        # bestKProfit = []
        # bestKNodeId = []
        # 寻找一个合适点进行插入
        for data in myGraph.nodes.data():
            node = data[1]
            if node['ID'] in existList:
                continue
            
            threeDayRatioList = [-1, -1, -1]
            threeDayTmpPathList = [[] for i in range(3)]
            threeDayTmpProfitList = [x for x in threeDayProfitList]

            # 遍历三条路径，选择一条最适合的插入这个点
            for day, travelPath in enumerate(threeDayPath):
                day = day + 1
                # 找一个最匹配的slack插入到它前边
                bestMatch = -1
                tmpWaitTime = -1
                gapTime = 10000000
                for index, _ in enumerate(travelPath[1:]):
                    # index值是阶段后的列表中的索引值
                    index = index + 1
                    preComponent = travelPath[index-1]
                    preToCandiNodeDuration = myGraph.edges[preComponent['ID'], node['ID']]['duration']
                    arriveTimeToCandiNode = preComponent['dTime'] + preToCandiNodeDuration
                    if (arriveTimeToCandiNode > routeMaxDuration 
                    or max(arriveTimeToCandiNode, node['TimeWindows'][day]['opentime']) + node['ServiceTime'] > routeMaxDuration 
                    or node['TimeWindows'][day]['closetime'] - arriveTimeToCandiNode < node['ServiceTime']):
                        break
                    
                    deparTimeOnCandiNode = max(arriveTimeToCandiNode, node['TimeWindows'][day]['opentime']) + node['ServiceTime']
                    curComponent = travelPath[index]
                    candiNodeToCurNodeDuration = myGraph.edges[node['ID'], curComponent['ID']]['duration']
                    arriveTimeToCurNode = deparTimeOnCandiNode + candiNodeToCurNodeDuration
                    # 由于插入这个点增加的时间
                    # t1为加入的点带来的时间duraion，t2为原先的pre到cur的duration
                    t1 = arriveTimeToCurNode - preComponent['dTime']
                    t2 = curComponent['aTime'] - preComponent['dTime']
                    deltaTime = t1 - t2
                    # 在slack允许的情况下找等待时间最长的点进行插入
                    curGapTime = curComponent['slack'] - deltaTime
                    if curGapTime < 0:
                        continue
                    if travelPath[index]['waitTime'] > tmpWaitTime:
                        bestMatch = index
                        tmpWaitTime = travelPath[index]['waitTime']

                    # # 更新当前的间隔值
                    # if curGapTime < gapTime:
                    #     gapTime = curGapTime
                    #     bestMatch = index

                
                # 没有合适的插入点
                if bestMatch == -1:
                    continue

                # 计算插入后的总收益与slack的比值
                tmpTotalProfit = threeDayProfitList[day-1] + node['Profit']
                tmpTravelPath = [copy.copy(x) for x in travelPath]
                timeParamDict = {
                                'arriveTimeToCandiNode':arriveTimeToCandiNode, 
                                'deparTimeOnCandiNode':deparTimeOnCandiNode, 
                                'arriveTimeToCurNode':arriveTimeToCurNode,
                                'day':day
                                }
                tmpTotalSlack, tmpTravelPath = calcuSlack2(myGraph, tmpTravelPath, node, bestMatch, timeParamDict)
                if float(tmpTotalSlack) == 0:
                    continue
                ratio = float(tmpTotalProfit) / float(tmpTotalSlack)
                threeDayRatioList[day-1] = ratio
                threeDayTmpPathList[day-1] = [copy.copy(x) for x in tmpTravelPath]
                threeDayTmpProfitList[day-1] = tmpTotalProfit

            # 随机选择一天进行插入
            accept = False
            
            dieTime = 0
            while accept == False:
                randomDay = random.randrange(0, 3)
                if threeDayRatioList[randomDay] > threeDayBestRatioList[randomDay]:
                    threeDayBestRatioList[randomDay] = threeDayRatioList[randomDay]
                    threeDayPath[randomDay] = [copy.copy(x) for x in threeDayTmpPathList[randomDay]]
                    threeDayProfitList[randomDay] = threeDayTmpProfitList[randomDay]
                    accept = True
                dieTime = dieTime + 1
                if dieTime > 15:
                    break

            # 取threeDayRatioList中最大值的那条路就是要插入的路径
            # accept = False
            # for i in range(3):
            #     if accept == False:
            #         bestRatio = max(threeDayRatioList)
            #         whichDay = threeDayRatioList.index(bestRatio)
            #         if bestRatio > threeDayBestRatioList[whichDay]:
            #             threeDayBestRatioList[whichDay] = bestRatio
            #             threeDayPath[whichDay] = [copy.copy(x) for x in threeDayTmpPathList[whichDay]]
            #             threeDayProfitList[whichDay] = threeDayTmpProfitList[whichDay]
            #             accept = True
            #         threeDayRatioList[whichDay] = -5

            if accept == True:
                existList.append(node['ID'])
                finish = False


    shake(myGraph, threeDayPath, threeDayBestRatioList, threeDayProfitList, existList)
    for day, path in enumerate(threeDayPath):
        print(path)
    profitSum = sum(threeDayProfitList)
    print('total profit:', profitSum)
    # bigPointPaths = os.listdir(bigPointDir)
    # for day, path in enumerate(threeDayPath):
    #     print(path)
    #     for component in path:
    #         if str(component['ID']) in bigPointPaths:
    #             smallG = nx.read_gml(bigPointDir + '\\' + str(component['ID']))
    #             smallG = nx.convert_node_labels_to_integers(smallG)
    #             BigPoint.dfsTraverse(smallG, component['aTime'] + component['waitTime'], component['dTime'], day+1) 
    #     print()
    
    return

def checkAndCalcu(myGraph, travelPath, day):
    # 检测一条路径是否合法
    preComponentID = travelPath[0]['ID']
    nextComponentID = -1
    for index, pathComponent in enumerate(travelPath[1:]):
        # !!!注意index的值!!!
        index = index + 1

        nextComponentID = pathComponent['ID']
        duration = myGraph.edges[preComponentID, nextComponentID]['duration']
        arriveToNextComponent = travelPath[index-1]['dTime'] + duration
        window = myGraph.nodes[nextComponentID]['TimeWindows'][day]
        deparTimeOnNextComponent = max(arriveToNextComponent, window['opentime']) + myGraph.nodes[nextComponentID]['ServiceTime']
        if (arriveToNextComponent > myGraph.graph['RouteMaxDuration'] 
        or deparTimeOnNextComponent > myGraph.graph['RouteMaxDuration']):
            return -1

        travelPath[index]['aTime'] = arriveToNextComponent
        travelPath[index]['dTime'] = deparTimeOnNextComponent
        travelPath[index]['closetime'] = window['closetime']
        travelPath[index]['waitTime'] = window['opentime'] - arriveToNextComponent
        if travelPath[index]['waitTime'] < 0:
            travelPath[index]['waitTime'] = 0
        preComponentID = nextComponentID

    # 计算终点的slack值
    tmpSlack = travelPath[-1]['slack'] = myGraph.graph['RouteMaxDuration'] - travelPath[-1]['aTime']
    totalSlack = tmpSlack
    # 全体slack更新
    travelPath[0]['closetime'] = 10000000
    for pathComponent in travelPath[-2::-1]:
        # print(pathComponent)
        pathComponent['slack'] = min(pathComponent['closetime'] - pathComponent['dTime'], tmpSlack)        
        tmpSlack = pathComponent['slack']
        totalSlack = totalSlack + tmpSlack

    # 返回值为totalSlack
    return totalSlack  

def singlePathShake(myGraph, threeDayPath, threeDayBestRatioList, threeDayProfitList):
    # 任意选择两个点，转置子路径
    iterNum = 30
    for day, path in enumerate(threeDayPath):
        bestRatio = threeDayBestRatioList[day]
        totalProfit = threeDayProfitList[day]
        day = day + 1
        # 初始温度
        T = 3000    
        # 温度衰减率
        DELTA = 0.85
        # 终止温度
        EPS = 1e-8
        while iterNum > 0:
            pathLen = len(path)
            if pathLen < 4:
                break
            # p1 < p2
            p1 = random.randrange(1, pathLen-1)
            p2 = random.randrange(1, pathLen-1)
            # while p2 == p1:
            #     p2 = random.randrange(1, pathLen-1)
            if p1 > p2:
                p1, p2 = p2, p1
            # 构造临时新路径
            tmpPath = []
            for p in path[0:p1]:
                tmpPath.append(copy.copy(p))
            for p in path[p2:p1-1:-1]:
                tmpPath.append(copy.copy(p))
            for p in path[p2+1:]:
                tmpPath.append(copy.copy(p))

            totalSlack = checkAndCalcu(myGraph, tmpPath, day)
            if totalSlack <= 0:
                continue
            ratio = float(totalProfit) / float(totalSlack)
            if ratio > bestRatio:
                bestRatio = ratio
                threeDayBestRatioList[day-1] = bestRatio
                path = tmpPath
            elif totalSlack > 0:
                # 模拟退火，以一定概率接收不是很好的解
                prob = math.exp(-(bestRatio-ratio) / T)
                p = random.random()
                if prob > p:
                    bestRatio = ratio
                    threeDayBestRatioList[day-1] = bestRatio
                    path = tmpPath    
            T = T * DELTA
            if T < EPS:
                break
            iterNum = iterNum - 1
    return


def replacePointShake(myGraph, threeDayPath, threeDayBestRatioList, threeDayProfitList, existList):
    # 选择图中没有被访问的点，进行替换    
    for day, path in enumerate(threeDayPath):
        bestRatio = threeDayBestRatioList[day]
        totalProfit = threeDayProfitList[day]
        day = day + 1
        # 初始温度
        T = 3000    
        # 温度衰减率
        DELTA = 0.85
        # 终止温度
        EPS = 1e-8
        for data in myGraph.nodes.data():
            iterNum = 0
            node = data[1]
            if node['ID'] in existList:
                continue
            pathLen = len(path)
            replacedNodeIndex = random.randrange(1, pathLen-1)
            tmpPath = [copy.copy(x) for x in path]
            tmpPath[replacedNodeIndex]['ID'] = node['ID']
            totalSlack = checkAndCalcu(myGraph, tmpPath, day)
            if totalSlack <= 0:
                continue
            ratio = float(totalProfit) / float(totalSlack)
            if ratio > bestRatio:
                existList.append(node['ID'])
                existList.remove(path[replacedNodeIndex]['ID'])
                bestRatio = ratio
                threeDayBestRatioList[day-1] = bestRatio
                path = tmpPath
            elif totalSlack > 0:
                # 模拟退火，以一定概率接收不是很好的解
                prob = math.exp(-(bestRatio-ratio) / T)
                p = random.random()
                if prob > p:
                    existList.append(node['ID'])
                    existList.remove(path[replacedNodeIndex]['ID'])
                    bestRatio = ratio
                    threeDayBestRatioList[day-1] = bestRatio
                    path = tmpPath   
            T = T * DELTA
            iterNum = iterNum + 1
            if T < EPS or iterNum > 30:
                break
    return

def swapBetweenPathShake(myGraph, threeDayPath, threeDayBestRatioList, threeDayProfitList):
    # 任意选择两个路径，进行子路交换
    # 路径较长的选取大子路，路劲短的选取小子路
    iterNum = 30
    # 初始温度
    T = 3000    
    # 温度衰减率
    DELTA = 0.85
    # 终止温度
    EPS = 1e-8
    while iterNum > 0:
        day1 = random.randrange(0, 3)
        day2 = random.randrange(0, 3)
        while day1 == day2:
            day2 = random.randrange(0, 3)
        bestRatio1 = threeDayBestRatioList[day1]
        totalProfit1 = threeDayProfitList[day1]
        bestRatio2 = threeDayBestRatioList[day2]
        totalProfit2 = threeDayProfitList[day2]
        path1 = threeDayPath[day1]
        path2 = threeDayPath[day2]

        pathLen1 = len(path1)
        pathLen2 = len(path2)

        if pathLen1 < 3 or pathLen2 < 3:
            continue

        p11 = random.randrange(1, pathLen1-1)
        p12 = random.randrange(1, pathLen1-1)
        # 可以出现单点情况
        if p11 > p12:
            p11, p12 = p12, p11

        p21 = random.randrange(1, pathLen2-1)
        p22 = random.randrange(1, pathLen2-1)
        if p21 > p22:
            p21, p22 = p22, p21 
        
        # 构造2条临时新路径
        tmpPath1 = []
        tmpPath2 = []
        for p in path1[0:p11]:
            tmpPath1.append(copy.copy(p))
        for p in path2[p21:p22+1]:
            tmpPath1.append(copy.copy(p))
        for p in path1[p12+1:]:
            tmpPath1.append(copy.copy(p))

        for p in path2[0:p21]:
            tmpPath2.append(copy.copy(p))
        for p in path1[p11:p12+1]:
            tmpPath2.append(copy.copy(p))
        for p in path2[p22+1:]:
            tmpPath2.append(copy.copy(p))

        totalSlack1 = checkAndCalcu(myGraph, tmpPath1, day1+1)
        totalSlack2 = checkAndCalcu(myGraph, tmpPath2, day2+1)
        if totalSlack1 <= 0 or totalSlack2 <= 0:
            continue
        ratio1 = float(totalProfit1) / float(totalSlack1)
        ratio2 = float(totalProfit2) / float(totalSlack2)

        if ratio1 > bestRatio1 and ratio2 > bestRatio2:
            bestRatio1 = ratio1
            path1 = tmpPath1
            bestRatio2 = ratio2
            path2 = tmpPath2
            threeDayBestRatioList[day1] = bestRatio1
            threeDayBestRatioList[day2] = bestRatio2

        else:
            # 模拟退火，以一定概率接收不是很好的解
            prob1 = math.exp(-(bestRatio1-ratio1) / T)
            prob2 = math.exp(-(bestRatio2-ratio2) / T)
            prob = max(prob1, prob2)
            p = random.random()
            if prob > p:
                bestRatio1 = ratio1
                path1 = tmpPath1
                bestRatio2 = ratio2
                path2 = tmpPath2
                threeDayBestRatioList[day1] = bestRatio1
                threeDayBestRatioList[day2] = bestRatio2

        T = T * DELTA
        if T < EPS:
            break
        iterNum = iterNum - 1
    return

def addPointShake(myGraph, threeDayPath, threeDayBestRatioList, threeDayProfitList, existList):
    # 选一个没有被访问的点，随机插入到路径中
    for day, path in enumerate(threeDayPath):
        bestRatio = threeDayBestRatioList[day]
        totalProfit = threeDayProfitList[day]
        day = day + 1
        # 初始温度
        T = 3000    
        # 温度衰减率   
        DELTA = 0.85
        # 终止温度
        EPS = 1e-8
        for data in myGraph.nodes.data():
            iterNum = 0
            node = data[1]
            if node['ID'] in existList:
                continue
            pathLen = len(path)
            insertNodeIndex = random.randrange(1, pathLen-1)
            tmpPath = [copy.copy(x) for x in path]
            tmpPath.insert(insertNodeIndex, {'ID':node['ID']})
            totalSlack = checkAndCalcu(myGraph, tmpPath, day)
            if totalSlack <= 0:
                continue
            ratio = float(totalProfit) / float(totalSlack)
            if ratio > bestRatio:
                existList.append(node['ID'])
                bestRatio = ratio
                threeDayBestRatioList[day-1] = bestRatio
                path = tmpPath
            elif totalSlack > 0:
                # 模拟退火，以一定概率接收不是很好的解
                prob = math.exp(-(bestRatio-ratio) / T)
                p = random.random()
                if prob > p:
                    existList.append(node['ID'])
                    bestRatio = ratio
                    threeDayBestRatioList[day-1] = bestRatio
                    path = tmpPath   
            T = T * DELTA
            iterNum = iterNum + 1
            if T < EPS or iterNum > 30:
                break
    return

def shake(myGraph, threeDayPath, threeDayBestRatioList, threeDayProfitList, existList):
    singlePathShake(myGraph, threeDayPath, threeDayBestRatioList, threeDayProfitList)
    replacePointShake(myGraph, threeDayPath, threeDayBestRatioList, threeDayProfitList, existList)
    swapBetweenPathShake(myGraph, threeDayPath, threeDayBestRatioList, threeDayProfitList)
    addPointShake(myGraph, threeDayPath, threeDayBestRatioList, threeDayProfitList, existList)


    #         # 检查当前点是否可以插入到bestKPath中       
    #         # 当前的ratio比存储的k条路径中的最差路径好
    #         if len(bestKRatio) < k:
    #             bestKPath.append([copy.copy(x) for x in tmpTravelPath])  
    #             bestKRatio.append(ratio)
    #             bestKProfit.append(tmpTotalProfit)
    #             bestKNodeId.append(node['ID'])
    #             # 代表还有比较好的点
    #             finish = False
    #         elif ratio > min(bestKRatio):
    #             index = bestKRatio.index(min(bestKRatio))
    #             del bestKPath[index]
    #             del bestKRatio[index] 
    #             del bestKNodeId[index]
    #             del bestKProfit[index]
    #             bestKPath.append([copy.copy(x) for x in tmpTravelPath])  
    #             bestKRatio.append(ratio)
    #             bestKProfit.append(tmpTotalProfit)
    #             bestKNodeId.append(node['ID'])
    #             # 代表还有比较好的点
    #             finish = False
            
    #     # 从k个候选者中随机挑出一个插入,
    #     # ！！！！！注意k个候选者没有选满的情况啊啊啊啊啊啊啊啊啊啊
    #     # 更新路径travelPath
    #     length = min(k, len(bestKPath))
    #     if length == 0:
    #         continue
    #     selectNode = random.randrange(0, length)
    #     travelPath = [copy.copy(x) for x in bestKPath[selectNode]]
    #     bestRatio = bestKRatio[selectNode]
    #     totalProfit = bestKProfit[selectNode]
    #     existList.append(bestKNodeId[selectNode])
    # # print(travelPath)
    # return travelPath;
# Define signal handler function

# os.chdir('instances')
# fileList = os.listdir('.')
# for f in fileList:
#     if os.path.isfile(f):
#         G = nx.Graph()
#         ll = []
#         createGraph(G, f, ll)
#         ll = random.sample(G.nodes, 6)
#         # print(G.nodes)
#         startDestList = [{'s':ll[0],'t':ll[1]}, {'s':ll[2],'t':ll[3]}, {'s':ll[4],'t':ll[5]}]
#         # print(startDestList)
#         toptw(startDestList, G)

# f = 'd:\PythonCode\TOPTW\instances\TPA_8_10-2.txt'
# f = 'd:\PythonCode\TOPTW\instances\TPA_8_20-2.txt'
# f = 'd:\PythonCode\TOPTW\instances\TPA_8_40-2.txt'
# f = 'd:\PythonCode\TOPTW\instances\TPA_8_80-2.txt'
f = 'd:\PythonCode\TOPTW\instances\TPA_8_140-2.txt'
G = nx.Graph()
ll = []
createGraph(G, f, ll)
ll = random.sample(G.nodes, 6)
# print(ll)
startDestList = [{'s':ll[0],'t':ll[1]}, {'s':ll[2],'t':ll[3]}, {'s':ll[4],'t':ll[5]}]
# print(startDestList)
t1 = time.time()
toptw(startDestList, G)
t2 = time.time()
print('time:', t2 - t1)