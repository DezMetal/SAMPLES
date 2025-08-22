# EmailzToJSON - Email Log Parser

**EmailzToJSON** is a command-line utility that processes email logs from a `.zip` archive. It extracts data from text files based on a defined pattern, normalizes the data, and structures it into a clean `JSON` output file, grouped by sender.

This script is a proof-of-concept for parsing semi-structured text logs and converting them into a machine-readable format for further analysis or data ingestion.

---

## How It Works

The script follows a clear, three-step process:

1.  **Extract from Zip:** It opens an archive named `email_logs.zip` and reads all `.txt` files contained within, concatenating their contents.
2.  **Parse with Pattern:** It uses a regular expression to identify individual email entries in the text. For each entry, it applies a second, more detailed regex pattern to extract named fields: `Subject`, `Sender`, `Recipient`, `Date`, `Body`, and `Attachments`.
3.  **Normalize and Structure:** The extracted data is normalized to ensure consistency. For example, sender and recipient emails are converted to lowercase. The script then organizes the parsed emails into a dictionary, using the sender's email as the key, and appends each corresponding email object to a list under that key.
4.  **Export to JSON:** The final, structured dictionary is exported to `email_log.json`. A detailed log of the entire operation is also saved to `LOG.txt`.

## Requirements

*   Python 3
*   `alive_progress`

You can install the required package using pip:

```bash
pip install alive-progress
```

## Usage

1.  Place your archive of email logs, named `email_logs.zip`, in the project directory. The archive should contain `.txt` files with the email data. An example is provided in the repository.
2.  Run the script from your terminal:

```bash
python3 EmailZipToJSON.py
```

The script will generate two files:

*   `email_log.json`: The final, structured JSON output.
*   `LOG.txt`: A log file detailing the extraction and parsing process.

## Expected Input Format

The script's parser is built around a specific text format where fields are labeled, for example:
```
Subject: This is the subject
Sender: sender@example.com
Recipient: recipient1@example.com, recipient2@example.com
Date: 2023-10-27
Body:
This is the main content of the email.
(Attachments: file1.pdf, file2.docx)
```
The regex patterns in the script can be modified to accommodate different log formats.
