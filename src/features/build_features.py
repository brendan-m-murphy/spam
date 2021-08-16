import email
import email.parser
import email.policy
import pandas as pd
import re


def clean1(email_):
    pat = re.compile(r'([-\w]+: .+|<.*|.*>|.*NextPart.*|charset=.*|\w+\.\w+\.?\w*\.?\w*\.?\w*)')
    return pat.sub(' ', email_)


def clean2(email_):
    msg = email.parser.Parser(policy=email.policy.default).parsestr(email_)
    return msg.get_content()


def get_words(email, exclude_below=2):
    return [x.lower()
            for x in re.findall(r'[A-Za-z]+', email)
            if len(x) > exclude_below]

def create_corpus(f, X):
    "X training set, f maps email to list of words"
    corpus = {}
    for email in X:
        for word in f(email):
            corpus[word] = corpus.get(word, 0) + 1
    return corpus

def create_df(X, corpus):
    word_freq = pd.Series(corpus)
    template = {k: 0 for k in sorted(word_freq.index.to_list())}
    keys = template.keys()

    def feature_vec1(email):
        vec = template.copy()
        for x in clean1(email):
            if x in keys:
                vec[x] = 1
        return vec

    df = pd.DataFrame({i: feature_vec1(email)
                       for i, email in enumerate(X)})

    return df.T
