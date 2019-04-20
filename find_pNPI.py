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


"""

__author__ = "Hai Hu; Yanting Li"

import re, os, sys, time
from collections import Counter

DELIMITER_zh = ["，", "；", "！", "？", ",", ";", "!", "?", "。"]
pat_delimiter_zh = re.compile('([{}])'.format(''.join([d for d in DELIMITER_zh])))

# known DE operators in Chinese
KNOWN_DE_OP_zh = ["没", "没有", "不", "不是", "无", "未", "不管", "不论", "无论", "不知", "不顾", "毫不", "不能", "不得", "绝不", "决不", "不准", "从未"]

# KNOWN_DE_OP_zh = []

USAGE="""
python3 find_pNPI.py tokenized_filename -v -save

e.g. python3 find_pNPI.py nyt.small.txt

-v for printing the contexts

-save for saving contexts to file
"""

def main():
    fn = sys.argv[1]
    if len(sys.argv) >= 2:
        if '-v' in sys.argv: verbose = True
        else: verbose = False
        if '-save' in sys.argv: save_context = True
        else: save_context = False
    start_time = time.time()
    my_counter = DEO_counter(fn, verbose, save_context)
    my_counter.DEO_contexts()


    # With distillation
    my_counter.compute_Sd()
    # No distillation
    # my_counter.compute_S()


    counter = 0
    with open("pNPIlist.txt", 'w') as f:
        for c, sd in reversed(sorted(my_counter.Sd_cache.items(), key = lambda x: x[1])):
        # If without distillation
        # for c, s in reversed(sorted(my_counter.S_cache.items(), key = lambda x: x[1])):

            counter += 1
            if counter == 151: break
            print("{:3} {} {}".format(counter, c, sd))
            # If without distillation
            # print("{:3} {} {}".format(counter, c, s))
            f.write("{}\t{}\n".format(counter, c))
    f.close()
        
    # print(my_counter.n_cache)
    print("\ncache accessed: ")
    print(my_counter.cache_counter)
    print("\n--- {} seconds ---\n".format(time.time() - start_time))

class DEO_counter(object):
    def __init__(self, fn, verbose, save_context):
        self.verbose = verbose
        self.save_context = save_context
        self.DEOs = KNOWN_DE_OP_zh
        self.pat_delimiter = pat_delimiter_zh

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

        # self.method = 1  # operationalization method in n()
        self.method = 2  # operationalization method in n(). all c in context
        self.thresh_whole = 120  # min freq in allwords
        self.thresh_context = 63  # min freq in context

        self.cache_counter = 0  # count num times the cache is accessed

        self.large_num = 1000000

    def DEO_contexts(self):
        # get wc_in_allwords
        my_command = "cat {} | tr ' ' '\n' | tr '\t' '\n' " \
                     "| LC_COLLATE=C sort | LC_COLLATE=C uniq -c " \
                     "> {}.count".format(self.fn, self.fn)
        os.system(my_command)
        with open(self.fn + ".count") as f:
            for line in f:
                if len(line.strip().split()) != 2: continue
                count, word = int(line.strip().split()[0]), line.strip().split()[1]
                self.wc_in_allwords[word] = self.wc_in_allwords.get(word, 0) + count

        if self.save_context: fn_context = open(self.fn + '.context', 'w')

        deo_context_dict = {}

        counter = 0
        with open(self.fn) as f:
            for line in f:
                line_split = self.pat_delimiter.split(line.strip())

                idx = 0
                new_line_split = []  # want: '什么意思\t?'
                while idx < len(line_split) - 1:
                    new_line_split.append(line_split[idx] + line_split[idx+1])
                    idx += 2
                # print()
                # print(line_split)
                # print(new_line_split)

                for chunk in new_line_split:
                    words_seg = chunk.split()  # ['但是', '任何', '成功', '的', '企业'] 都?
                    # print(words_seg)

                    # words_whole_str = ''.join(words_seg)
                    # print(words_whole_str)
                    # print()
                    context = words_seg

                    # if DEO in chunk
                    for deo in self.DEOs:
                        if deo in context:
                            counter += 1
                            context_old = context[:]

                            # remove all deo in the context
                            context = self.remove_all_deo(context)

                            if self.verbose: print(context)
                            if self.save_context:
                                fn_context.write(' '.join(context_old) + "\n")

                            # save to deo_context_dict
                            if deo not in deo_context_dict:
                                deo_context_dict[deo] = [context_old]
                            else: deo_context_dict[deo].append(context_old)

                            self.words_in_context.extend(context)
                            self.context_list.append(tuple(context))
                            self.n_words_context += len(context)
                            if len(self.context_list) % 1000 == 0:
                                print("processed {:7} contexts".format(len(self.context_list)))
                            break


        if self.save_context: fn_context.close()

        self.wc_in_context = Counter(self.words_in_context)
        self.n_allwords = sum(self.wc_in_allwords.values())
        print('\nfound {} DEO contexts\n'.format(counter))
        print('n_allwords', self.n_allwords)
        print('n_words_context', self.n_words_context)
        print('len wc_in_allwords', len(self.wc_in_allwords))
        print('len wc_in_context', len(self.wc_in_context))
        print()

        with open(self.fn + ".deo.context", 'w') as f:
            f.write("DEO\tcontext\n")
            for deo in sorted(deo_context_dict.keys()):
                for context in deo_context_dict[deo]:
                    f.write("{}\t{}\n".format(deo, ' '.join(context)))
    #
    # def count_deo(self, context):
    #     # TODO
    #     ans = 0
    #     return ans

    def remove_all_deo(self, context):
        """ remove all DEOs in context, context = [谁 都 不能 产生 任何 分裂 国家 的 企图] """
        ans = []
        for word in context:
            if word not in self.DEOs:
                ans.append(word)
        return ans

    def idx_first_DEO(self, words):
        """ return the idx of the first DEO in a string(words)        """
        idx = self.large_num
        for deo in self.DEOs:
            idx_tmp = words.find(deo)
            if idx_tmp != -1 and idx_tmp < idx:
                idx = idx_tmp
        return min(idx, self.large_num)

    def get_S(self, c):
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
        return S

    def compute_S(self):
        """ compute S for all candidates """
        for candidate in self.wc_in_context:
            if self.wc_in_allwords[candidate] < self.thresh_whole: continue
            if self.wc_in_context[candidate] < self.thresh_context: continue
            self.get_S(candidate)

    def get_n(self, context, candidate):
        # ---------------------
        # operationalization 1:
        # context = [we, don't, have, plans]
        # candidate = don't
        # n = S(we) + S(have) + S(plans)
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
            for p in piggys:
                ans += self.get_S(p)

            self.n_cache[candidate][context] = ans
            return ans

        # ---------------------
        # operationalization 2:
        # context = [we, don't, have, plans]
        # candidate = don't
        # n = S(we) + S(don't) + S(have) + S(plans)
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



