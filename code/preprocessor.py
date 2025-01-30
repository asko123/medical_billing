import logging
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
import constants
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import re
import string
from gensim.models import Word2Vec
import multiprocessing
from collections import defaultdict, Counter
import csv
import os
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

my_stopwords = set([stopword for stopword in stopwords.words('english')])
my_stopwords.update({'admission', 'birth', 'date', 'discharge', 'service', 'sex', 'patient', 'name'

                        , 'history',
                     'hospital', 'last', 'first', 'course', 'past', 'day', 'one', 'family', 'chief', 'complaint'})
stemmer = SnowballStemmer('english')
punct = string.punctuation.replace('-', '') + ''.join(["``", "`", "..."])
trantab = str.maketrans(punct, len(punct) * ' ')


# Credit: https://github.com/jamesmullenbach/caml-mimic
def reformat(code, is_diag):
    """
        Put a period in the right place because the MIMIC-3 data files exclude them.
        Generally, procedure codes have dots after the first two digits,
        while diagnosis codes have dots after the first three digits.
    """
    code = ''.join(code.split('.'))
    if is_diag:
        if code.startswith('E'):
            if len(code) > 4:
                code = code[:4] + '.' + code[4:]
        else:
            if len(code) > 3:
                code = code[:3] + '.' + code[3:]
    else:
        code = code[:2] + '.' + code[2:]
    return code


def combine_diag_proc_codes(hadm_id_set, out_filename='ALL_CODES_filtered.csv'):
    logging.info("Started Preprocessing raw MIMIC-III data")
    diag_df = pd.read_csv(constants.DIAGNOSES_FILE_PATH, dtype={"ICD9_CODE": str})
    proc_df = pd.read_csv(constants.PORCEDURES_FILE_PATH, dtype={"ICD9_CODE": str})

    diag_df['ICD9_CODE'] = diag_df['ICD9_CODE'].apply(lambda code: str(reformat(str(code), True)))
    proc_df['ICD9_CODE'] = proc_df['ICD9_CODE'].apply(lambda code: str(reformat(str(code), False)))
    codes_df = pd.concat([diag_df, proc_df], ignore_index=True)
    num_original_hadm_id = len(codes_df['HADM_ID'].unique())
    logging.info(f'Total unique HADM_ID (original): {num_original_hadm_id}')

    codes_df = codes_df[codes_df['HADM_ID'].isin(hadm_id_set)]
    codes_df.sort_values(['SUBJECT_ID', 'HADM_ID'], inplace=True)
    num_filtered_hadm_id = len(codes_df['HADM_ID'].unique())
    logging.info(f'Total unique HADM_ID (ALL_CODES_filtered): {num_filtered_hadm_id}')
    num_unique_codes = len(codes_df['ICD9_CODE'].unique())
    logging.info(f'Total unique ICD9_CODE (ALL_CODES_filtered): {num_unique_codes}')
    codes_df.to_csv(f'{constants.GENERATED_DIR}/{out_filename}', index=False,
               columns=['SUBJECT_ID', 'HADM_ID', 'ICD9_CODE'],
               header=['SUBJECT_ID', 'HADM_ID', 'ICD9_CODE'])

    return out_filename


def clean_text(text, trantab, my_stopwords=None, stemmer=None):
    text = text.lower().translate(trantab)
    tokens = text.strip().split()

    if stemmer:
        tokens = [stemmer.stem(t) for t in tokens]

    tokens = [token for token in tokens if not token.isnumeric() and len(token) > 2]

    if my_stopwords:
        tokens = [x for x in tokens if x not in my_stopwords]

    text = ' '.join(tokens)
    text = re.sub('-', '', text)
    text = re.sub('\d+\s', ' ', text)
    text = re.sub('\d', 'n', text)
    return text


