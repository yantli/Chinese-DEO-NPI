#!/usr/bin/env python3
"""
prepare data wsj1994-1996
"""

__author__ = "Yanting Li"

import sys, re

IN = open('1995.txt')
OUT = open('1995clean.txt', 'w')


line = 'XXX'
article = []
while line:
    line = IN.readline()
    if line.strip() != "":
        line = line.strip()
        article.append(line)
        if line == "</TEXT>":
            # print (article)
            i = article.index("<TEXT>")
            # for n in (0, len(article)-1):
            #     if article[n].find("<TEXT>"):
            #         print (n)
            #     else:
            #         n += 1
            text = []
            # print (i, len(article))
            n = i+2
            while n < len(article)-1:
                # print (n)
                text.append(article[n])
                n += 1
            # print (text)

            sent = ' '.join(text)
            sent = sent.replace("<p> ", "\n")
            # print (sent)
            OUT.write(sent)
            article = []


IN.close()
OUT.close()