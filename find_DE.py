#!/usr/bin/env python3
"""
Finding Downward Entailing Operators(DEOs) in Chinese

test:

NPI: 我 没有 任何 书
NPI: 他 没有 任何 中文 书
NPI: 你 从来 没有 吃过 西餐
小红 喜欢 书
小张 喜欢 书
我 喜欢 书
我 喜欢 书
我 喜欢 书

k = n_all / n_byNPI
      count_byNPI   n_byNPI   F_byNPI   count_all   n_all    F      S=F_byNPI/F
我       1            14       1/14        4          26     1/26       1/4 * k
他       1            14       1/14        1          26     1/26        1 * k
你       1            14       1/14        1          26     1/26        1 * k
没有      3           14       1/14         3          26     3/26       1 * k
任何      2           14       1/14         2          26     2/26       1 * k
从来      1           14       1/14         1          26     1/26       1 * k
小红      0           14       0/14         1          26     1/26        0

TODO: larger sentence chunks.


"""

__author__ = "Hai Hu; Yanting Li"

import re, os, sys, time
from collections import Counter

DELIMITER_zh = ["，", "；", "！", "？", ",", ";", "!", "?", "。"]
pat_delimiter_zh = re.compile('([{}])'.format(''.join([d for d in DELIMITER_zh])))
DELIMITER_zh_nocomma = ["；", "！", "？", ";", "!", "?", "。"]
pat_delimiter_zh_nocomma = re.compile('([{}])'.format(''.join([d for d in DELIMITER_zh_nocomma])))

DELIMITER_en = ["\s;\s", "\s.\s", "\s,\s", "\s!\s", "\s?\s"]
pat_delimiter_en = re.compile("(\s;\s|\s\.\s|\s,\s|\s!\s|\s\?\s)")


from zh_NPIs import NPI_zh

WH_zh = {"什么", "谁", "哪儿", "哪里", "哪个", "怎么", "多少"}
WH_OP_zh = {"吗", "呢", "？", "?"}

NPI_en = [
    # column 1 of Danescu 2009
    "any", "at all", "give a damn",  "do a thing",  "bat an eye",
    "giving a damn", "doing a thing", "batting an eye",
    "gave a damn", "did a thing", "batted an eye",
    "given a damn", "done a thing",
    "gives a damn", "does a thing", "bats an eye",

    # col 2
    "in weeks", "in ages", "in years",
    "drink a drop", "last long", "take long", "be long",
    "arrive until", "leave until", "would care", "would mind",
    "drinking a drop", "lasting long", "taking long", "being long", "arriving until", "leaving until",
    "drank a drop", "lasted long", "took long", "arrived until", "left until",
    "drunk a drop", "taken long",
    "drinks a drop", "lasts long", "takes along",

    # col 3
    "budge", "red cent", "but what", "give a shit", "eat a bite",
    "budging", "giving a shit", "eating a bite",
    "budged", "gave a shit", "ate a bite",
    "given a shit", "eaten a bite",
    "budges", "gives a shit", "eats a bite",

    # col 4
    "yet", "ever", "bother to", "lift a finger", "to speak of",
    "bothering to", "lifting a finger",
    "bothered to", "lifted a finger",
    "bothers to", "lifts a finger"
]

NPI_en = [" "+npi+" " for npi in NPI_en]
# NPI_en = [" any "]


# pNPI_zh = ["任何", "手软", "尽如人意", "间断", "辜负", "断", "振", "非但", "幸", "拒", "迟迟", "逾期", "丝毫", "放过", "想到",
#           "例外", "建树", "畅", "多久", "利于", "敌", "逊色", "够", "少于", "可言"
#            ]

# known DE operators in Chinese
KNOWN_DE_OP_zh = ["没", "没有", "不", "不是", "无", "未", "不管", "不论", "无论", "不知", "不顾", "毫不", "不能", "不得", "绝不", "决不", "不准", "从未"]

#KNOWN_DE_OP_zh = []

KNOWN_DE_OP_en = ["not", "n't", "no", "none", "neither", "nor",
                  "few", "each", "every", "without"]
# KNOWN_DE_OP_en = []

USAGE="""
python3 find_DE.py tokenized_filename lang -v -save

e.g. python3 find_DE.py nyt.small.txt en

-v for printing the contexts

-save for saving contexts to file
"""

