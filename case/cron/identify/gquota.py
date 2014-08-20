# -*- coding: utf-8 -*-
import networkx as nx
import time
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import math
from scipy import linalg
import numpy as np


from SSDB import SSDB 
from config import SSDB_HOST, SSDB_PORT

def _utf8_unicode(s):
    if isinstance(s, unicode):
        return s
    else:
        return unicode(s, 'utf-8')


def get_ave(dict_value):
    sumvalue = 0
    for nodes, value in dict_value.iteritems():
        sumvalue += value
    ave = float(sumvalue) / float(len(dict_value)) 
    return ave

def get_powerlaw(dhistogram, prekey):
    l = len(dhistogram)
    print 'l:', l
    pre_x = []
    pre_y = []
    for i in range(l):
        if dhistogram[i] != 0:
            pre_x.append(i+1)
            pre_y.append(dhistogram[i])
        else:
            continue
    x = pre_x
    p_y = pre_y
    y =[]
    allcount = sum(dhistogram)
    for count in p_y:
        fre = float(count) / float(allcount)
        y.append(fre)
    lnx = [math.log(f, math.e) for f in x]
    lny = [math.log(f, math.e) for f in y]
    a = np.mat([lnx, [1]*len(x)]).T
    b = np.mat(lny).T

    (t, res, rank, s) = linalg.lstsq(a, b) # 最小二乘求系数,t为2*1的矩阵
    #print 'results:', linalg.lstsq(a,b)
    #print 't:', t[0][0]

    xx = x
    r = t[0][0]
    c = t[1][0]
    yy = [math.e**(r*a+c) for a in lnx]
    xx = []
    xydict = {}
    for i in x:
        xx.append(i-1)
    xydict['x'] = xx
    xydict['y'] = yy
    save_quota(prekey + '_xydict', xydict)
    # 保存回归参数
    return t[0][0]

def compute_quota(G, gg ,date, windowsize, topic):
    prekey = _utf8_unicode(topic)+'_'+str(date)+'_'+str(windowsize)
    
    #print 'G_nodes:',len(G.nodes())
    #print 'gg_nodes:', len(gg.nodes())
    #无向图的最大连通子图
    HH = nx.connected_component_subgraphs(gg)
    maxhn = 0
    for h in HH:
        if maxhn < len(h.nodes()):
            maxhn = len(h.nodes())
            H = h
    #print 'H_nodes:', len(H.nodes())

    dCentrality = nx.degree_centrality(G)
    # 度中心性 dict{nodes:value} 度量重要性
    avedc = get_ave(dCentrality)
    #平均度中心性 float
    save_quota(prekey+'_ave_degree_centrality', avedc)
    
    bCentrality = nx.betweenness_centrality(G)
    # 介数中心 dict{nodes:value},度量其对网络流程的重要性
    avebc = get_ave(bCentrality)
    # 平均介数中心性 float
    save_quota(prekey+'_ave_betweenness_centrality', avebc)

    cCentrality = nx.closeness_centrality(G)
    # 紧密中心性 dict{nodes:value},，度量感知整个网络流程事件的位置
    avecc = get_ave(cCentrality)
    # 平均紧密中心性 float
    save_quota(prekey+'_ave_closeness_centrality', avecc)
    
    eCentrality = nx.eigenvector_centrality_numpy(G)
    # 特征向量中心性
    aveec = get_ave(eCentrality)
    # 平均特征向量中心性 float
    save_quota(prekey+'_eigenvector_centrality', aveec)
    

    avespl = nx.average_shortest_path_length(H)
    # 平均最短路径长度 float
    save_quota(prekey+'_average_shortest_path_length', avespl)
    
    
    dhistogram = nx.degree_histogram(G)
    # 节点度分布（从一到最大度的出现频次）
    save_quota(prekey+'_degree_histogram', dhistogram)

    gamma = get_powerlaw(dhistogram, prekey)
    # 幂律分布系数
    save_quota(prekey+'_power_law_distribution', gamma)
    
    
    nnodes = len(G.nodes())
    # the number of nodes in G
    save_quota(prekey+'_number_nodes', nnodes)

    alldegree = sum(dhistogram)
    ave_degree = float(alldegree) / float(nnodes)
    # ave_degree 平均节点度
    save_quota(prekey+'_ave_degree', ave_degree)

    
    nedges = len(G.edges())
    # the number of edged in G
    save_quota(prekey+'_number_edges', nedges)
    
    gdiameter = nx.diameter(H)
    # The diameter is the maximum eccentricity   int-n
    save_quota(prekey+'_diameter', gdiameter)

    geccentricity = nx.eccentricity(H)
    # the eccentricity of nodes in gg
    avegec = get_ave(geccentricity)
    save_quota(prekey+'_ave_eccentricity',avegec)


    sconnectedn = nx.number_strongly_connected_components(G)
    # 强连通子图数量  int-n
    save_quota(prekey+'_number_strongly_connected_components', sconnectedn)

    wconnectesn = nx.number_weakly_connected_components(G)
    # 弱连通子图数量 int-n
    save_quota(prekey+'_number_weakly_connected_components', wconnectesn)
    

    aveclustering = nx.average_clustering(gg)
    # 平均聚类系数
    save_quota(prekey+'_average_clustering', aveclustering)

    dassortativity_coefficient = nx.degree_assortativity_coefficient(G)
    # 同配性系数
    save_quota(prekey + '_degree_assortativity_coefficient', dassortativity_coefficient)

    #kscore = nx.k_core(G)
    # k_score k核数
    #save_quota(prekey + '_k_core', kscore)

    
    

def save_quota(key, value):
    '''保存网络指标
    '''
    try:
        ssdb = SSDB(SSDB_HOST, SSDB_PORT)
        if ssdb:
            print 'ssdb yes'
        else:
            print 'ssdb no'
        result = ssdb.request('set',[key, value])
        if result.code == 'ok':
            print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), 'save success', key ,value
        else:
            print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), 'save failed'
    except Exception, e:
        print time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())),'SSDB ERROR'
