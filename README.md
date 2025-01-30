# Medical Billing Code Prediction

This project processes MIMIC-III clinical notes to predict medical billing codes.

## Data Access

**Important:** The data in the `mimicdata` directory is just a demo structure. To use this code with real data, you must:

1. Request access to MIMIC-III data at [PhysioNet](https://physionet.org/content/mimic3-carevue/1.4/)
2. Complete the required CITI "Data or Specimens Only Research" training
3. Sign the data use agreement
4. Download the following files and place them in the `mimicdata` directory:
   - NOTEEVENTS.csv
   - PROCEDURES_ICD.csv
   - DIAGNOSES_ICD.csv
   - D_ICD_DIAGNOSES.csv
   - D_ICD_PROCEDURES.csv
   - ICD9_descriptions

## Project Setup

1. Create a Python virtual environment:
bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install NLTK data:
```bash
python code/setup_nltk.py
```

4. Create the required directories:
```bash
python code/setup_directories.py
```

5. Configure your environment by copying the example .env file:
```bash
cp .env.example .env
```

6. Update the paths in `.env` to match your MIMIC data location:
```bash
# MIMIC Data Paths (update these paths to match your MIMIC data location)
MIMIC_NOTES_PATH=path/to/your/NOTEEVENTS.csv
MIMIC_PROCEDURES_PATH=path/to/your/PROCEDURES_ICD.csv

# Model Configuration
MODEL_SAVE_DIR=models/
LOG_DIR=logs/

# Training Parameters
BATCH_SIZE=32
NUM_WORKERS=4
LEARNING_RATE=0.001
```

## Running the Code

1. First, verify your MIMIC data setup:
```bash
python code/verify_data.py
```

2. If needed, analyze the NOTEEVENTS file structure:
```bash
python code/analyze_noteevents.py
```

3. Run the preprocessor to prepare the data:
```bash
python code/preprocessor.py
```

This will:
- Load and validate the MIMIC data files
- Extract discharge summaries from clinical notes
- Process procedures and diagnoses
- Create dataset splits for training

4. The preprocessor will create several files in `mimicdata/processed/`:
- `discharge_summaries.csv`: Processed discharge summaries
- `ALL_CODES_filtered.csv`: Combined and filtered ICD codes
- Dataset splits for training/validation/testing

## Project Structure

```
.
├── code/
│   ├── analyze_noteevents.py  # Data analysis utilities
│   ├── constants.py           # Project constants and configurations
│   ├── preprocessor.py        # Data preprocessing pipeline
│   ├── setup_directories.py   # Directory structure setup
│   ├── setup_nltk.py         # NLTK data setup
│   └── verify_data.py        # Data verification utilities
├── mimicdata/                 # Directory for MIMIC-III data files
│   ├── processed/            # Processed data outputs
│   └── caml/                 # CAML model specific data
├── models/                    # Saved model checkpoints
├── logs/                     # Training logs
└── results/                  # Evaluation results
```

## Data Requirements

The MIMIC-III dataset is large:
- NOTEEVENTS.csv should be several GB in size
- It should contain millions of clinical notes
- The category column should contain various note types including "Discharge summary"

## Troubleshooting

If you encounter issues:

1. Check your data files:
```bash
ls -lh mimicdata/
```

2. Verify file contents:
```bash
head -n 5 mimicdata/NOTEEVENTS.csv
```

3. Common issues:
- Empty or truncated data files
- Incorrect file permissions
- Missing NLTK data
- Incorrect paths in .env file

## Citation

If you use this code or MIMIC-III data in your research, please cite:

```bibtex
@article{johnson2016mimic,
  title={MIMIC-III, a freely accessible critical care database},
  author={Johnson, Alistair EW and Pollard, Tom J and Shen, Lu and Li-Wei, H Lehman and Feng, Mengling and Ghassemi, Mohammad and Moody, Benjamin and Szolovits, Peter and Celi, Leo Anthony and Mark, Roger G},
  journal={Scientific data},
  volume={3},
  number={1},
  pages={1--9},
  year={2016},
  publisher={Nature Publishing Group}
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.