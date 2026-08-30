# Quick Start Guide

## Preqiuisites

To use this tool, you will need:

- Partially or fully downloaded Tokyo 7th Sisters game data. Integrity only affects how many data you can extract.

- Keys for decryption and encryption procedure. These can be either obtained by reverse engineering the game yourself, providing a valid keys.txt, or extract from the final version of Tokyo 7th Sisters APK/XAPK (13.0.2)

You will need to legally own and acquire these files and keys yourself.

This program will not assist you in finding them or handing them to you.

## Set or Import Keys

Go to `Settings` tab. You will see 4 text boxes for 4 keys respectively. If you already have a valid `key.txt` in the program folder, these will be automatically filled. Otherwise, you can do one of the following things:

- Debug the game, get the keys and enter the keys yourself.

- Supply a `key.txt` elsewhere.

- Supply an APK or XAPK file of Tokyo 7th Sisters, version 13.0.2.

  - Only the key extracted from this particular version is tested and known to work. I haven't tested against other versions. So currently this is the only supported version.

Once the keys are properly set up, you can start encrypting or decrypting your game data.

## Acquire Game Data

We will be using Android as an example.

By default, t7s downloads and stores game data in:

`Android/data/jp.ne.donuts.t7s/files`

You can transfer these files to your computer with various tools. Search the Internet or ask your favorite LLM for how-to.

In this folder there are a few subfolders we need to pay attention to:

- `download` - game assets, including card images, banner images, voice, scripts, audio files, beatmap files...literally almost anything. Encrypted binaries.

- `masterData` - main database of t7s' game logic, including what card the game has, when gacha banners switch, how and when are shop items on sale, etc. etc. Encrypted SQL queries.

- `resourceMeta` - metadata for t7s' game asset files. The game with decide if the data is corrupt or missing using these manifests. Plain text.

- `transactionData` - your current save data. Encrypted json. You might wanna backup this one.

- `transactionDataBackup` - automatic backups of your save data, including snapshots. You might also wanna back this one up, just in case.

You should back these game data up, in case you corrupt your installation because you might not be able to recover them in the future.

Ideally, you might have your device rooted - in that case, you can back them up using softwares like NeoBackup, but this is out of the scope of this guide.

## Extracing Game Assets

First, if you'd like processed files automatically exported to a certain location, go to settings and review the output folder options.

Normally you will not need to care about the `Mode` option. The program will automatically decide for you.

Once ready, drag and drop `.enc` files into the main window's drag-and-drop zone. Decryption/Encryption process will automatically begin.

When it's done, you can:

- Double click on the items in the list to directly open them

- Right click on the items for more options

- Drag more files into it for processing

- Export all processed data into a designated folder, using "Export Files" button 

- Clear the queue, and start over

If you run into error, one or more of the following things might be happening:

- Your system drive is full and the program failed to write into it

- You do not have sufficient access to files and folders

- Your decryption keys are incorrect

In the future version of the program, error handling will point you to the right direction easier. But for now, feel free to create new issues on this repository.