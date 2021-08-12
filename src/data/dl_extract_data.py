import glob
import os
import pickle
import re
import requests
import subprocess
import tarfile

DATA_PATH = os.path.join('..', '..', 'data')
RAW_PATH = os.path.join(DATA_PATH, 'raw')
INT_PATH = os.path.join(DATA_PATH, 'interim')

def download_data():
    """
    Download Apache spamassassin data and unzip it raw data directory.
    """
    DL_ROOT = 'https://spamassassin.apache.org/old/publiccorpus'

    # get file names
    response = requests.get(DL_ROOT)
    pat = re.compile('<a href=[\'"]([\w\._]+)["\']([\w\._]+)</a>')
    links = [match.group(1)
             for match in re.finditer(pat. response.text)]
    for i, link in enumerate(links):
        if 'readme' in link:
            README = link
            to_pop = i
            break
    links = links.pop(to_pop)


    # get readme file
    path = os.path.join(RAW_PATH, 'readme.html')
    response = requests.get(RAW_PATH + README)
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
            f.write(r.content)
            file_bz2 = tarfile.open(bz2_path)
            file_bz2.extractall(path=RAW_PATH)
            file_bz2.close()
        os.remove(bz2_path)

    # fetch all the remaining files
    for link in links:
        fetch_data(link)


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
    Return two lists, ham_emails and spam_emails,
    that contain pairs of the form (dir_name, list_of_emails),
    where dir_name is the name of a directory, and list_of_emails
    is a list of emails in that directory as strings.

    Note: 110 emails from the spam directories had unknown encodings
    and they are not included in the output.
    """
    dirs = [dir for dir in os.listdir(RAW_PATH)
            if not dir.endswith('.txt')]
    ham_dirs = [dir for dir in dirs if 'ham' in dir]
    spam_dirs = [dir for dir in dirs if 'spam' in dir]

    ham_emails = [read_data(dir, encoding_='windows-1252')
                  for dir in ham_dirs]

    spam_emails= [read_data(dir) for dir in spam_dirs]


    return list(zip(ham_dirs, ham_emails)), list(zip(spam_dirs, spam_emails))


def pickle_emails(ham, spam):
    """
    Pickle the results of extract_emails() into the interim
    data directory.
    """
    with open(os.path.join(INT_PATH, 'ham.pkl'), 'wb') as f:
        pickle.dump(ham, f)

    with open(os.path.join(INT_PATH, 'spam.pkl'), 'wb') as f:
        pickle.dump(spam, f)
