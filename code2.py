# -*- coding: UTF-8 -*-
import networkx as nx
import random
import copy

# 3条最优路径

def createGraph(myGraph):
    categoryMap = {1:70, 2:40, 3:20, 4:10, 5:5}

    file = open('data.txt')
    # 略过两行注释
    file.readline()
    file.readline()
    lists = file.readline().strip().split(';')
    # print(lists)
    G.graph['nb_nodes'] = int(lists[0])
    G.graph['RouteMaxDuration'] = int(lists[1])
    G.graph['TotalMaxDuration'] = int(lists[2])
    print(G.graph)

    # 略过两行注释
    file.readline()
    file.readline()
    for i in range(G.graph['nb_nodes']):
        lists = file.readline().strip().split(';')
        node = int(lists[0])
        G.add_node(node)
        G.nodes[node]['ID'] = node
        G.nodes[node]['ServiceTime'] = categoryMap[int(lists[1])]
        G.nodes[node]['Priority'] = int(lists[2])
        G.nodes[node]['Profit'] = int(lists[3])
        G.nodes[node]['Probability'] = float(lists[4])
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

def optw(startP, destP, myGraph, existList, day):
    travelPath = [{'ID':startP}, {'ID':destP}]
    totalProfit = 0
    bestRatio = -1

    routeMaxDuration = myGraph.graph['RouteMaxDuration']
    # 就算s,t位置的slack值
    duration = myGraph.edges[startP, destP]['duration']
    destSlack = routeMaxDuration - duration
    startSlack = 0
    travelPath[0]['slack'] = startSlack
    travelPath[0]['aTime'] = 0
    travelPath[0]['dTime'] = 0
    travelPath[1]['slack'] = destSlack
    travelPath[1]['aTime'] = duration
    travelPath[1]['dTime'] = duration

    finish = False
    while finish == False:
        finish = True
        # top-k最优路径
        k = 5
        bestKPath = []
        bestKRatio = []
        bestKProfit = []
        bestKNodeId = []
        # 寻找一个合适点进行插入
        for data in myGraph.nodes.data():
            node = data[1]
            if node['ID'] in existList:
                continue
            # 找一个最匹配的slack插入到它前边
            bestMatch = -1
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
                # 增加的时间与slack之间的间隔，间隔值越小越好
                curGapTime = curComponent['slack'] - deltaTime
                if curGapTime < 0:
                    continue
                # 更新当前的间隔值
                if curGapTime < gapTime:
                    gapTime = curGapTime
                    bestMatch = index

            
            # 没有合适的插入点
            if bestMatch == -1:
                continue

            # 计算插入后的总收益与slack的比值
            tmpTotalProfit = totalProfit + node['Profit']
            tmpTravelPath = [copy.copy(x) for x in travelPath]
            timeParamDict = {
                            'arriveTimeToCandiNode':arriveTimeToCandiNode, 
                            'deparTimeOnCandiNode':deparTimeOnCandiNode, 
                            'arriveTimeToCurNode':arriveTimeToCurNode,
                            'day':day
                            }
            tmpTotalSlack, tmpTravelPath = calcuSlack2(myGraph, tmpTravelPath, node, bestMatch, timeParamDict)
            if tmpTotalSlack == 0:
                continue
            ratio = float(tmpTotalProfit) / float(tmpTotalSlack)

            # 检查当前点是否可以插入到bestKPath中  
            # 当前的ratio比存储的k条路径中的最差路径好
            if len(bestKRatio) < k:
                bestKPath.append([copy.copy(x) for x in tmpTravelPath])  
                bestKRatio.append(ratio)
                bestKProfit.append(tmpTotalProfit)
                bestKNodeId.append(node['ID'])
                # 代表还有比较好的点
                finish = False
            elif ratio > min(bestKRatio):
                index = bestKRatio.index(min(bestKRatio))
                del bestKPath[index]
                del bestKRatio[index] 
                del bestKNodeId[index]
                del bestKProfit[index]
                bestKPath.append([copy.copy(x) for x in tmpTravelPath])  
                bestKRatio.append(ratio)
                bestKProfit.append(tmpTotalProfit)
                bestKNodeId.append(node['ID'])
                # 代表还有比较好的点
                finish = False
            
        # 从k个候选者中随机挑出一个插入,
        # ！！！！！注意k个候选者没有选满的情况啊啊啊啊啊啊啊啊啊啊
        # 更新路径travelPath
        length = min(k, len(bestKPath))
        if length == 0:
            continue
        selectNode = random.randrange(0, length)
        travelPath = [copy.copy(x) for x in bestKPath[selectNode]]
        bestRatio = bestKRatio[selectNode]
        totalProfit = bestKProfit[selectNode]
        existList.append(bestKNodeId[selectNode])
    # print(travelPath)
    return travelPath;

def toptw(startDestList, myGraph):
    # 用来记录加入到路径中的点
    existList = []
    for val in startDestList:
        existList.append(val['s'])
        existList.append(val['t'])
    for day, val in enumerate(startDestList):
        print(optw(val['s'], val['t'], myGraph, existList, day+1))
        
    

G = nx.Graph()
createGraph(G)
startDestList = [{'s':960,'t':212}, {'s':84,'t':1259}, {'s':858,'t':1240}]
toptw(startDestList, G)
