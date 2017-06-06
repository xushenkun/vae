import argparse
import os

import numpy as np
import torch as t
from torch.optim import Adam

from utils.batch_loader import BatchLoader
from utils.parameters import Parameters
from model.rvae_dilated import RVAE_dilated

if __name__ == "__main__":    

    parser = argparse.ArgumentParser(description='RVAE_dilated')
    parser.add_argument('--num-iterations', type=int, default=25000, metavar='NI',
                        help='num iterations (default: 25000)')
    parser.add_argument('--batch-size', type=int, default=45, metavar='BS',
                        help='batch size (default: 45)')
    parser.add_argument('--use-cuda', type=bool, default=True, metavar='CUDA',
                        help='use cuda (default: True)')
    parser.add_argument('--learning-rate', type=float, default=0.0005, metavar='LR',
                        help='learning rate (default: 0.0005)')
    parser.add_argument('--dropout', type=float, default=0.3, metavar='DR',
                        help='dropout (default: 0.3)')
    parser.add_argument('--use-trained', type=bool, default=False, metavar='UT',
                        help='load pretrained model (default: False)')
    parser.add_argument('--ppl-result', default='', metavar='CE',
                        help='ce result path (default: '')')
    parser.add_argument('--kld-result', default='', metavar='KLD',
                        help='ce result path (default: '')')

    args = parser.parse_args()

    prefix = 'poem'
    word_is_char = True

    batch_loader = BatchLoader('', prefix, word_is_char)

    if not os.path.exists('data/' + batch_loader.prefix + 'word_embeddings.npy'):
        raise FileNotFoundError("word embeddings file was't found")

    parameters = Parameters(batch_loader.max_word_len,
                            batch_loader.max_seq_len,
                            batch_loader.words_vocab_size,
                            batch_loader.chars_vocab_size, word_is_char)

    rvae = RVAE_dilated(parameters, batch_loader.prefix)
    if args.use_trained:
        rvae.load_state_dict(t.load(batch_loader.prefix+'trained_RVAE'))
    if args.use_cuda and t.cuda.is_available():
        rvae = rvae.cuda()

    optimizer = Adam(rvae.learnable_parameters(), args.learning_rate)

    train_step = rvae.trainer(optimizer, batch_loader)
    validate = rvae.validater(batch_loader)

    ppl_result = []
    kld_result = []

    for iteration in range(args.num_iterations):

        ppl, kld = train_step(iteration, args.batch_size, args.use_cuda and t.cuda.is_available(), args.dropout)
        train_ppl = ppl.data.cpu().numpy()[0]
        train_kld = kld.data.cpu().numpy()[0]
        if iteration % 10 == 0:
            print('\n')
            print('------------TRAIN-------------')
            print('----------ITERATION-----------')
            print(iteration)
            print('---------PERPLEXITY-----------')            
            print(train_ppl)
            print('-------------KLD--------------')            
            print(train_kld)
            print('------------------------------')

        if iteration % 10 == 0:
            ppl, kld = validate(args.batch_size, args.use_cuda and t.cuda.is_available())

            ppl = ppl.data.cpu().numpy()[0]
            kld = kld.data.cpu().numpy()[0]

            print('\n')
            print('------------VALID-------------')
            print('---------PERPLEXITY-----------')
            print(ppl)
            print('-------------KLD--------------')
            print(kld)
            print('------------------------------')

            ppl_result += [ppl]
            kld_result += [kld]
        print('----------ITERATION-----------%s: train_ppl[%s] train_kld[%s]'%(iteration, train_ppl, train_kld))
        if iteration % 20 == 0:
            seed = np.random.normal(size=[1, parameters.latent_variable_size])

            sample = rvae.sample(batch_loader, 50, seed, args.use_cuda and t.cuda.is_available())

            print('\n')
            print('------------SAMPLE------------')
            print(sample)
            print('------------------------------')

    t.save(rvae.state_dict(), batch_loader.prefix+'trained_RVAE')

    np.save(batch_loader.prefix+'ppl_result_{}.npy'.format(args.ppl_result), np.array(ppl_result))
    np.save(batch_loader.prefix+'kld_result_npy_{}'.format(args.kld_result), np.array(kld_result))
