import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from gensim.parsing import remove_stopwords
from wordcloud import WordCloud

import nltk
from nltk.corpus import stopwords

import re
import numpy as np
import pandas as pd
from pprint import pprint

# Gensim
import gensim
import gensim.corpora as corpora
from gensim.utils import simple_preprocess
from gensim.models import CoherenceModel

# spacy for lemmatization
import spacy

# Plotting tools
import pyLDAvis
import pyLDAvis.gensim  # don't skip this

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
#
conn = sqlite3.connect('homework.db')
c = conn.cursor()

# 执行SQL查询，选择abstract和year列
c.execute('SELECT abstract, year FROM article')

# 读取所有结果
results = c.fetchall()

# 用字典来分组数据，键为年份，值为对应年份的abstract列表
grouped_by_year = {}
for abstract, year in results:
    if year in grouped_by_year:
        grouped_by_year[year].append(str(abstract))
    else:
        grouped_by_year[year] = [abstract]

years = sorted(list(grouped_by_year.keys()))
print(grouped_by_year[2024])

def LDA_topic_modeling(abstracts):
    def sent_to_words(sentences):
        for sentence in sentences:
            yield gensim.utils.simple_preprocess(str(sentence), deacc=True)  # deacc=True removes punctuations

    def remove_stopwords(texts):
        return [[word for word in gensim.utils.simple_preprocess(str(doc)) if word not in custom_stop_words] for doc in
                texts]

    def make_bigrams(texts):
        return [bigram_mod[doc] for doc in texts]

    def lemmatization(texts, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV']):
        nlp = spacy.load('en_core_web_sm', disable=['parser', 'ner'])
        texts_out = []
        for sent in texts:
            doc = nlp(" ".join(sent))
            texts_out.append([token.lemma_ for token in doc if token.pos_ in allowed_postags])
        return texts_out

    # 添加医学领域相关的停用词
    medical_stop_words = ["patient", "treatment", "clinical", "study", "result", "method", "data", "analysis",
                          "objective", "background"]
    custom_stop_words = stopwords.words('english') + medical_stop_words

    # 转换每个摘要为词列表
    words_list = list(sent_to_words(abstracts))

    # 创建bigram和trigram模型
    bigram = gensim.models.Phrases(words_list, min_count=5, threshold=100)
    trigram = gensim.models.Phrases(bigram[words_list], threshold=100)

    bigram_mod = gensim.models.phrases.Phraser(bigram)
    trigram_mod = gensim.models.phrases.Phraser(trigram)

    # 数据预处理
    data_nostops = remove_stopwords(words_list)
    data_bigrams = make_bigrams(data_nostops)
    data_lemmatized = lemmatization(data_bigrams, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV'])

    # 创建字典和语料库
    id2word = corpora.Dictionary(data_lemmatized)
    corpus = [id2word.doc2bow(text) for text in data_lemmatized]

    # 构建LDA模型
    lda_model = gensim.models.ldamodel.LdaModel(corpus=corpus,
                                                id2word=id2word,
                                                num_topics=10,
                                                random_state=100,
                                                update_every=1,
                                                chunksize=100,
                                                passes=10,
                                                alpha='auto',
                                                per_word_topics=True)

    # 可视化主题
    vis = pyLDAvis.gensim.prepare(lda_model, corpus, id2word)
    pyLDAvis.enable_notebook()
    return pyLDAvis.display(vis)


def text_summarization(input_text):

    # Parse the input text
    parser = PlaintextParser.from_string(input_text, Tokenizer("english"))

    # Create an LSA summarizer
    summarizer = LsaSummarizer()

    # Generate the summary
    summary = summarizer(parser.document, sentences_count=3)  # You can adjust the number of sentences in the summary

    # Output the summary
    print("\nSummary:")
    for sentence in summary:
        print(sentence)



