import networkx as nx
import os
import matplotlib.pyplot as plt
import copy

def dfs(G, s, t, path, edgeVisited):
    path.append(s)
    neighborList = list(G.neighbors(s))
      
    pathPath = []
    # print(str(s) + ' linjiedian ' + str(neighborList))
    for i in neighborList:
        pathPath.append(copy.copy(path))
    for index, neighbor in enumerate(neighborList):
        currentPath = pathPath[index]
        #print(currentPath)
        #print(neighbor, edgeVisited[s][neighbor])
        if neighbor == t:
            currentPath.append(t)
            print(currentPath)
            currentPath.pop()
            continue;   
        if edgeVisited[s][neighbor] == False:
            edgeVisited[s][neighbor] = True
            dfs(G, neighbor, t, currentPath, edgeVisited)
            edgeVisited[s][neighbor] = False
    path.pop()

def dfsTraverse(G, s, t):
    path = []
    ll = []
    edgeVisited = []
    edgeVisited = [[False for _ in range(20)] for _ in range(20)]

    dfs(G, s, t, path, edgeVisited)


G = nx.generators.random_graphs.fast_gnp_random_graph(10, p=0.2, directed=False)

while len(list(nx.connected_components(G))) > 1:
    G = nx.generators.random_graphs.fast_gnp_random_graph(10, p=0.2, directed=False)
# neighborList = list(G.neighbors(0))
# print(neighborList)

'''
G = nx.Graph()
G.add_edges_from([(0,6),(6,5),(5,8),(5,9)])
'''
dfsTraverse(G, 0, 9)
# print('finish')
nx.draw(G, with_labels=True)
plt.show()
'''
for i in G.nodes:
    print(list(G.neighbors(i)))
print(list(nx.connected_components(G)))
ll = []
for i in range(nx.number_of_nodes(G)):
    ll.append(False)
print(ll)
nx.draw(G, with_labels=True)
plt.show()
'''