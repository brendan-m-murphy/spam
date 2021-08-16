import glob
import math
import os
import pickle
import random
import re
import requests
import subprocess
import tarfile

DATA_PATH = os.path.join('..', '..', 'data')
RAW_PATH = os.path.join(DATA_PATH, 'raw')
INT_PATH = os.path.join(DATA_PATH, 'interim')

# path to reference docs
REF_PATH = os.path.join('..', '..', 'references')


def download_data():
    """
    Download Apache spamassassin data and unzip it raw data directory.
    """
    DL_ROOT = 'https://spamassassin.apache.org/old/publiccorpus'

    # get file names
    response = requests.get(DL_ROOT)
    pat = re.compile('<a href=[\'"]([\w\._]+)["\']([\w\._]+)</a>')
    links = [match.group(1)
             for match in re.finditer(pat, response.text)]

    # separate README file
    README = ""
    for i, link in enumerate(links):
        if 'readme' in link:
            README = link
            to_pop = i
            break
    if README:
        links = links.pop(to_pop)


    # get readme file
    if README:
        path = os.path.join(REF_PATH, 'readme.html')
        response = requests.get(REF_PATH + README)
        with open(path, 'wb') as f:
            f.write(response.content)

    # get email files
    def fetch_data(file_):
        """
        Download file_, write the contents to the raw data
        directory, unzip, remove .bz2 file.
        """
        DL_URL = DL_ROOT + file_
        response = requests.get(DL_URL)

        bz2_path = os.path.join(RAW_PATH, file_)
        with open(bz2_path, 'wb') as f:
            f.write(response.content)
            file_bz2 = tarfile.open(bz2_path)
            file_bz2.extractall(path=RAW_PATH)
            file_bz2.close()
        os.remove(bz2_path)

    # fetch all the remaining files
    for link in links:
        fetch_data(link)


def clean_up():
    """
    Remove by-products of file downloads.

    """

    for file in glob.glob(os.path.join(DATA_PATH, '*.bz2')):
        os.remove(file)
    for file in glob.glob(os.path.join(REF_PATH, '*.bz2')):
        os.remove(file)


#### EXTRACT DATA ####

def get_encoding(file_):
    "Use file -i to get encoding of file_"
    file_info = subprocess.run(['file', '-i', file_],
                                capture_output=True)
    file_info = file_info.stdout.decode('utf-8').split(' ')
    encoding = file_info[-1].lstrip('charset=').rstrip('\n')
    return encoding


def read_data(dir, encoding_='utf-8'):
    """
    Return a list of strings corresponding to the contents of the
    files in the directory dir, which is located in the raw data directory.

    Specify the encoding, and if this fails, try to guess the encoding.
    The guess is wrong, it seems that get_encoding tends to guess ascii
    when it should be windows-1252, so try that instead.
    """
    email = []
    PATH = os.path.join(RAW_PATH, dir)
    for file in os.listdir(PATH):
        file_path = os.path.join(PATH, file)
        try:
            with open(file_path, 'r', encoding=encoding_) as f:
                email.append(f.read())
        except LookupError:
                pass
        except UnicodeError:
            try:
                with open(file_path, 'r',
                          encoding=get_encoding(file_path)) as f:
                    email.append(f.read())
            except UnicodeError:
                try:
                    with open(file_path, 'r',
                              encoding='windows-1252') as f:
                        email.append(f.read())
                except UnicodeError:
                    pass
    return email


def extract_emails():
    """
    Return two lists containing ham and spam emails as strings.

    Note: 110 emails from the spam directories had unknown encodings
    and they are not included in the output.

    :returns: a pair of lists containing containing ham and spam emails

    """
    dirs = [dir for dir in os.listdir(RAW_PATH)
            if not dir.endswith('.txt')]
    ham_dirs = [dir for dir in dirs if 'ham' in dir]
    spam_dirs = [dir for dir in dirs if 'spam' in dir]

    ham_emails = [read_data(dir, encoding_='windows-1252')
                  for dir in ham_dirs]

    spam_emails= [read_data(dir) for dir in spam_dirs]

    ham = [email for sublist in ham_emails for email in sublist]
    spam = [email for sublist in spam_emails for email in sublist]
    return ham, spam


def pickle(obj, path, filename):
    """Pickle the object obj in the directory path with specified filename.

    :param obj: object to pickle
    :param path: string or path-like object, path to directory for output
    :param filename: string, name of pickle file output

    """
    assert(filename.endswith('.pkl'))
    with open(os.path.join(path, filename), 'wb') as f:
        pickle.dump(obj, f)


def train_test(data, ratio=0.2, shuffle=True, seed=42):
    """Split a list into training and test sets, with specified ratio.

    By default, the data is shuffled with a fixed random seed.
    The data is not mutated.

    :param data: list of data objects
    :param ratio: ratio of data to take for test set
    :param shuffle: if true, the data is shuffled before being split
    :param seed: random seed for the shuffle
    :returns: pair of lists (training set, test set)

    """
    n = len(data)
    k = math.floor(ratio * n)
    if shuffle:
        random.seed(42)
        data_shuffled = random.sample(data, k=n)
    else:
        data_shuffled = data

    return data_shuffled[:k], data_shuffled[k:]


def main():
    """Download and extract data, pickle the results.#!/usr/bin/env python

    Data is downloaded to the raw data folder, the README file is downloaded
    to references, and the ham and spam emails are split into train and test sets,
    then pickled in the interim data folder.

    """
    download_data()
    clean_up()

    ham, spam = extract_emails()
    ham_train, ham_test = train_test(ham)
    spam_train, spam_test = train_test(spam)

    pickle(ham_train, INT_PATH, 'ham_train.pkl')
    pickle(ham_test, INT_PATH, 'ham_test.pkl')
    pickle(spam_train, INT_PATH, 'spam_train.pkl')
    pickle(spam_test, INT_PATH, 'spam_test.pkl')


if __name__ == '__main__':
    main()
