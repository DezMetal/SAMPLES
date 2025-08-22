# EmailzToJSON - Email Log Parser

**EmailzToJSON** is a Python script that extracts and parses email logs from a `.zip` archive, converts them into a structured JSON format, and exports the result.

This tool is designed to process a specific, semi-structured text format for email logs, making it easy to analyze or ingest email data into other systems. It groups emails by sender and includes details like recipients, subject, body, and attachments.

---

## How It Works

The script automates the following process:

1.  **Load Zip Archive:** It opens a specified `.zip` file (default: `email_logs.zip`) and reads the content of all `.txt` files within it.
2.  **Parse Content:** It uses regular expressions to find and parse individual email entries from the aggregated text content. It extracts the following fields:
    *   Subject
    *   Sender
    *   Recipient(s)
    *   Date
    *   Body
    *   Attachments (if any)
3.  **Structure Data:** The parsed emails are organized into a Python dictionary, where keys are the senders' email addresses.
4.  **Export to JSON:** The final dictionary is written to an `email_log.json` file.
5.  **Log Progress:** The entire process, including which files are being processed and any errors, is logged to `LOG.txt`.

## Requirements

*   Python 3
*   `alive_progress`

You can install the required package using pip:

```bash
pip install alive-progress
```

## Usage

1.  **Place your email archive** in the same directory and name it `email_logs.zip`. The archive should contain one or more `.txt` files with the email data. An example archive is included in the project.
2.  **Run the script** from your terminal:

```bash
python3 EmailZipToJSON.py
```

The script will perform the extraction and parsing, and you will find the following output files:

*   `email_log.json`: The structured email data.
*   `LOG.txt`: A detailed log of the script's execution.

## Input Format

The script expects the email logs inside the `.txt` files to have a consistent format, with fields clearly labeled (e.g., `Subject:`, `Sender:`). An example of the expected structure can be inferred from the regular expressions in the script.
