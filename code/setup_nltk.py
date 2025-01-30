import nltk

def download_nltk_resources():
    """Download required NLTK resources"""
    resources = [
        'punkt',
        'stopwords',
        'averaged_perceptron_tagger',
        'wordnet'
    ]
    
    for resource in resources:
        try:
            nltk.download(resource)
            print(f"Successfully downloaded {resource}")
        except Exception as e:
            print(f"Error downloading {resource}: {e}")

if __name__ == "__main__":
    download_nltk_resources() 