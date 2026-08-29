# t7s Enc File Tool

t7s Enc File Tool is a Windows desktop utility and command-line tool for
encrypting and decrypting Tokyo 7th Sisters `.enc` asset files,
based on Sagilio's [SeventhResource](https://github.com/SeventhServices/SeventhResource) implementation.

This is an unofficial community project. ***You must provide your own legally
obtained files and encryption keys.***

## Generative AI Usage Disclosure

*This project was developed with substantial assistance from generative AI coding tools. If you prefer not to use AI-assisted or “vibe-coded” software, please keep that in mind before using it.*

## Download

### Running from source

Python 3.12 or newer is recommended.

```powershell
python -m pip install -r requirements.txt

# GUI
python t7s_assetcrypt.py

# CLI
python t7s_assetcrypt.py --help
```

Alternatively, download the latest `t7s_enc_tool.exe` from the project's
[GitHub Releases](https://github.com/EBEBEEBE/t7s-enc-tool/releases) page.

The executable is self-contained. It does not require a separate Python
installation.

## Basic usage

Run `t7s_enc_tool.exe` without arguments to open the graphical interface.

From the Main page you can:

1. Select, or drag and drop files or folders for processing;
2. Start the processing and review the per-file status and output log;
3. Select a location to export processed file, and generate csv as logs;

The application supports recursive folder processing. APK/XAPK key extraction
and the application's settings are available through the Settings page.

## Command-line usage

Run the executable with arguments to use the CLI instead of the GUI:

```text
t7s_enc_tool.exe [decrypt|d|decode|encrypt|e|encode] [input] [options]
```

Examples:

```powershell
# Show help
.\t7s_enc_tool.exe --help

# Decrypt one file using key.txt
.\t7s_enc_tool.exe decrypt .\asset.enc

# Encrypt a file using a specific key and format
.\t7s_enc_tool.exe encrypt .\asset.json --key .\my-key.txt --type v2

# Process a folder recursively
.\t7s_enc_tool.exe decrypt .\assets --output .\decoded

# Automatically decrypt eligible files in the current directory
.\t7s_enc_tool.exe --auto-decode

# Automatically encrypt transaction data in the current directory
.\t7s_enc_tool.exe --auto-encode-transaction-data
```

Available options:

| Option | Description |
| --- | --- |
| `-o`, `--output` | Output filename or folder. |
| `-k`, `--key` | Plain-text key file; defaults to `key.txt`. |
| `-t`, `--type` | Force `v1`, `v2`, or `v2z`; otherwise format is inferred per file. |
| `--auto` | Recursive mode; decrypts only `.enc` files and skips `.enc` files when encrypting. |
| `--auto-decode`, `-ad` | Automatically decrypt from the current directory. |
| `--auto-encode-transaction-data`, `-aetd` | Automatically encrypt transaction data from the current directory. |

Folder input is processed recursively. Run `--help` for the authoritative
command-line help for the installed version.



## Project information

- [About, licensing, and acknowledgements](ABOUT.md)
- [Full disclaimer](DISCLAIMER.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)
- [Third-party license texts](THIRD_PARTY_LICENSES/)
- [Project license](LICENSE)

Original project code is dedicated to the public domain under CC0-1.0.
Third-party components remain subject to their own licenses.

## Safety and legal notice

Back up your files before processing them. The original game is discontinued,
and modified files may not be recoverable or usable. Do not use this tool for
piracy, unauthorized redistribution, or unlawful commercial use.

Read the [full disclaimer](DISCLAIMER.md) before using the application.
