import os
import argparse

# Get absolute path to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data directories
DATA_DIR = os.path.join(BASE_DIR, 'mimicdata')
GENERATED_DIR = os.path.join(DATA_DIR, 'processed')
CAML_DIR = os.path.join(DATA_DIR, 'caml')

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)
os.makedirs(CAML_DIR, exist_ok=True)

# Data files with absolute paths
NOTEEVENTS_FILE_PATH = os.path.join(DATA_DIR, 'NOTEEVENTS.csv')
PROCEDURES_FILE_PATH = os.path.join(DATA_DIR, 'PROCEDURES_ICD.csv')
DIAGNOSES_FILE_PATH = os.path.join(DATA_DIR, 'DIAGNOSES_ICD.csv')

# Code description files
DIAG_CODE_DESC_FILE_PATH = os.path.join(DATA_DIR, 'D_ICD_DIAGNOSES.csv')
PROC_CODE_DESC_FILE_PATH = os.path.join(DATA_DIR, 'D_ICD_PROCEDURES.csv')
ICD_DESC_FILE_PATH = os.path.join(DATA_DIR, 'ICD9_descriptions')

# Generated files
VOCAB_FILE_PATH = os.path.join(GENERATED_DIR, 'vocab.csv')
EMBED_FILE_PATH = os.path.join(GENERATED_DIR, 'vocab.embed')
CODE_FREQ_PATH = os.path.join(GENERATED_DIR, 'code_freq.csv')
CODE_DESC_VECTOR_PATH = os.path.join(GENERATED_DIR, 'code_desc_vectors.csv')

# Special tokens
PAD_SYMBOL = '<PAD>'
UNK_SYMBOL = '<UNK>'

# Constants
FULL = 'full'
TOP50 = '50'

# Debug version
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default=DATA_DIR,
                      help='Directory containing the MIMIC III data')
    parser.add_argument('--generated_dir', type=str, default=GENERATED_DIR,
                      help='Directory for storing generated data')
    parser.add_argument('--log', default="INFO", help="Logging level.")
    parser.add_argument('--random_seed', default=271, help="Random seed.")

    parser.add_argument(
        '--data_setting',
        type=str,
        default=TOP50,
        help='Data Setting (full or top50)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default='TransICD',
        help='Transformer or TransICD models'
    )

    parser.add_argument(
        '--num_epoch',
        type=int,
        default=[30, 35, 40],
        nargs='+',
        help='Number of epochs to train.'
    )

    parser.add_argument(
        '--learning_rate',
        type=float,
        default=[0.001],
        nargs='+',
        help='Initial learning rate.'
    )

    parser.add_argument(
        '--batch_size',
        type=int,
        default=8,
        help='Batch size. Must divide evenly into the dataset sizes.'
    )

    parser.add_argument(
        '--max_len',
        type=int,
        default=2500,
        help='Max Length of discharge summary'
    )

    parser.add_argument(
        '--embed_size',
        type=int,
        default=128,
        help='Embedding dimension for text token'
    )

    parser.add_argument(
        '--freeze_embed',
        action='store_true',
        default=True,
        help='Freeze CBOW embedding or fine tune'
    )

    parser.add_argument(
        '--label_attn_expansion',
        type=int,
        default=2,
        help='Expansion factor for attention model'
    )

    parser.add_argument(
        '--num_trans_layers',
        type=int,
        default=2,
        help='Number of transformer layers'
    )

    parser.add_argument(
        '--num_attn_heads',
        type=int,
        default=8,
        help='Number of transformer attention heads'
    )

    parser.add_argument(
        '--trans_forward_expansion',
        type=int,
        default=4,
        help='Factor to expand transformers hidden representation'
    )

    parser.add_argument(
        '--dropout_rate',
        type=float,
        default=0.1,
        help='Dropout rate for transformers'
    )

    args = parser.parse_args()  # '--target_kernel_size 4 8'.split()
    return args

