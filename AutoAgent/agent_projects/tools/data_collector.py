import sys

def collect_data(prompt):
    data = input(prompt + ": ")
    return data

if __name__ == "__main__":
    if len(sys.argv) > 1 and (sys.argv[1] == '-h' or sys.argv[1] == '--help'):
        print("Usage: python data_collector.py <prompt1> <prompt2> ...\nEach prompt will be used to collect user input.")
        sys.exit(0)
    elif len(sys.argv) < 2:
        print("Usage: python data_collector.py <prompt1> <prompt2> ...\nEach prompt will be used to collect user input.\nUse -h or --help for more information.")
        sys.exit(1)
    collected_data = {}
    for i in range(1, len(sys.argv)):
        prompt = sys.argv[i]
        collected_data[prompt] = collect_data(prompt)
    print(collected_data)