def main():
    if len(sys.argv) <= 2:
        print(USAGE)
        exit()
    else:
        fn = sys.argv[1]
        lang = sys.argv[2]
        if len(sys.argv) >= 3:
            if '-v' in sys.argv: verbose = True
            else: verbose = False
            if '-save' in sys.argv: save_context = True
            else: save_context = False
     # lang = "zh"
    # lang = "en"
    start_time = time.time()
    my_counter = NPI_counter(fn, lang, verbose, save_context)
    my_counter.NPI_contexts()


    # With distillation
    my_counter.compute_Sd()
    # No distillation
    # my_counter.compute_S()

    ## ---------------------
    ## begin: sanity check
    ## ---------------------
    # my_context = ['``', 'so', 'i', 'doubt', 'you', '\'ll', 'see']
    #
    # for w in my_context:
    #     print()
    #     print(w)
    #     print(my_counter.wc_in_context[w])
    #     print(my_counter.wc_in_allwords[w])
    #     print("S(c):", my_counter.wc_in_context[w]/my_counter.wc_in_allwords[w] * 1790662/5292)
    #     print("=?", my_counter.S_cache[w])
    #
    # n1 = sum( [my_counter.S_cache[w] for w in my_context] )
    # print("\nn1=", n1)
    # print("\n=?", my_counter.n_cache[tuple(my_context)])

    # so S(c) and n(c) are correctly calculated!!

    ## ---------------------
    ## end: sanity check
    ## ---------------------

    # exit()

    counter = 0
    with open("DElist.txt", 'w') as f:
        for c, sd in reversed(sorted(my_counter.Sd_cache.items(), key = lambda x: x[1])):
        # for c, s in reversed(sorted(my_counter.S_cache.items(), key = lambda x: x[1])):
        # for c, sd in sorted(my_counter.Sd_cache.items(), key=lambda x: x[1]):
            counter += 1
            if counter == 151: break
            print("{:3} {} {}".format(counter, c, sd))
            # print("{:3} {} {}".format(counter, c, s))
            f.write("{}\t{}\n".format(counter, c))
    f.close()
        
    # print(my_counter.n_cache)
    print("\ncache accessed: ")
    print(my_counter.cache_counter)
    print("\n--- {} seconds ---\n".format(time.time() - start_time))

class NPI_counter(object):
    def __init__(self, fn, lang, verbose, save_context):
        self.lang = lang
        self.verbose = verbose
        self.save_context = save_context
        if self.lang == "zh":
            self.NPIs = NPI_zh
            # self.pat_delimiter = pat_delimiter_zh
            self.pat_delimiter = pat_delimiter_zh_nocomma
            self.known_DE_op = KNOWN_DE_OP_zh
        else:
            self.NPIs = NPI_en
            self.pat_delimiter = pat_delimiter_en
            self.known_DE_op = KNOWN_DE_OP_en
        
        self.S_cache = {}
        self.Sd_cache = {}
        self.n_cache = {}
        self.fn = fn
        self.wc_in_context = {}
        self.wc_in_allwords = {}
        self.n_words_context = 0
        self.n_allwords = 0
        self.context_list = []  # a list of tuples, each tuple a context
        self.words_in_context = []  # all tokens in context

        self.method = 1  # operationalization method in n()
