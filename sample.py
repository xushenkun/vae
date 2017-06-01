import argparse
import os

import numpy as np
import torch as t

from utils.batch_loader import BatchLoader
from utils.parameters import Parameters
from model.rvae_dilated import RVAE_dilated

if __name__ == '__main__':    

    parser = argparse.ArgumentParser(description='Sampler')
    parser.add_argument('--use-cuda', type=bool, default=True, metavar='CUDA',
                        help='use cuda (default: True)')
    parser.add_argument('--num-sample', type=int, default=10, metavar='NS',
                        help='num samplings (default: 10)')

    args = parser.parse_args()

    prefix = 'poem'
    word_is_char = True

    batch_loader = BatchLoader('', prefix, word_is_char)

    assert os.path.exists(batch_loader.prefix+'trained_RVAE'), \
        'trained model not found'

    parameters = Parameters(batch_loader.max_word_len,
                            batch_loader.max_seq_len,
                            batch_loader.words_vocab_size,
                            batch_loader.chars_vocab_size)

    rvae = RVAE_dilated(parameters)
    rvae.load_state_dict(t.load(batch_loader.prefix+'trained_RVAE'))
    if args.use_cuda and t.cuda.is_available():
        rvae = rvae.cuda()

    for iteration in range(args.num_sample):
        seed = np.random.normal(size=[1, parameters.latent_variable_size])
        result = rvae.sample(batch_loader, 50, seed, args.use_cuda and t.cuda.is_available())
        print(result)
        print()