# -*- coding: UTF-8 -*-
import networkx as nx
import random 
import os
import copy

def constructG(smallG, timeWindows):
    # 生成出入口
    passageway = random.sample(smallG.nodes, 5)
    smallG.graph['entrance'] = passageway[0:3]
    smallG.graph['export'] = passageway[3:5]
    # 生成点的属性
    for node in smallG.nodes.data():
        # profit; service; time window
        node[1]['Profit'] = random.randint(100, 1000)
        node[1]['ServiceTime'] = random.randint(1, 10)
        tws = [{} for _ in range(4)]
        for tw in timeWindows:
            if tw.get('day', False) == False:
                continue;
            window = {}
            window['day'] = tw['day']
            opentime = tw['opentime']
            closetime = tw['closetime']
            # 以一定的概率改变时间窗口
            dice = random.randint(1, 5)
            if  dice > 3:
                # 改变closetime
                if dice == 4:
                    closetime = random.randint(opentime, closetime)
                else: 
                # 改变opentime    
                    opentime = random.randint(opentime, closetime)
                    
            window['opentime'] = opentime
            window['closetime'] = closetime
            tws[tw['day']] = copy.copy(window)
        node[1]['TimeWindows'] = tuple(tws[:])

    # 生成边的属性
    for edge in smallG.edges.data():
        # profit; walk time
        edge[2]['Profit'] = random.randint(50, 300)
        edge[2]['duration'] = random.randint(1, 10)  
    
    return;

def generateG(keyPointName):
    G = nx.Graph()
    categoryMap = {1:60, 2:40, 3:20, 4:10, 5:5}
    file = open(keyPointName)
    # 略过两行注释
    file.readline()
    file.readline()
    lists = file.readline().strip().split(';')
    # print(lists)
    G.graph['nb_nodes'] = int(lists[0])
    print(G.graph)

    # 略过两行注释
    file.readline()
    file.readline()
    # 统计Category=1的节点个数
    cat1 = 0
    for i in range(G.graph['nb_nodes']):
        lists = file.readline().strip().split(';')
        node = int(lists[0])
        G.add_node(node)
        G.nodes[node]['ID'] = node
        G.nodes[node]['ServiceTime'] = categoryMap[int(lists[1])]
        if int(lists[1]) == 1:
            cat1 += 1
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
    keyPointNum = int(G.graph['nb_nodes'] / 5)
    print(keyPointNum)
    print(cat1)

    cnt = min(cat1, keyPointNum)

    os.makedirs(file.name.split('.')[0])
    os.chdir(file.name.split('.')[0])
    for data in G.nodes.data():                               
        node = data[1]
        if cnt > 0 and node['ServiceTime'] == 60:   
            smallG = nx.generators.random_graphs.fast_gnp_random_graph(12, p=0.2, directed=False)
            while len(list(nx.connected_components(smallG))) > 1:
                smallG = nx.generators.random_graphs.fast_gnp_random_graph(12, p=0.2, directed=False)
            constructG(smallG, node['TimeWindows'])
            keyPointFile = open(str(node['ID']), 'wb')
            # nx.write_gexf(smallG, keyPointFile)
            nx.write_gml(smallG, keyPointFile)
            keyPointFile.close()
            cnt -= 1
    os.chdir('../')
    print(os.getcwd())
    keyPointFile.close()
    file.close()
    return;

def dfs(smallG, s, exportList, arriveTime, path, profitSum, edgeVisited, paramDict):
    path.append(s)
    neighborList = list(smallG.neighbors(s))
    # print(path)
    # print(neighborList)
    pathPath = []
    # print(str(s) + ' linjiedian ' + str(neighborList))
    for i in neighborList:
        pathPath.append(copy.copy(path))
    for index, neighbor in enumerate(neighborList):
        # 判断是否会超时
        neighborNode = smallG.nodes[neighbor]
        reachTime = arriveTime + smallG.edges[s, neighbor]['duration']
        # print(reachTime, neighborNode['ServiceTime'])
        if neighbor not in path and reachTime + neighborNode['ServiceTime'] > paramDict['maxDuration']:
            # print('maxDuration超时')
            continue;

        # 判断时间窗口是否满足
        timeWindows = neighborNode['TimeWindows']
        allowVisit = False
        window = timeWindows[paramDict['day']]
        if window == {}:
            continue;
        if window['closetime'] - reachTime > neighborNode['ServiceTime']:
            allowVisit = True
        if neighbor not in path and allowVisit == False:
            # print('tw超时')                                                                                                                                   
            continue;
        # 早到了
        waitTime = 0
        if neighbor not in path and reachTime < window['opentime']:
            waitTime = window['opentime'] - reachTime 

        # 判断从当前点到终点的最短路径是否会超时
        overTime = True
        for export in exportList:
            if reachTime + waitTime + neighborNode['ServiceTime'] + nx.dijkstra_path_length(smallG, neighbor, export, weight='duration') < paramDict['maxDuration']:
                overTime = False
        if overTime == True:
            # print('dijkstra超时')
            continue;
                                
        currentPath = pathPath[index]
        # print(currentPath)
        # print(neighbor, edgeVisited[s][neighbor])
        if neighbor in exportList:
            # print(neighbor)
            currentPath.append(neighbor)
            # print('ddd')
            # print(currentPath)
            if profitSum > paramDict['bestProfit']:
                paramDict['bestProfit'] = profitSum
                paramDict['bestPath'] = copy.copy(currentPath)
            currentPath.pop()
            continue;   
        if edgeVisited[s][neighbor] == False:   
            edgeVisited[s][neighbor] = True
            profitSum = profitSum + neighborNode['Profit']
            departureTime = reachTime + waitTime + neighborNode['ServiceTime']   
            dfs(smallG, neighbor, exportList, departureTime, currentPath, profitSum, edgeVisited, paramDict)
            profitSum = profitSum - neighborNode['Profit']
            edgeVisited[s][neighbor] = False
    path.pop()
            

def dfsTraverse(smallG, arriveTime, maxDuration, day):
    # arriveTime是从s点到达此地，经过wait后的时间，即进入入口的时间
    entranceList = list(map(int, smallG.graph['entrance']))
    exportList = list(map(int, smallG.graph['export']))
    path = []
    profitSum = 0
    paramDict = {}
    paramDict['maxDuration'] = maxDuration
    paramDict['bestProfit'] = 0
    paramDict['bestPath'] = []
    paramDict['day'] = day
    edgeVisited = [[False for _ in range(20)] for _ in range(20)]

    for entrance in entranceList:
        dfs(smallG, entrance, exportList, arriveTime, path, profitSum, edgeVisited, paramDict)
    print('bestProfit', paramDict['bestProfit'])
    print('bestPath', paramDict['bestPath'])

if __name__ == "__main__":
    # os.chdir('instances')
    # fileList = os.listdir('.')
    # for f in fileList:
    #     generateG(f)

    smallG = nx.read_gml('d:\PythonCode\TOPTW\instances\TPA_6_10-1\960')
    smallG = nx.convert_node_labels_to_integers(smallG)
    # print(smallG.nodes.data())
    # print(smallG.edges.data())
    dfsTraverse(smallG, 200, 270, 3)