#        self.method = 2  # operationalization method in n(). all c in context
        self.thresh_whole = 100  # min freq in allwords
        self.thresh_context = 10  # min freq in context

        self.cache_counter = 0  # count num times the cache is accessed

        self.large_num = 1000000

    def NPI_contexts(self):
        # get wc_in_allwords
        # cat CTB_seg_split2_all| tr ' ' '\n' | LC_COLLATE=C sort | LC_COLLATE=C uniq -c > CTB_seg_split2_all.count
        my_command = "cat {} | tr ' ' '\n' | tr '\t' '\n' " \
                     "| LC_COLLATE=C sort | LC_COLLATE=C uniq -c " \
                     "> {}.count".format(self.fn, self.fn)
        os.system(my_command)
        with open(self.fn + ".count") as f:
            for line in f:
                if len(line.strip().split()) != 2: continue
                # ignore case!
                if self.lang == 'zh':
                    count, word = int(line.strip().split()[0]), line.strip().split()[1]
                else:
                    count, word = int(line.strip().split()[0]), line.strip().split()[1].lower()
                # could already have a count for Capitalized word
                self.wc_in_allwords[word] = self.wc_in_allwords.get(word, 0) + count

        if self.save_context: fn_context = open(self.fn + '.context', 'w')

        npi_context_dict = {}

        counter = 0
        with open(self.fn) as f:
            for line in f:
                # TODO test different ways of splitting into chunks
                # maybe not on ，

                # line_split = ['1998年\t', ',', '\t三峡\t工程\t转入\t二期\t施工\t', '。', '']
                line_split = self.pat_delimiter.split(line.strip())

                # write in paper
                # add back the delimiter to remove cases where wh co-occur with wh operators
                idx = 0
                new_line_split = []  # want: '什么意思\t?'
                while idx < len(line_split) - 1:
                    new_line_split.append(line_split[idx] + line_split[idx+1])
                    idx += 2

                # new_line_split = ['abc','def','ghi',...]
                # we want: 'abcdef','defghi'

                for chunk in new_line_split:
                    #Code on Chinese texts written by Hai
                    if self.lang == "zh":
                        # TODO try different ways of identifying NPIs
                        # for now: trust the segmentation
                        words_seg = chunk.split()  # ['但是', '任何', '成功', '的', '企业'] 都?
                        # print(words_seg)

                        # words_whole_str = ''.join(words_seg)
                        # print(words_whole_str)
                        # print()
                        context = words_seg

                        # count the number of NPIs
                        # num_npi = self.count_npi()
                        # if num_npi >= 2:
                        #     print(context)

                        # if NPI in chunk
                        for npi in self.NPIs:
                            if npi in context:
                                # don't want wh + wh operators, e.g. 什么 + 吗
                                # if npi in WH_zh:
                                #     if any([op in context for op in WH_OP_zh]):
                                #         continue

                                # don't want known DE operators
                                if not self.whether_known_DE(context):
                                # if not any([de in context for de in self.known_DE_op]):
                                    counter += 1
                                    context_old = context[:]

                                        # remove all npi in the context
                                    context = self.remove_all_npi(context)

                                    if self.verbose: print(context)
                                    if self.save_context:
                                        fn_context.write(' '.join(context_old) + "\n")

                                    # save to npi_context_dict
                                    if npi not in npi_context_dict:
                                        npi_context_dict[npi] = [context_old]
                                    else: npi_context_dict[npi].append(context_old)

                                    self.words_in_context.extend(context)
                                    self.context_list.append(tuple(context))
                                    self.n_words_context += len(context)
                                    if len(self.context_list) % 1000 == 0:
                                        print("processed {:7} contexts".format(len(self.context_list)))
                                    # TODO what if 2 NPIs? break it! we only need to
                                    # capture the potential DE operators
                                    break
                                    # context = context_old

                    # Code on English texts written by Yanting
                    else:  # lang = "en"
                        words = " " + chunk.lower() + " "  # " in any event "
                        # if NPI in chunk
                        idx_NPI, mynpi = self.idx_first_NPI(words)
                        if idx_NPI != self.large_num:  # if NPI found
                            context = words[:idx_NPI]
                            context = context.strip().split()
                            # don't want known DE operators
                            if context:
                                if not any([de in context for de in self.known_DE_op]) and context != ["``"] and context != ["''"]:
                                    if self.verbose:
                                        # words  :  and it is best to live without any ties and commitments
                                        # context: ['and', 'it', 'is', 'best', 'to', 'live', 'without']
                                        print("\nwords  :", words)
                                        print("context:", context)
                                    if self.save_context:
                                        fn_context.write(' '.join(context) + "\n")

                                    # save to npi_context_dict
                                    if mynpi not in npi_context_dict:
                                        npi_context_dict[mynpi] = [context]
                                    else:
                                        npi_context_dict[mynpi].append(context)

                                # if context:
                                    counter += 1
                                    self.words_in_context.extend(context)
                                    self.context_list.append(tuple(context))
                                    self.n_words_context += len(context)
                                    if len(self.context_list) % 1000 == 0:
                                        print("processed in {:7} contexts".format(len(self.context_list)))

        if self.save_context: fn_context.close()

        self.wc_in_context = Counter(self.words_in_context)
        self.n_allwords = sum(self.wc_in_allwords.values())
        print('\nfound {} NPI contexts\n'.format(counter))
        print('n_allwords', self.n_allwords)
        print('n_words_context', self.n_words_context)
        print('len wc_in_allwords', len(self.wc_in_allwords))
        print('len wc_in_context', len(self.wc_in_context))
        print()

        with open(self.fn + ".npi.context", 'w') as f:
            f.write("NPI\tcontext\n")
            for npi in sorted(npi_context_dict.keys()):
                for context in npi_context_dict[npi]:
                    f.write("{}\t{}\n".format(npi, ' '.join(context)))

