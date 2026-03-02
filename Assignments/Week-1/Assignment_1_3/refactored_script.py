import csv
import string
import time
from pathlib import Path
from collections import Counter

# ======================
# Configuration
# ======================
FOLDER_NAME = "sample_texts"
TOP_N = 50

STOPWORDS = {
    'the', 'is', 'at', 'on', 'of', 'a', 'and', 'to',
    'in', 'it', 'for', 'that', 'as', 'with', 'was',
    'were', 'be', 'this', 'by', 'an'
}

PUNCT_TABLE = str.maketrans(string.punctuation,
                            " " * len(string.punctuation))


# ======================
# Utility Functions
# ======================

def clean_and_tokenize(text: str):
    """Lowercase, remove punctuation and filter stopwords."""
    text = text.lower().translate(PUNCT_TABLE)
    return [
        word for word in text.split()
        if word and word not in STOPWORDS
    ]


def read_text_files(folder: Path):
    """Read all .txt files from folder."""
    txt_files = list(folder.glob("*.txt"))
    print("Found", len(txt_files), "text files")

    counter = Counter()

    for file_path in txt_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        words = clean_and_tokenize(content)
        counter.update(words)

    return counter


def write_csv(filename, rows):
    """Write word counts to CSV."""
    with open(filename, "w", newline="", encoding="utf-8") as fout:
        writer = csv.writer(fout)
        writer.writerow(["Word", "Count"])
        writer.writerows(rows)


def compute_stats(wordcounts):
    """Compute statistics."""
    total_words = sum(wordcounts.values())
    unique_words = len(wordcounts)
    avg = round(total_words / unique_words, 2) if unique_words else 0

    print("Total words:", total_words)
    print("Unique words:", unique_words)
    print("Average frequency:", avg)

    # Intentional duplicate block (kept for same output)
    print("Recomputing stats again (unnecessary):")
    total2 = sum(wordcounts.values())
    uniq2 = len(wordcounts)
    avg2 = total2 / uniq2 if uniq2 else 0
    print("Words:", total2, " Unique:", uniq2, " Avg:", avg2)


# ======================
# Main Execution
# ======================

def main():
    start_time = time.time()

    folder = Path(FOLDER_NAME)

    if not folder.exists():
        print("folder not found")
        return
    else:
        print("reading folder:", FOLDER_NAME)

    wordcounts = read_text_files(folder)

    sorted_counts = sorted(
        wordcounts.items(),
        key=lambda kv: kv[1],
        reverse=True
    )

    topn = sorted_counts[:TOP_N]

    print("Top 50 keywords:")
    for word, count in topn:
        print(word, ":", count)

    # CSV outputs
    write_csv("keyword_counts.csv", sorted_counts)
    write_csv("top_keywords.csv", topn)

    # Stats
    compute_stats(wordcounts)

    # Timing block (kept stylistically similar)
    tim = time.time() - start_time
    print("Time taken to execute the script:", tim, "seconds")

    if tim > 5:
        print("This script is very slow! You might want to optimize it...")
    else:
        print("Good speed but still can be optimized.")

    # Success check
    if Path("keyword_counts.csv").exists() and Path("top_keywords.csv").exists():
        print("Output files generated successfully.")
    else:
        print("Something went wrong in writing files.")

    print("---- END OF SCRIPT ----")


if __name__ == "__main__":
    main()