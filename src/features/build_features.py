import email
import email.policy
import nltk
import pandas as pd
import pickle
import random
import re
from sklearn.base import BaseEstimator, TransformerMixin


def unzip(x):
    y, z = zip(*x)
    return list(y), list(z)


def get_raw_data(type='train', path='../../data/interim/', seed=42):
    if type in ('train', 'val', 'test'):
        with open(path + f'ham_{type}.pkl', 'rb') as f:
            ham = pickle.load(f)
        with open(path + f'spam_{type}.pkl', 'rb') as f:
            spam = pickle.load(f)
        raw = [(x, 0) for x in ham] + [(x, 1) for x in spam]
        random.seed(seed)
        random.shuffle(raw)
        X, y = unzip(raw)
        return X, pd.Series(y)
    else:
        raise ValueError(f'Type "{type}" not recognized. Please enter "train", "val", or "test".')


def clean1(email_):
    pat = re.compile(r'([-\w]+: .+|<.*|.*>|.*NextPart.*|charset=.*|\w+\.\w+\.?\w*\.?\w*\.?\w*)')
    return pat.sub(' ', email_)


def clean2(mail):
    msg = email.message_from_string(mail, policy=email.policy.default)
    pat_html_dumb = re.compile('<.*?>', re.DOTALL)

    for part in msg.walk():
        if part.get_content_type() in ('text/plain', 'text/html'):
            try:
                cont = part.get_content()
            except:
                cont = str(part.get_payload())
            else:
                return re.sub(pat_html_dumb, " ", cont)
    return ""


def get_words(email, exclude_below=2, stemming=False):
    result = [x.lower()
              for x in re.findall(r'[A-Za-z]+', email)
              if len(x) > exclude_below]
    if stemming:
        porter = nltk.PorterStemmer()
        result = [porter.stem(t) for t in result]

    return result


def create_corpus(f, X):
    "X training set, f maps email to list of words"
    corpus = {}
    for email in X:
        for word in f(email):
            corpus[word] = corpus.get(word, 0) + 1
    return corpus


def create_df(X, corpus, cleaner=clean2, tokenizer=get_words, lower=None, upper=None):
    word_freq = pd.Series(corpus).sort_values(ascending=False)
    if lower and upper:
        filt = word_freq.between(lower, upper)
        template = word_freq[filt] * 0
    elif lower:
        filt = word_freq.gt(lower)
        template = word_freq[filt] * 0
    elif upper:
        filt = word_freq.lt(upper)
        template = word_freq[filt] * 0
    else:
        template = word_freq * 0
    keys = template.keys()

    def feature_vec(mail):
        vec = template.copy()
        for x in tokenizer(cleaner(mail)):
            if x in keys:
                vec[x] = 1
        return vec

    df = pd.DataFrame({i: feature_vec(email)
                       for i, email in enumerate(X)})

    return df.T


def bisection_search(x, L):
    """Bisection search for element x in ordered list L

    :param x: object of type comparable to elements of L
    :param L: list of objects sorted in ascending order
    :returns: True if x is in L, false otherwise

    """
    if len(L) == 0:
        return False
    else:
        point = len(L) // 2
        if x == L[point]:
            return True
        elif x > L[point]:
            return bisection_search(x, L[point + 1:])
        else:
            return bisection_search(x, L[:point])


class BagOfWords(BaseEstimator, TransformerMixin):
    def __init__(self, exclude_words=[], high_rel=1.0, low_rel=0.0,
                 high_abs=None, low_abs=0, stemming=False) -> None:
        self.word_freq = None
        self.corpus = []
        self.working_word_freq = None
        self.working_corpus = []
        self.exclude_words = exclude_words
        self.max_freq = None
        self.high_rel = high_rel
        self.low_rel = low_rel
        self.high_abs = high_abs
        self.low_abs = low_abs
        self.stemming = stemming

    def fit(self, X, y=None):
        """Creates a corpus from X by extracting all words in the strings in X.
        The corpus is saved, minus any excluded words, as a Series, which has high and
        low frequency words removed.

        :param X: a list of strings
        :param y: placeholder

        """
        corpus = create_corpus(lambda x: get_words(clean2(x), stemming=self.stemming), X)

        self.word_freq = pd.Series(corpus).sort_index(ascending=True)
        self.corpus = self.word_freq.index.to_list()
        self.max_freq = self.word_freq.max()

        if self.high_abs is None:
            self.high_abs = self.max_freq + 1

        filt1 = self.word_freq.isin(self.exclude_words)
        filt2 = self.word_freq.between(max(self.low_abs, self.low_rel * self.max_freq),
                                       min(self.high_abs, self.high_rel * self.max_freq))

        self.working_word_freq = self.word_freq[~filt1 & filt2]
        self.working_corpus = self.working_word_freq.index.to_list()

        return self


    def set_filters(self, exclude_words=None,
                    high_rel=None, low_rel=None,
                    high_abs=None, low_abs=None):
        if high_rel:
            self.high_rel = high_rel
        if low_rel:
            self.low_rel = low_rel
        if high_abs:
            self.high_abs = high_abs
        if low_abs:
            self.low_abs = low_abs
        if exclude_words:
            self.exclude_words = exclude_words

        filt1 = self.word_freq.isin(self.exclude_words)
        filt2 = self.word_freq.between(max(self.low_abs, self.low_rel * self.max_freq),
                                       min(self.high_abs, self.high_rel * self.max_freq))

        self.working_word_freq = self.word_freq[~filt1 & filt2]
        self.working_corpus = self.working_word_freq.index.to_list()


    def transform(self, X, y=None):
        """Creates a one-hot encoded dataframe from the list of text X, using
        the bag of words encoding provided by self.word_freq.

        :param X: list of strings
        :param y: placeholder
        :returns: pandas dataframe with one row for each element of X

        """
        def feature_vector(text):
            """Convert a string into a one-hot encoded vector
            using the encoding provided self.word_freq

            :param text: a string
            :returns: a pandas Series with the vector encoding of the words in text

            """
            vec = self.working_word_freq * 0
            for x in get_words(clean2(text), stemming=self.stemming):
                if bisection_search(x, self.working_corpus):
                    vec[x] = 1
            return vec

        df = pd.DataFrame({i: feature_vector(x) for i, x in enumerate(X)})

        return df.T
