import sqlite3

import nltk
import numpy as np
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
# Gensim
import gensim
import gensim.corpora as corpora
from gensim.models import CoherenceModel

# spacy for lemmatization
import spacy

# Plotting tools
import pyLDAvis
import pyLDAvis.gensim  # don't skip this

from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from scipy.sparse.linalg import svds

medical_stop_words = ["patient", "treatment", "clinical", "study", "result", "method", "data", "analysis",
                      "objective", "background"]
custom_stop_words = stopwords.words('english') + medical_stop_words


def remove_stopwords(texts):
    return [[word for word in gensim.utils.simple_preprocess(str(doc)) if word not in custom_stop_words] for doc in
            texts]


def low_rank_svd(matrix, singular_count=2):
    u, s, vt = svds(matrix, k=singular_count)
    return u, s, vt


def LDA_topic_modeling(abstracts):
    def sent_to_words(sentences):
        for sentence in sentences:
            yield gensim.utils.simple_preprocess(str(sentence), deacc=True)  # deacc=True removes punctuations

    def make_bigrams(texts):
        return [bigram_mod[doc] for doc in texts]

    def lemmatization(texts, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV']):
        nlp = spacy.load('en_core_web_sm', disable=['parser', 'ner'])
        texts_out = []
        for sent in texts:
            doc = nlp(" ".join(sent))
            texts_out.append([token.lemma_ for token in doc if token.pos_ in allowed_postags])
        return texts_out

    # Convert each summary into a list of words
    words_list = list(sent_to_words(abstracts))

    # Creating bigram models
    bigram = gensim.models.Phrases(words_list, min_count=5, threshold=100)

    bigram_mod = gensim.models.phrases.Phraser(bigram)

    # Data preprocessing
    data_nostops = remove_stopwords(words_list)
    data_bigrams = make_bigrams(data_nostops)
    data_lemmatized = lemmatization(data_bigrams, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV'])

    # Creating dictionaries and corpora
    id2word = corpora.Dictionary(data_lemmatized)
    corpus = [id2word.doc2bow(text) for text in data_lemmatized]

    # 构建LDA模型
    lda_model = gensim.models.ldamodel.LdaModel(corpus=corpus,
                                                id2word=id2word,
                                                num_topics=5,
                                                )

    # 可视化主题
    vis = pyLDAvis.gensim.prepare(lda_model, corpus, id2word)
    pyLDAvis.enable_notebook()
    return pyLDAvis.display(vis)


def text_summarization(abstracts):
    tokenize_abstracts = []
    for abstract in abstracts:
        tokenize_abstracts.append(sent_tokenize(abstract))
    tokenize_abstracts = [y for x in tokenize_abstracts for y in x]  # flatten list

    def normalize_abstracts(abstracts):
        # lower case and remove special characters\whitespaces
        abstracts = abstracts.lower()
        abstracts = abstracts.strip()
        # tokenize document
        tokenize_words = nltk.word_tokenize(abstracts)
        # filter stopwords out of document
        filtered_tokens = [word for word in tokenize_words if word not in custom_stop_words]
        # re-create document from filtered tokens
        abstracts = ' '.join(filtered_tokens)
        return abstracts

    # Converting text to numerical features using TF-IDF vectoriser
    normalize_corpus = np.vectorize(normalize_abstracts)
    norm_sentences = normalize_corpus(tokenize_abstracts)

    tv = TfidfVectorizer(min_df=0., max_df=1., use_idf=True)
    dt_matrix = tv.fit_transform(norm_sentences)
    dt_matrix = dt_matrix.toarray()

    vocab = tv.get_feature_names_out()
    td_matrix = dt_matrix.T
    pd.DataFrame(np.round(td_matrix, 2), index=vocab).head(10)

    num_sentences = 5
    num_topics = 3

    # Topics are extracted using Singular Value Decomposition (SVD), which decomposes the word-document matrix into a
    # word-topic matrix and a topic-document matrix
    u, s, vt = low_rank_svd(td_matrix, singular_count=num_topics)
    term_topic_mat, singular_values, topic_document_mat = u, s, vt

    # remove singular values below threshold
    sv_threshold = 0.5
    min_sigma_value = max(singular_values) * sv_threshold
    singular_values[singular_values < min_sigma_value] = 0

    # Sentences with the highest scores were ranked according to their significance scores and selected as the key
    # elements of the text
    salience_scores = np.sqrt(np.dot(np.square(singular_values), np.square(topic_document_mat)))

    top_sentence_indices = (-salience_scores).argsort()[:num_sentences]
    top_sentence_indices.sort()
    print('\n'.join(np.array(tokenize_abstracts)[top_sentence_indices]))


