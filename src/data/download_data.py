import glob, os, re, requests, tarfile


# path to raw data
DATA_PATH = os.path.join('..', '..', 'data', 'raw')

# path to reference docs
REF_PATH = os.path.join('..', '..', 'references')



def download_data():
    """Fetch links for spam and ham emails, download readme,
    download and unzip emails.

    """
    DL_ROOT = 'https://spamassassin.apache.org/old/publiccorpus/'

    # get file names
    response = requests.get(DL_ROOT)
    pat = re.compile('<a href=[\'"]([\w\._]+)["\']([\w\._]+)</a>')
    links = [match.group(1)
             for match in re.finditer(pat, response.text)]
    for i, link in enumerate(links):
        if 'readme' in link:
            README = link
            to_pop = i
            break
    links = links.pop(to_pop)

    # get readme file
    path = os.path.join(REF_PATH, 'readme.html')
    response = requests.get(DL_ROOT + README)
    with open(path, 'wb') as f:
        f.write(response.content)

    # get email files
    def fetch_data(file_name):
        bz2_path = os.path.join(DATA_PATH, file_name)
        DL_URL = DL_ROOT + file_name
        response = requests.get(DL_URL)
        with open(bz2_path, 'wb') as f:
            f.write(response.content)
            file_bz2 = tarfile.open(bz2_path)
            file_bz2.extractall(path=DATA_PATH)
            file_bz2.close()
        os.remove(bz2_path)

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


def main():
    download_data()
    clean_up()


if __name__='__main__':
    main()
