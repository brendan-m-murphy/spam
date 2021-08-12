import pandas as pd
import re


def clean1(email):
    pat = re.compile(r'([-\w]+: .+|<.*|.*>|.*NextPart.*|charset=.*|\w+\.\w+\.?\w*\.?\w*\.?\w*)')
    email2 = pat.sub(' ', email)
    return [x.lower()
            for x in re.findall(r'[A-Za-z]+', email2)
            if len(x) > 2]

def create_corpus(f, X):
    "X training set, f maps email to list of words"
    corpus = {}
    for email in X:
        for word in f(email):
            corpus[word] = corpus.get(word, 0) + 1
    return corpus

def create_df(X, word_freq):
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

word_freq = pd.Series(create_corpus(clean1, X_train))
filt = word_freq.between(6, 900)
