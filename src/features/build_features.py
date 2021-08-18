import email
import nltk
import pandas as pd
import re
from sklearn.base import BaseEstimator, TransformerMixin


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


class BagOfWords(BaseEstimator, TransformerMixin):
    def __init__(self, exclude_words=[], high=1.0, low=0.0, stemming=False) -> None:
        self.word_freq = None
        self.corpus = []
        self.exclude_words = exclude_words
        self.high = high
        self.low = low
        self.stemming = stemming

    def fit(self, X, y=None):
        """Creates a corpus from X by extracting all words in the strings in X.
        The corpus is saved, minus any excluded words, as a Series, which has high and
        low frequency words removed.

        :param X: a list of strings
        :param y: placeholder

        """
        corpus = create_corpus(lambda x: get_words(clean2(x), stemming=self.stemming), X)
        for word in self.exclude_words:
            if word in corpus:
                del corpus[word]

        word_freq = pd.Series(corpus)
        filt = word_freq.betwee(self.low, self.high)
        self.word_freq = word_freq[filt]

        self.corpus = self.word_freq.index.to_list()


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

            vec = self.word_freq * 0
            for x in get_words(clean2(text), stemming=self.stemming):
                if x in self.corpus:
                    vec[x] = 1
            return vec

        df = pd.DataFrame({i: feature_vector(x) for i, x in enumerate(X)})

        return df.T
