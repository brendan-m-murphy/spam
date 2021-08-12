# -*- coding: utf-8 -*-
import click
import logging
from pathlib import Path
from dotenv import find_dotenv, load_dotenv


# TODO TRAIN/VAL/TEST SPLIT FUNCTION
# choose random seed?
# import random

# def train_val_test(ham, spam):
#     all_ham, all_spam = [], []
#     for x in ham:
#         all_ham.extend(x[1])
#     for x in spam:
#         all_spam.extend(x[1])

#     random.shuffle(all_ham)
#     random.shuffle(all_spam)

#     all_ham = [(x, 0) for x in all_ham]
#     all_spam = [(x, 1) for x in all_spam]

#     n_ham = len(all_ham)
#     n_spam = len(all_spam)

#     a, b = int(0.6 * n_ham), int(0.8 * n_ham)
#     c, d = int(0.6 * n_spam), int(0.8 * n_spam)

#     train = all_ham[:a] + all_spam[:c]
#     val = all_ham[a:b] + all_spam[c:d]
#     test = all_ham[b:] + all_spam[d:]

#     random.shuffle(train)
#     random.shuffle(val)
#     random.shuffle(test)

#     return train, val, test


@click.command()
@click.argument('input_filepath', type=click.Path(exists=True))
@click.argument('output_filepath', type=click.Path())
def main(input_filepath, output_filepath):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)
    logger.info('making final data set from raw data')


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