def load_mimic_data():
    """Load MIMIC data from CSV files"""
    try:
        notes_path = os.getenv('MIMIC_NOTES_PATH')
        procedures_path = os.getenv('MIMIC_PROCEDURES_PATH')
        
        # Convert relative paths to absolute if needed
        if not os.path.isabs(notes_path):
            notes_path = os.path.abspath(os.path.join(os.getcwd(), notes_path))
        if not os.path.isabs(procedures_path):
            procedures_path = os.path.abspath(os.path.join(os.getcwd(), procedures_path))
        
        print(f"\nLoading data from:")
        print(f"NOTEEVENTS: {notes_path}")
        print(f"PROCEDURES: {procedures_path}")
        
        # Load NOTEEVENTS with detailed column info
        notes_df = pd.read_csv(notes_path)
        print("\nNOTEEVENTS.csv info:")
        print(f"Shape: {notes_df.shape}")
        print("\nColumns (with sample values):")
        for col in notes_df.columns:
            print(f"\n{col}:")
            print(f"  Type: {notes_df[col].dtype}")
            print(f"  Null values: {notes_df[col].isnull().sum()}")
            print(f"  Sample unique values: {notes_df[col].unique()[:5]}")
        
        # Load PROCEDURES
        procedures_df = pd.read_csv(procedures_path)
        print(f"\nPROCEDURES.csv info:")
        print(f"Shape: {procedures_df.shape}")
        print(f"Columns: {procedures_df.columns.tolist()}")
        
        return notes_df, procedures_df
    except Exception as e:
        print(f"\nError loading MIMIC data: {str(e)}")
        print("\nDebug information:")
        print(f"Current working directory: {os.getcwd()}")
        print(f"NOTEEVENTS path: {notes_path}")
        print(f"PROCEDURES path: {procedures_path}")
        raise


