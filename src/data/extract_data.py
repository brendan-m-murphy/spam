import os
import pickle
import subprocess

def get_encoding(file_path):
    "Use file -i to get encoding of file with path file_path"
    file_info = subprocess.run(['file', '-i', file_path],
                                capture_output=True)
    file_info = file_info.stdout.decode('utf-8').split(' ')
    encoding = file_info[-1].lstrip('charset=').rstrip('\n')
    return encoding

def read_data(dir, DATA_PATH, encoding_='utf-8'):
    """
    Return a list of strings corresponding to the contents of the
    files in the directory dir, which is located at the end of DATA_PATH.

    Specify the encoding, and if this fails, try to guess the encoding.
    The guess is wrong, it seems that get_encoding tends to guess ascii
    when it should be windows-1252, so try that instead.
    """
    email = []
    PATH = os.path.join(DATA_PATH, dir)
    for file in os.listdir(PATH):
        file_path = os.path.join(PATH, file)
        try:
            with open(file_path, 'r', encoding=encoding_) as f:
                email.append(f.read())
        except UnicodeError:
            try:
                with open(file_path, 'r',
                          encoding=get_encoding(file_path)) as f:
                    email.append(f.read())
            except LookupError as e:
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
    Return two lists, ham_emails and spam_emails,
    that contain pairs of the form (dir_name, list_of_emails),
    where dir_name is the name of a directory, and list_of_emails
    is a list of emails in that directory as strings.
    
    Note: 110 emails from the spam directories had unknown encodings
    and they are not included in the output.
    """
    DATA_PATH = os.path.join('..', '..', 'data', 'raw')

    dirs = [dir for dir in os.listdir(DATA_PATH)
            if not dir.endswith('.txt')]
    ham_dirs = [dir for dir in dirs if 'ham' in dir]
    spam_dirs = [dir for dir in dirs if 'spam' in dir]
    
    ham_emails = [read_data(dir, DATA_PATH, encoding_='windows-1252')
                  for dir in ham_dirs]

    spam_emails= [read_data(dir, DATA_PATH)
                  for dir in spam_dirs]

    
    return list(zip(ham_dirs, ham_emails)), list(zip(spam_dirs, spam_emails))


def pickle_emails(ham, spam):
    PATH = os.path.join('..', '..', 'data', 'iterim')

    with open(os.path.join(PATH, 'ham.pkl'), 'wb') as f:
        pickle.dump(ham, f)

    with open(os.path.join(PATH, 'spam.pkl'), 'wb') as f:
        pickle.dump(spam, f)
