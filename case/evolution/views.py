#-*- coding:utf-8 -*-

import os
import json
from city_count import Pcount
from BeautifulSoup import BeautifulSoup
from case.extensions import db
from case.model import CityRepost
# 根据count不同，给不同的城市不同的颜色
from city_color import province_color_map
from flask import Blueprint, url_for, render_template, request, abort, flash, session, redirect
from city_map import partition_count, map_circle_data, map_line_data, statistics_data

mod = Blueprint('evolution', __name__, url_prefix='/evolution')

#mtype_kv={'original': 1, 'forward': 2, 'comment': 3,'sum':4}

Minute = 60
Fifteenminutes = 15 * Minute
Hour = 3600
SixHour = Hour * 6
Day = Hour * 24
MinInterval = Fifteenminutes

province_list = [u'安徽', u'北京', u'重庆', u'福建', u'甘肃', u'广东', u'广西', u'贵州', u'海南', \
                 u'河北', u'黑龙江', u'河南', u'湖北', u'湖南', u'内蒙古', u'江苏', u'江西', u'吉林', \
                 u'辽宁', u'宁夏', u'青海', u'山西', u'山东', u'上海', u'四川', u'天津', u'西藏', u'新疆', \
                 u'云南', u'浙江', u'陕西', u'台湾', u'香港', u'澳门', u'海外', u'其他']


def info2map(infos):
    count = {}
    rank = {}
    ratio = {}
    top10 = {}
    for info in infos:
        map_dict = infos[info]
        count[info] = [0] * 35
        rank[info] = [0] * 35
        ratio[info] = [0] *35
        for p in range(35):
            try:
                pcount = map_dict['count'][province_list[p]][0]
                prank = map_dict['count'][province_list[p]][1]
                pratio = map_dict['count'][province_list[p]][2]
            except:
                continue
            count[info][p] = pcount
            rank[info][p] = prank
            ratio[info][p] = pratio

        top10[info] = map_dict['summary']

    data = {'count':count, 'rank':rank, 'ratio':ratio, 'top10':top10}

    return data


def readPropagateSpatial(stylenum, topic, end_ts , during):
    """将从数据库中读取的数据转化为map_data
    """
    city_count = {}
    city_count = Pcount(end_ts, during, stylenum, topic) # PCount从db中计算各个省市地区的总数
    max_count = max(city_count.values())
    map_data = province_color_map(city_count)

    return max_count, map_data


@mod.route("/topic_ajax_spatial/")
def ajax_spatial():
    """
    地域演化的页面,从database获取数据返回topic_spatial.html
    """

    stylenum = request.args.get('style', '') # stylenum表示返回count是origin：1,forward：2,comment：3,sum：4 
    stylenum = int(stylenum)
    topic = request.args.get('topic', '')
    during = request.args.get('during', 60 * 60) # 默认查询时间粒度为3600秒
    during = int(during)
    end_ts = request.args.get('end_ts', '')
    end_ts = long(end_ts)
    start_ts = request.args.get('start_ts', '')
    start_ts = long(start_ts)
    pointnum = (end_ts - start_ts) / during # 时间点数

    spatial_dict = {}
    global_max_count = 0
    for i in range(pointnum):
        end_ts = start_ts +  during * (i + 1)
        max_count, topic_spatial_info = readPropagateSpatial(stylenum, topic, end_ts , during)  # 查询在一定时间范围内，某个topic的stylenum信息各个省市的数量
        if global_max_count < max_count:
            global_max_count = max_count
        spatial_dict[str(end_ts)] = topic_spatial_info

    map_data = info2map(spatial_dict)
    map_data['max_count'] = global_max_count

    return json.dumps(map_data)

@mod.route('/city_map_view/')
def city_map_view():
    topic = u'中国'
    ts_arr = []
    results = []
    items = db.session.query(CityRepost).filter(CityRepost.topic == topic).all()
    if items:
        for item in items:
            r = {}
            r['original'] = item.original
            r['topic'] = item.topic
            r['mid'] = item.mid
            r['ts'] = item.ts
            r['origin_location'] = item.origin_location
            r['repost_location'] = item.repost_location

            ts_arr.append(r['ts'])
            ts_arr = sorted(list(set(ts_arr)))
            results.append(r)
        ts_series, groups = partition_count(ts_arr, results)
        draw_circle_data = map_circle_data(groups)
        max_repost_num, draw_line_data = map_line_data(groups)
        repost_series, origin_series, post_series, statistic_data = statistics_data(groups)
        print 'end'
        return json.dumps({'ts_arr':ts_arr, 'results':results, 'ts_series':ts_series, 'groups': groups, \
                'draw_circle_data':draw_circle_data, 'draw_line_data': draw_line_data, 'max_repost_num': max_repost_num, \
                'repost_series':repost_series, 'origin_series':origin_series, 'post_series':post_series, 'statistic_data':statistic_data})
    else:
        print 'no results'