# Calculating Sd: original codes written by Yanting, broken down into functions by Hai.
    def count_npi(self, context):
        # TODO
        ans = 0
        return ans

    def whether_known_DE(self, context):
        """ return False if no known DE operator in context = [谁 都 不能 产生 任何 分裂 国家 的 企图] """
        for word in context:
            if any([de in word for de in ['不', '没', '未', '无'] ]):
                return True
        return False

    def remove_all_npi(self, context):
        """ remove all npis in context, context = [谁 都 不能 产生 任何 分裂 国家 的 企图] """
        ans = []
        for word in context:
            if word not in self.NPIs:
                ans.append(word)
        return ans

    def idx_first_NPI(self, words):
        """ return the idx of the first NPI in a string(words)
        e.g. words = " if you ever wanted to do this "  ever is NPI
        return 8
        """
        idx = self.large_num
        mynpi = None
        for npi in self.NPIs:
            idx_tmp = words.find(npi)
            if idx_tmp != -1 and idx_tmp < idx:
                idx = idx_tmp
                mynpi = npi
        return min(idx, self.large_num), mynpi

    def get_S(self, c):
        # w/o cache 1 min 26 s
        # w cache 1 min 26 s
        if c in self.S_cache:
            # print("get cache")
            return self.S_cache[c]
        FbyNPIc = self.wc_in_context.get(c) / self.n_words_context
        if self.wc_in_allwords.get(c) is None:
            print(c)
            self.wc_in_allwords[c] = 1
        Fc = self.wc_in_allwords.get(c) / self.n_allwords
        S = FbyNPIc / Fc
        self.S_cache[c] = S
        if c in ["没", "没有", "不", "无"]:
            print(c, S)
        return S

    def compute_S(self):
        """ compute S for all candidates """
        for candidate in self.wc_in_context:
            # TODO: tune 150, 10
            if self.wc_in_allwords[candidate] < self.thresh_whole: continue
            if self.wc_in_context[candidate] < self.thresh_context: continue
            self.get_S(candidate)

    def get_n(self, context, candidate):
        # ---------------------
        # operationalization 1:
        # context = [we, do, not, have, plans]
        # candidate = not
        # n = S(we) + S(do) + S(have) + S(plans)
        if self.method == 1:
            # check cache
            if candidate in self.n_cache:
                if context in self.n_cache[candidate]:
                    self.cache_counter += 1
                    return self.n_cache[candidate][context]
            else:
                self.n_cache[candidate] = {}

            ans = 0

            piggys = set(context)  # convert context to set
            piggys.remove(candidate)
            if piggys:
                for p in piggys:
                    ans += self.get_S(p)
            else:
                ans = self.get_S(candidate)
            self.n_cache[candidate][context] = ans
            return ans

        # ---------------------
        # operationalization 2:
        # context = [we, do, not, have, plans]
        # candidate = not
        # n = S(we) + S(do) + S(not) + S(have) + S(plans)
        else:
            # check cache
            if context in self.n_cache:
                self.cache_counter += 1
                return self.n_cache[context]

            ans = 0

            for p in context:
                ans += self.get_S(p)

            self.n_cache[context] = ans
            return ans

    def compute_Sd(self):
        """ compute Sd for all
        frequency boundary here """
        for candidate in self.wc_in_context:
            if self.wc_in_allwords[candidate] < self.thresh_whole: continue
            if self.wc_in_context[candidate] < self.thresh_context: continue
            self.compute_Sd_helper(candidate)

    def compute_Sd_helper(self, candidate):
        """ compute Sd for a single candidate """
        numerator = 0
        for context in self.context_list:
            if candidate in context:
                # print(context)
                numerator += self.get_S(candidate) / self.get_n(context, candidate)
        self.Sd_cache[candidate] = numerator / self.get_N(candidate)

    def get_N(self, candidate):
        return self.wc_in_context.get(candidate)

if __name__ == "__main__":
    main()



