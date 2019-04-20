#!/usr/bin/env python3
"""
prepare data sogounews
"""

__author__ = "Yanting Li"

import sys, re

IN = open('sogou.txt')
OUT = open('sogouclean.txt', 'w')


line = 'XXX'
article = []
while line:
    line = IN.readline()
    if line.strip() != "":
        line = line.strip()
        article.append(line)
        if line == "</content>":
            # print (article)
            i = article.index("<content>")
            if article[i+1] != '</content>':
                sent = article[i+1]
                # print (sent)
                OUT.write(sent)
                OUT.write("\n")
            article = []


IN.close()
OUT.close()