# -*- coding: utf-8 -*-

import re
import opencc
import os
import time
import csv
from gensim import corpora
from utils import load_scws, cut, load_emotion_words
from flow_psy import flow_psychology_classfiy
#from test_data import input_data #测试输入

AB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

cut_str = load_scws()

cc = opencc.OpenCC('s2t', opencc_path='/usr/bin/opencc')
emotions_words = load_emotion_words()
emotions_words = [unicode(e, 'utf-8') for e in emotions_words]
t_emotions_words = [cc.convert(e) for e in emotions_words]
emotions_words.extend(t_emotions_words)
emotions_words = [w.encode('utf-8') for w in emotions_words]
emotions_words_set = set(emotions_words)
emotion_pattern = re.compile(r'\[(\S+?)\]')


def if_emoticoned_weibo(r):
    # 微博是否包含指定的表情符号集
    emotions = re.findall(emotion_pattern, r['text'])
    is_emoticoned = 1 if set(emotions) & emotions_words_set else 0
    return is_emoticoned

'''define 2 kinds of seed emoticons'''
positive_set = set()
negative_set = set()

with open(os.path.join(AB_PATH, '4groups.csv')) as f:
    for l in f:
        pair = l.rstrip().split('\t')
        if pair[1] == '1' or pair[1] == '4':
            positive_set.add(pair[0])

        if pair[1] == '2' or pair[1] == '3':
            negative_set.add(pair[0])

POSITIVE = 1
NEGATIVE = -1
MIDDLE = 0

def emoticon(text):
    """ Extract emoticons and define the overall sentiment """

    remotions = re.findall(emotion_pattern, text)
    positive = 0
    negative = 0

    for e in remotions:

        if e in positive_set:
            positive = positive + 1
        elif e in negative_set:
            negative = negative + 1
        else:
            pass

    if positive > negative:
        return POSITIVE
    elif positive < negative:
        return NEGATIVE
    else:
        return MIDDLE


'''define subjective dictionary and subjective words weight'''
dictionary_1 = corpora.Dictionary.load(os.path.join(AB_PATH, 'triple_subjective_1.dict'))
step1_score = {}
with open(os.path.join(AB_PATH, 'triple_subjective_1.txt')) as f:
    for l in f:
        lis = l.rstrip().split()
        step1_score[int(lis[0])] = [float(lis[1]), float(lis[2])]

'''define polarity dictionary and polarity words weight'''
dictionary_2 = corpora.Dictionary.load(os.path.join(AB_PATH, 'binary_polarity.dict'))
step2_score = {}
with open(os.path.join(AB_PATH, 'binary_weight.txt')) as f:
    for l in f:
        lis = l.rstrip().split()
        step2_score[int(lis[0])] = [float(lis[1]), float(lis[2])]


def triple_classifier(tweet):
    '''
    输出结果：
    0 中性
    1 积极
    2 生气
    3 焦虑
    4 悲伤
    5 厌恶
    6 消极其他
    '''
    sentiment = MIDDLE
    if isinstance(tweet['text'],unicode):
        text = tweet['text']
    else:
        text = tweet['text'].decode('utf-8')
    keywords_list = []

    emoticon_sentiment = emoticon(text.encode('utf-8'))
    if emoticon_sentiment != MIDDLE:
        entries = cut(cut_str, text.encode('utf-8'))
        entry = [e.decode('utf-8', 'ignore') for e in entries]
        keywords_list = entry
        if emoticon_sentiment == POSITIVE:
            sentiment = emoticon_sentiment
            text = u''
        else:
            sentiment = flow_psychology_classfiy(text.encode('utf-8'))
            if sentiment == 0:
                sentiment = 6
            text = u''
    
    if text != u'':
        entries = cut(cut_str, text.encode('utf-8'))
        entry = [e.decode('utf-8', 'ignore') for e in entries]
        keywords_list = entry
        
        
        bow = dictionary_1.doc2bow(entry)
        s = [1, 1]
        for pair in bow:
            s[0] = s[0] * (step1_score[pair[0]][0] ** pair[1])
            s[1] = s[1] * (step1_score[pair[0]][1] ** pair[1])
        if s[0] < s[1]:
            bow = dictionary_2.doc2bow(entry)
            s2 = [1, 1]
            for pair in bow:
                s2[0] = s2[0] * (step2_score[pair[0]][0] ** pair[1])
                s2[1] = s2[1] * (step2_score[pair[0]][1] ** pair[1])
            if s2[0] > s2[1]:
                sentiment = POSITIVE
            elif s2[0] == s2[1]:
                sentiment = MIDDLE
            else:
                sentiment = flow_psychology_classfiy(text.encode('utf-8'))
                if sentiment == 0:
                    sentiment = 6
        else:
            sentiment = MIDDLE        

    return sentiment, keywords_list

##def write_result(uid_weibo,result,label_list):
##
##    with open('./result/result_20160113.csv', 'wb') as f:
##        writer = csv.writer(f)
##        for i in range(0,len(uid_weibo)):
##            writer.writerow((uid_weibo[i],result[i],label_list[i]))        

##if __name__ == '__main__':
##    uid_weibo = input_data()
##    start = time.time()
##    result = []
##    for k,v in uid_weibo.iteritems():
##        for text in v:
##            domain, keywords_list = triple_classifier(text)
##            result.append(domain)
##    end = time.time()
##    print '%s seconds...' % (end-start)
##    print result

