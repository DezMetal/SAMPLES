import requests
import hashlib
import textwrap
import math
import time
import argparse
import sys

# It's common to import the class from a separate file.
# Ensure validator.py is in the same directory.
from validator import BenchmarkValidator

class Color:
    """A helper class for adding color to terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class QuantumNumberGenerator:
    """
    Generates verifiably random numbers using quantum entropy from the ANU API,
    purified with cryptographic hashing to ensure statistical uniformity.
    """
    API_URL = "https://api.quantumnumbers.anu.edu.au"
    MAX_API_LENGTH = 1024

    def __init__(self, api_key, verbose=True):
        if not api_key or "YOUR_SECRET_API_KEY_HERE" in api_key:
            raise ValueError("API Key is missing. Please provide a valid key.")
        self.api_key = api_key
        self.verbose = verbose
        self.bit_stream = ""

    def _log(self, message, color=Color.ENDC):
        if self.verbose:
            # Use textwrap for clean formatting and apply color
            print(textwrap.fill(f"{color}{message}{Color.ENDC}", width=80))

    def _acquire_raw_entropy(self, length=128):
        self._log(f"[API CALL] Making a single request for {length} blocks of raw quantum data...", color=Color.CYAN)
        params = {"length": length, "type": "hex16", "size": 2}
        headers = {"x-api-key": self.api_key}
        try:
            response = requests.get(self.API_URL, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("success"):
                hex_string = "".join(data["data"])
                self._log(f"[SUCCESS] Acquired {len(hex_string)} raw hexadecimal characters.", color=Color.GREEN)
                return hex_string
            else:
                self._log(f"[FAILURE] API call was not successful: {data.get('message')}", color=Color.FAIL)
                return None
        except requests.exceptions.RequestException as e:
            self._log(f"[FAILURE] An error occurred during API call: {e}", color=Color.FAIL)
            return None

    def _purify_chunk(self, hex_chunk):
        raw_bytes = bytes.fromhex(hex_chunk)
        hasher = hashlib.sha256(raw_bytes)
        purified_hex = hasher.hexdigest()
        return bin(int(purified_hex, 16))[2:].zfill(256)

    def _prefetch_and_build_stream(self, num_sets, set_size, max_val):
        self._log("\n" + "="*60, color=Color.HEADER)
        self._log("  STEP 1: PRE-FETCHING & PURIFYING ENTROPY", color=Color.HEADER)
        self._log("="*60, color=Color.HEADER)
        self._log("Calculating the total amount of random data needed for the request.")
        bits_per_num = (max_val - 1).bit_length()
        prob_success = max_val / (2**bits_per_num)
        total_numbers_needed = num_sets * set_size
        expected_attempts = (total_numbers_needed / prob_success) * 1.5 * 1.2
        total_bits_needed = math.ceil(expected_attempts * bits_per_num)
        self._log(f"Estimated purified bits required: {Color.BOLD}{total_bits_needed}{Color.ENDC}")

        purification_cycles_needed = math.ceil(total_bits_needed / 256)
        HEX_CHARS_PER_HASH = 128
        total_hex_chars_needed = purification_cycles_needed * HEX_CHARS_PER_HASH
        api_length_needed = math.ceil(total_hex_chars_needed / 4)
        self._log(f"This requires an API 'length' parameter of {Color.BOLD}{api_length_needed}{Color.ENDC}.")

        if api_length_needed > self.MAX_API_LENGTH:
            self._log(f"[WARNING] Request is too large for a single API call. Fetching maximum allowed ({self.MAX_API_LENGTH} blocks).", color=Color.WARNING)
            api_length_to_fetch = self.MAX_API_LENGTH
        else:
            api_length_to_fetch = api_length_needed

        raw_hex_data = self._acquire_raw_entropy(length=api_length_to_fetch)
        if not raw_hex_data:
            raise Exception("Failed to acquire any entropy from the API.")

        self._log("\n[PURIFYING] Processing the entire raw data batch...", color=Color.BLUE)
        num_hashes = len(raw_hex_data) // HEX_CHARS_PER_HASH
        for i in range(num_hashes):
            start = i * HEX_CHARS_PER_HASH
            end = start + HEX_CHARS_PER_HASH
            hex_chunk = raw_hex_data[start:end]
            self.bit_stream += self._purify_chunk(hex_chunk)
        self._log(f"[SUCCESS] Entropy pre-fetch complete. Final purified bit stream has {len(self.bit_stream)} bits.", color=Color.GREEN)

    def generate_unique_sets(self, num_sets, set_size, max_val):
        if set_size > max_val:
            raise ValueError(f"Impossible request: Set size ({set_size}) cannot be larger than the maximum value ({max_val}).")
        self._prefetch_and_build_stream(num_sets, set_size, max_val)

        self._log("\n" + "="*60, color=Color.HEADER)
        self._log(f"  STEP 2: GENERATING {num_sets} SETS", color=Color.HEADER)
        self._log("="*60, color=Color.HEADER)
        self._log(f"Pouring numbers from the bit stream into unique sets of {set_size}. Repeats within a single set are discarded.")

        all_sets = []
        bits_needed = (max_val - 1).bit_length()
        while len(all_sets) < num_sets:
            current_set = set()
            while len(current_set) < set_size:
                if len(self.bit_stream) < bits_needed:
                    self._log("\n[WARNING] Ran out of entropy before all requested sets could be completed.", color=Color.WARNING)
                    return all_sets
                bit_chunk = self.bit_stream[:bits_needed]
                self.bit_stream = self.bit_stream[bits_needed:]
                num = int(bit_chunk, 2)
                if num < max_val:
                    value = num + 1
                    if value not in current_set:
                        current_set.add(value)
            all_sets.append(list(current_set))
        self._log(f"\n[COMPLETE] Successfully generated {len(all_sets)} complete sets.", color=Color.GREEN)
        return all_sets

def main():
    parser = argparse.ArgumentParser(
        description="Generates purified random number sets from quantum entropy.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('--api-key', default="oh45ihpbug54sk1852zQna87KmutGZ6yaaexrQ85", help="Your secret API key from quantumnumbers.anu.edu.au.\n(Required for security and to prevent unauthorized use.)")
    parser.add_argument('--sets', type=int, default=1, help="The number of unique sets to generate. Default: 1")
    parser.add_argument('--size', type=int, default=7, help="The size of each unique number set. Default: 7")
    parser.add_argument('--max', type=int, default=59, help="The maximum value for any single number. Default: 59")
    parser.add_argument('--validate', action='store_true', help="If set, validates each generated set against the benchmark CSV.")
    parser.add_argument('--benchmark-file', default='randNorm100k.csv', help="Path to the benchmark CSV file for validation. Default: randNorm100k.csv")
    parser.add_argument('--quiet', action='store_true', help="If set, suppresses detailed logging and only prints the final numbers.")

    # A simple check for color support
    is_color_supported = sys.stdout.isatty()

    args = parser.parse_args()

    try:
        is_verbose = not args.quiet
        generator = QuantumNumberGenerator(api_key=args.api_key, verbose=is_verbose)
        final_sets = generator.generate_unique_sets(
            num_sets=args.sets,
            set_size=args.size,
            max_val=args.max
        )

        # --- Pretty Print Results ---
        header = "  Your Purified Quantum Random Number Sets  "
        print("\n" + f"{Color.HEADER}╔{'═' * (len(header))}╗{Color.ENDC}")
        print(f"{Color.HEADER}║{Color.BOLD}{header}{Color.ENDC}{Color.HEADER}║{Color.ENDC}")
        print(f"{Color.HEADER}╚{'═' * (len(header))}╝{Color.ENDC}")

        if not final_sets:
            print(f"  {Color.WARNING}No complete sets were generated with the available entropy.{Color.ENDC}")
        else:
            for i, num_set in enumerate(final_sets):
                set_str = ", ".join(map(str, sorted(num_set)))
                print(f"  {Color.BOLD}Set {i+1:<2}:{Color.ENDC} {set_str}")

        if args.validate:
            print("\n" + "─"*40)
            validator = BenchmarkValidator(benchmark_filepath=args.benchmark_file, verbose=is_verbose)
            for i, num_set in enumerate(final_sets):
                validator.validate_new_set(new_data=num_set, set_number=i+1)

    except (ValueError, Exception) as e:
        print(f"\n{Color.FAIL}[ERROR] An error occurred: {e}{Color.ENDC}")

if __name__ == "__main__":
    main()
