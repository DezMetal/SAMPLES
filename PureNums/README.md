# ⚛️ PureNums - Quantum Number Generator

PureNums is a command-line tool that generates verifiably random numbers sourced from the quantum vacuum. It uses the Australian National University's (ANU) Quantum Random Numbers API to fetch true random data and purifies it through cryptographic hashing to ensure statistical uniformity and remove any potential bias.

The tool also includes a validation module to statistically compare the generated numbers against a large benchmark dataset, providing confidence in their randomness.

---

## Features

*   **True Quantum Randomness:** Sources entropy directly from the ANU Quantum Numbers API.
*   **Cryptographic Purification:** Uses SHA-256 hashing to "purify" the raw quantum data, ensuring a uniform, unbiased distribution.
*   **Flexible Set Generation:** Create multiple sets of unique random numbers with customizable size and maximum values.
*   **Statistical Validation:** Includes a validator that runs Chi-Squared and Runs tests to check for consistency with a trusted random number benchmark.
*   **Verbose Logging:** Provides detailed, color-coded logs to trace the entire process from API call to final output.

---
## Portfolio Highlight

### Use Cases
*   **Cryptography & Security:** Generate high-quality random numbers for cryptographic keys, security tokens, or initialization vectors.
*   **Scientific Simulations:** Provide a source of true, non-deterministic randomness for Monte Carlo simulations and other scientific models.
*   **Gaming & Lotteries:** Create verifiably fair and unpredictable results for lottery number generation, prize drawings, or procedural content generation in games.
*   **Data Science:** Generate random samples from a dataset for statistical analysis or machine learning model training.

### Proof of Concept
This project is a proof of concept for a **verifiable, high-entropy random number generation pipeline**. It demonstrates:
*   **Entropy Sourcing:** The ability to consume data from an external, hardware-based entropy source via a REST API (ANU Quantum Random Numbers).
*   **Cryptographic Purification:** The application of a cryptographic hash function (SHA-256) as a randomness extractor. This "purifies" the raw quantum data, smoothing out any potential statistical biases from the source and protecting against flaws in the source generator.
*   **Statistical Validation:** A robust validation module that uses statistical tests (Chi-Squared for distribution, Wald-Wolfowitz runs test for clustering) to compare the generated numbers against a trusted benchmark dataset, providing confidence in their quality.
*   **Efficient Data Handling:** The script intelligently calculates the required amount of entropy needed upfront to minimize API calls and efficiently generates numbers from a pre-fetched bitstream.

### Hireable Skills
*   **Python Development:** Building robust, command-line interface (CLI) applications with `argparse`.
*   **API Integration:** Consuming data from external REST APIs and handling API keys securely.
*   **Data Analysis & Statistics:** Using libraries like `pandas` and `numpy` to perform statistical tests (Chi-Squared, Runs Test) for data validation.
*   **Cryptography Concepts:** Practical application of cryptographic hashing (SHA-256) for randomness extraction and data purification.
*   **Algorithm Design:** Developed a clear pipeline for fetching, processing, and validating data.

---

## How It Works

1.  **Estimate Entropy:** The tool first calculates the estimated amount of random bits required to fulfill the user's request, accounting for the probability of rejection sampling.
2.  **Fetch Raw Data:** It makes a single, efficient API call to the ANU service to acquire the necessary quantum data in hexadecimal format.
3.  **Purify Stream:** The raw hex data is processed in chunks. Each chunk is hashed using SHA-256, and the resulting digest is converted into a binary bit stream. This process removes any potential statistical anomalies from the source.
4.  **Generate Numbers:** The tool draws bits from the purified stream to construct numbers within the desired range. It ensures all numbers within a set are unique.
5.  **Validate (Optional):** If requested, the final number sets are passed to the `BenchmarkValidator`, which compares their statistical properties (frequency, clustering) against a pre-supplied benchmark dataset (`randNorm100k.csv`).

---

## Setup and Usage

### 1. Prerequisites

*   Python 3.6+
*   An API key from the [ANU Quantum Random Numbers API](https://quantumnumbers.anu.edu.au/).

### 2. Installation

First, clone the repository and navigate into the `PureNums` directory. It is recommended to use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 3. Running the Generator

Run the `main.py` script from the command line. You must provide your ANU API key.

```bash
python main.py --api-key YOUR_SECRET_API_KEY_HERE [OPTIONS]
```

**Key Arguments:**

*   `--api-key`: Your secret API key.
*   `--sets`: The number of unique sets to generate (e.g., `5`).
*   `--size`: The size of each number set (e.g., `6`).
*   `--max`: The maximum value for any single number (e.g., `49`).
*   `--validate`: If set, runs the benchmark validation on the generated sets.
*   `--quiet`: Suppresses detailed logging and only prints the final numbers.

---

## Examples

**Example 1: Generate a single lottery-style number set**

This will generate one set of 7 numbers, with a maximum value of 59.

```bash
python main.py --api-key YOUR_KEY --sets 1 --size 7 --max 59
```

**Example 2: Generate 5 sets and validate them**

This will generate five sets of 10 numbers (max value 100) and run a statistical validation against `randNorm100k.csv`.

```bash
python main.py --api-key YOUR_KEY --sets 5 --size 10 --max 100 --validate
```