def validate_data_files():
    """Validate that required data files exist"""
    required_files = [
        constants.NOTEEVENTS_FILE_PATH,
        constants.PROCEDURES_FILE_PATH,
        constants.DIAGNOSES_FILE_PATH,
        constants.DIAG_CODE_DESC_FILE_PATH,
        constants.PROC_CODE_DESC_FILE_PATH,
        constants.ICD_DESC_FILE_PATH
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("\nError: Missing required MIMIC files:")
        for file in missing_files:
            print(f"- {file}")
        print("\nPlease ensure all required MIMIC files are in the correct location.")
        raise FileNotFoundError("Missing required MIMIC files")


def write_discharge_summaries():
    """Process and write discharge summaries"""
    notes_df, _ = load_mimic_data()
    
    print("\nDataset Overview:")
    print(f"Total number of notes: {len(notes_df)}")
    
    # Print all column names for debugging
    print("\nColumns in NOTEEVENTS.csv:")
    for col in notes_df.columns:
        print(f"- {col}")
        if col.lower() in ['category', 'description']:
            print(f"\nUnique values in {col}:")
            print(notes_df[col].value_counts().head(10))
    
    # Try to find any column that might contain category information
    category_like_cols = [col for col in notes_df.columns 
                         if any(term in col.upper() 
                               for term in ['CATEGORY', 'TYPE', 'CLASS', 'DESC'])]
    
    if category_like_cols:
        print("\nFound columns that might contain category information:")
        for col in category_like_cols:
            print(f"\n{col}:")
            print("Sample values:")
            print(notes_df[col].value_counts().head(10))
    
    # Determine which column to use for categories
    if 'category' in notes_df.columns:
        category_col = 'category'
    elif 'CATEGORY' in notes_df.columns:
        category_col = 'CATEGORY'
    elif 'category_description' in notes_df.columns:
        category_col = 'category_description'
    elif 'CATEGORY_DESCRIPTION' in notes_df.columns:
        category_col = 'CATEGORY_DESCRIPTION'
    elif 'description' in notes_df.columns:
        category_col = 'description'
    elif 'DESCRIPTION' in notes_df.columns:
        category_col = 'DESCRIPTION'
    else:
        raise KeyError(
            "Could not find category column in NOTEEVENTS.csv.\n"
            f"Available columns: {notes_df.columns.tolist()}\n"
            "Expected one of: CATEGORY, CATEGORY_DESCRIPTION, or DESCRIPTION"
        )
    
    print(f"\nUsing {category_col} column to identify discharge summaries")
    
    # Select discharge summaries - try different possible category values
    possible_categories = [
        'discharge summary',
        'discharge summaries',
        'discharge',
        'summary',
        'Discharge summary',
        'Discharge Summary',
        'DISCHARGE SUMMARY',
        'Discharge note',
        'Discharge Report'
    ]
    
    # Print all unique categories before filtering
    print(f"\nAll unique values in {category_col} column:")
    print(notes_df[category_col].value_counts())
    
    # Try case-insensitive matching
    pattern = '|'.join(possible_categories)
    print(f"\nLooking for categories matching pattern: {pattern}")
    
    # Filter for discharge summaries
    disch_df = notes_df[notes_df[category_col].str.contains(pattern, case=False, na=False)]
    
    if len(disch_df) == 0:
        print("\nWarning: No discharge summaries found!")
        print(f"\nSample of available categories in {category_col}:")
        print(notes_df[category_col].value_counts().head(20))
        
        # Try to find any similar categories
        print("\nSearching for similar categories...")
        all_categories = notes_df[category_col].unique()
        similar_found = [cat for cat in all_categories 
                        if any(term.lower() in str(cat).lower() 
                              for term in ['discharge', 'summary', 'report'])]
        if similar_found:
            print("\nFound similar categories:")
            for cat in similar_found:
                print(f"- {cat}")
        
        raise ValueError("No discharge summaries found in the dataset")
    
    print(f"\nFound {len(disch_df)} discharge summaries")
    print("\nSample of found discharge summaries:")
    print(disch_df[[category_col, 'text']].head())
    
    # Sort by HADM_ID and CHARTDATE/CHARTTIME to get the latest note for each admission
    if 'CHARTDATE' in disch_df.columns:
        sort_col = 'CHARTDATE'
    elif 'CHARTTIME' in disch_df.columns:
        sort_col = 'CHARTTIME'
    else:
        raise KeyError("Could not find CHARTDATE or CHARTTIME column in NOTEEVENTS.csv")
    
    # Sort and get latest note for each admission
    disch_df = disch_df.sort_values(['HADM_ID', sort_col]).groupby('HADM_ID').last().reset_index()
    
    # Create output directory if it doesn't exist
    os.makedirs('mimicdata/processed', exist_ok=True)
    
    # Write processed discharge summaries
    output_filename = 'mimicdata/processed/discharge_summaries.csv'
    disch_df.to_csv(output_filename, index=False)
    
    print(f"\nWrote {len(disch_df)} discharge summaries to {output_filename}")
    
    # Return set of HADM_IDs and filename
    return set(disch_df['HADM_ID'].unique()), output_filename


def process_procedures():
    """Process procedures data"""
    _, procedures_df = load_mimic_data()
    
    # Group procedures by admission
    proc_by_admission = procedures_df.groupby('HADM_ID')['ICD9_CODE'].apply(list).reset_index()
    
    # Write processed procedures
    output_filename = 'mimicdata/processed/procedures_by_admission.csv'
    proc_by_admission.to_csv(output_filename, index=False)
    
    return proc_by_admission


def create_datasets(hadm_ids, split_ratios=[0.7, 0.1, 0.2]):
    """Create train/dev/test splits"""
    hadm_ids = list(hadm_ids)
    np.random.shuffle(hadm_ids)
    
    # Calculate split points
    train_end = int(len(hadm_ids) * split_ratios[0])
    dev_end = int(len(hadm_ids) * (split_ratios[0] + split_ratios[1]))
    
    # Split data
    train_ids = hadm_ids[:train_end]
    dev_ids = hadm_ids[train_end:dev_end]
    test_ids = hadm_ids[dev_end:]
    
    # Create output directory
    os.makedirs('mimicdata/caml', exist_ok=True)
    
    # Write full splits
    pd.Series(train_ids).to_csv('mimicdata/caml/train_full_hadm_ids.csv', index=False)
    pd.Series(dev_ids).to_csv('mimicdata/caml/dev_full_hadm_ids.csv', index=False)
    pd.Series(test_ids).to_csv('mimicdata/caml/test_full_hadm_ids.csv', index=False)
    
    # Write 50% splits
    pd.Series(train_ids[:len(train_ids)//2]).to_csv('mimicdata/caml/train_50_hadm_ids.csv', index=False)
    pd.Series(dev_ids[:len(dev_ids)//2]).to_csv('mimicdata/caml/dev_50_hadm_ids.csv', index=False)
    pd.Series(test_ids[:len(test_ids)//2]).to_csv('mimicdata/caml/test_50_hadm_ids.csv', index=False)


def build_vocab(train_full_filename='train_full.csv', out_filename='vocab.csv'):
    train_df = pd.read_csv(f'{constants.GENERATED_DIR}/{train_full_filename}')
    desc_dt = load_code_desc()
    desc_series = pd.Series(list(desc_dt.values())).apply(lambda text: clean_text(text, trantab, my_stopwords, stemmer))

    full_text_series = train_df['TEXT'].append(desc_series, ignore_index=True)
    cv = CountVectorizer(min_df=1)
    cv.fit(full_text_series)

    out_file_path = f'{constants.GENERATED_DIR}/{out_filename}'
    with open(out_file_path, 'w') as fout:
        for word in cv.get_feature_names():
            fout.write(f'{word}\n')


def load_code_desc():
    desc_dict = defaultdict(str)
    with open(constants.DIAG_CODE_DESC_FILE_PATH, 'r') as descfile:
        r = csv.reader(descfile)
        #header
        next(r)
        for row in r:
            code = row[1]
            desc = row[-1]
            desc_dict[reformat(code, True)] = desc
    with open(constants.PROC_CODE_DESC_FILE_PATH, 'r') as descfile:
        r = csv.reader(descfile)
        #header
        next(r)
        for row in r:
            code = row[1]
            desc = row[-1]
            if code not in desc_dict.keys():
                desc_dict[reformat(code, False)] = desc
    with open(constants.ICD_DESC_FILE_PATH, 'r') as labelfile:
        for i,row in enumerate(labelfile):
            row = row.rstrip().split()
            code = row[0]
            if code not in desc_dict.keys():
                desc_dict[code] = ' '.join(row[1:])
    return desc_dict


def embed_words(disch_full_filename='disch_full.csv', embed_size=128, out_filename='disch_full.w2v'):
    disch_df = pd.read_csv(f'{constants.GENERATED_DIR}/{disch_full_filename}')
    sentences = [text.split() for text in disch_df['TEXT']]
    desc_dt = load_code_desc()
    for desc in desc_dt.values():
        sentences.append(clean_text(desc, trantab, my_stopwords, stemmer).split())

    num_cores = multiprocessing.cpu_count()
    min_count = 0
    window = 5
    num_negatives = 5
    logging.info('\n**********************************************\n')
    logging.info('Training CBOW embedding...')
    logging.info(f'Params: embed_size={embed_size}, workers={num_cores-1}, min_count={min_count}, window={window}, negative={num_negatives}')
    w2v_model = Word2Vec(min_count=min_count, window=window, size=embed_size, negative=num_negatives, workers=num_cores-1)
    w2v_model.build_vocab(sentences, progress_per=10000)
    w2v_model.train(sentences, total_examples=w2v_model.corpus_count, epochs=30, report_delay=1)
    w2v_model.init_sims(replace=True)
    w2v_model.save(f'{constants.GENERATED_DIR}/{out_filename}')
    logging.info('\n**********************************************\n')
    return out_filename


def map_vocab_to_embed(vocab_filename='vocab.csv', embed_filename='disch_full.w2v', out_filename='vocab.embed'):
    model = Word2Vec.load(f'{constants.GENERATED_DIR}/{embed_filename}')
    wv = model.wv
    del model

    embed_size = len(wv.word_vec(wv.index2word[0]))
    word_to_idx = {}
    with open(f'{constants.GENERATED_DIR}/{vocab_filename}', 'r') as fin, open(f'{constants.GENERATED_DIR}/{out_filename}', 'w') as fout:
        pad_embed = np.zeros(embed_size)
        unk_embed = np.random.randn(embed_size)
        unk_embed_normalized = unk_embed / float(np.linalg.norm(unk_embed) + 1e-6)
        fout.write(constants.PAD_SYMBOL + ' ' + np.array2string(pad_embed, max_line_width=np.inf, separator=' ')[1:-1] + '\n')
        fout.write(constants.UNK_SYMBOL + ' ' + np.array2string(unk_embed_normalized, max_line_width=np.inf, separator=' ')[1:-1] + '\n')
        word_to_idx[constants.PAD_SYMBOL] = 0
        word_to_idx[constants.UNK_SYMBOL] = 1

        for line in fin:
            word = line.strip()
            word_embed = wv.word_vec(word)
            fout.write(word + ' ' + np.array2string(word_embed, max_line_width=np.inf, separator=' ')[1:-1] + '\n')
            word_to_idx[word] = len(word_to_idx)

    logging.info(f'Size of training vocabulary (including PAD, UNK): {len(word_to_idx)}')
    return word_to_idx


def vectorize_code_desc(word_to_idx, out_filename='code_desc_vectors.csv'):
    desc_dict = load_code_desc()
    with open(f'{constants.GENERATED_DIR}/{out_filename}', 'w') as fout:
        w = csv.writer(fout, delimiter=' ')
        w.writerow(["CODE", "VECTOR"])
        for code, desc in desc_dict.items():
            tokens = clean_text(desc, trantab, my_stopwords, stemmer).split()
            inds = [word_to_idx[t] if t in word_to_idx.keys() else word_to_idx[constants.UNK_SYMBOL] for t in tokens]
            w.writerow([code] + [str(i) for i in inds])


def inspect_noteevents():
    """Helper function to inspect NOTEEVENTS.csv structure"""
    try:
        print(f"\nAttempting to inspect: {constants.NOTEEVENTS_FILE_PATH}")
        
        # Check if file exists
        if not os.path.exists(constants.NOTEEVENTS_FILE_PATH):
            print(f"Error: File not found at {constants.NOTEEVENTS_FILE_PATH}")
            return
        
        # Check file size
        file_size = os.path.getsize(constants.NOTEEVENTS_FILE_PATH)
        print(f"File size: {file_size / (1024*1024):.2f} MB")
        
        if file_size == 0:
            print("Error: File is empty")
            return
        
        # Try to read the file header
        print("\nFile header:")
        with open(constants.NOTEEVENTS_FILE_PATH, 'r') as f:
            header = f.readline().strip()
            print(header)
        
        # Load the data
        notes_df = pd.read_csv(constants.NOTEEVENTS_FILE_PATH)
        print("\nNOTEEVENTS.csv structure:")
        print(f"\nShape: {notes_df.shape}")
        print("\nColumns:")
        for col in notes_df.columns:
            print(f"- {col}")
            n_nulls = notes_df[col].isnull().sum()
            n_unique = notes_df[col].nunique()
            print(f"  Null values: {n_nulls}")
            print(f"  Unique values: {n_unique}")
        
        # Try to find category-like columns
        category_cols = [col for col in notes_df.columns if 'CATEGORY' in col.upper() or 'TYPE' in col.upper() or 'DESC' in col.upper()]
        if category_cols:
            print("\nPossible category columns found:")
            for col in category_cols:
                print(f"\n{col} sample values:")
                print(notes_df[col].value_counts().head())
        
        print(f"\nTotal notes: {len(notes_df)}")
        
    except Exception as e:
        print(f"Error inspecting NOTEEVENTS.csv: {e}")
        print("\nDebug information:")
        print(f"Current working directory: {os.getcwd()}")
        print(f"File path: {constants.NOTEEVENTS_FILE_PATH}")


def main():
    """Main preprocessing pipeline"""
    print("Inspecting NOTEEVENTS structure...")
    inspect_noteevents()
    
    print("\nProcessing discharge summaries...")
    hadm_id_set, disch_filename = write_discharge_summaries()
    
    print("\nProcessing procedures...")
    proc_by_admission = process_procedures()
    
    print("\nCreating dataset splits...")
    create_datasets(hadm_id_set)
    
    print("\nPreprocessing complete!")


if __name__ == "__main__":
    if not os.path.exists('../results'):
        os.makedirs('../results')
    args = constants.get_args()
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(filename='../results/preprocess.log', filemode='w', format=FORMAT, level=logging.INFO)
    main()

