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
    DL_ROOT = 'https://spamassassin.apache.org/old/publiccorpus/'

    # file names
    ham_tars = ['20030228_hard_ham.tar.bz2', '20030228_easy_ham_2.tar.bz2', '20030228_easy_ham.tar.bz2']
    spam_tars = ['20050311_spam_2.tar.bz2', '20030228_spam.tar.bz2']

    # get readme file
    path = os.path.join(REF_PATH, 'readme.html')
    response = requests.get(DL_ROOT + 'readme.html')
    with open(path, 'wb') as f:
        f.write(response.content)

    # get email files
    def fetch_data(file_, extract_path=RAW_PATH):
        """
        Download file_, write the contents to the raw data
        directory, unzip, remove .bz2 file.
        """
        DL_URL = DL_ROOT + file_
        response = requests.get(DL_URL)
        bz2_path = os.path.join(RAW_PATH, file_)
        with open(bz2_path, 'wb') as f:
            f.write(response.content)
        with tarfile.open(bz2_path) as file_bz2:
            file_bz2.extractall(path=extract_path)
        os.remove(bz2_path)

    # fetch all the remaining files
    ham_extract = os.path.join(RAW_PATH, 'ham')
    os.makedirs(ham_extract, exist_ok=True)
    for link in ham_tars:
        fetch_data(link, ham_extract)

    spam_extract = os.path.join(RAW_PATH, 'spam')
    os.makedirs(spam_extract, exist_ok=True)
    for link in spam_tars:
        fetch_data(link, spam_extract)


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
            except LookupError:
                pass
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
    ham_dirs = [dir for dir in os.listdir(os.path.join(RAW_PATH, 'ham'))]
    spam_dirs = [dir for dir in os.listdir(os.path.join(RAW_PATH, 'spam'))]

    ham_emails = [read_data(os.path.join('ham', dir), encoding_='windows-1252')
                  for dir in ham_dirs]

    spam_emails= [read_data(os.path.join('spam', dir)) for dir in spam_dirs]

    ham = [email for sublist in ham_emails for email in sublist]
    spam = [email for sublist in spam_emails for email in sublist]
    return ham, spam


def pickle_data(obj, path, filename):
    """Pickle the object obj in the directory path with specified filename.

    :param obj: object to pickle
    :param path: string or path-like object, path to directory for output
    :param filename: string, name of pickle file output

    """
    assert(filename.endswith('.pkl'))
    with open(os.path.join(path, filename), 'wb') as f:
        pickle.dump(obj, f)


def train_test(data, val_ratio=0.2, test_ratio=0.2, shuffle=True, seed=42):
    """Split a list into training and test sets, with specified ratio.

    By default, the data is shuffled with a fixed random seed.
    The data is not mutated.

    :param data: list of data objects
    :param val_ratio: ratio of data to take for validation set
    :param test_ratio: ratio of data to take for test set
    :param shuffle: if true, the data is shuffled before being split
    :param seed: random seed for the shuffle
    :returns: triple of lists (training set, validation set, test set)

    """
    n = len(data)
    k_val = math.floor((1 - val_ratio - test_ratio) * n)
    k_test = math.floor((1 - test_ratio) * n)
    if shuffle:
        random.seed(42)
        data_shuffled = random.sample(data, k=n)
    else:
        data_shuffled = data

    return data_shuffled[:k_val], data_shuffled[k_val:k_test], data_shuffled[k_test:]


def main():
    """Download and extract data, pickle the results.#!/usr/bin/env python

    Data is downloaded to the raw data folder, the README file is downloaded
    to references, and the ham and spam emails are split into train and test sets,
    then pickled in the interim data folder.

    """
    download_data()

    ham, spam = extract_emails()

    ham_train, ham_val, ham_test = train_test(ham)
    spam_train, spam_val, spam_test = train_test(spam)

    pickle_data(ham_train, INT_PATH, 'ham_train.pkl')
    pickle_data(ham_val, INT_PATH, 'ham_val.pkl')
    pickle_data(ham_test, INT_PATH, 'ham_test.pkl')
    pickle_data(spam_train, INT_PATH, 'spam_train.pkl')
    pickle_data(spam_val, INT_PATH, 'spam_val.pkl')
    pickle_data(spam_test, INT_PATH, 'spam_test.pkl')



if __name__ == '__main__':
    main()
