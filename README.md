# Speech Transcription Tool

This application is a Speech Transcription Tool built with Python, using Tkinter for the GUI, matplotlib for plotting spectrograms, and several other libraries to handle audio processing and transcription management.

![Spectrogram](https://github.com/CShulby/Speech-Transcription-Tool/blob/main/Spectrogram.png "Spectrogram")


## Features

- Load WAV files from a directory for transcription.
- Display spectrograms of audio files.
- Play audio files directly from the interface.
- Annotate transcriptions and save them to a CSV file.
- Navigate through audio files (previous and next).

## Prerequisites

Before you can run the tool, you need to have Python installed on your system along with the following Python libraries:

- tkinter
- matplotlib
- scipy
- pandas
- pydub
- simpleaudio

## Setup

1. **Clone the repository**

   ```
   git clone https://github.com/cshulby/speech-transcription-tool.git
   cd speech-transcription-tool
   ```
   
## Install dependencies

It's recommended to use a virtual environment:

```
pip install -r requirements.txt
```

## Configure the tool

Edit the config_app.json file to set the paths and parameters as per your requirements.

## Usage

Run the main script to open the GUI:

```
python main.py
```

## Load audio files

Use the "Audio Files Folder" button to select the directory containing your WAV files.

## Transcribe

    Play the audio and listen to it through the interface.
    Enter the transcriptions in the provided text field.
    Use the "Submit to Save" button to save the transcription to a CSV file.

## Navigation

Use the "Next >>" and "<< Previous" buttons to move between files.
You can also use the cursor to play or stop at a certain point in the audio

## Exit the tool

Click the "Quit" button to close the application.

## Notes
- Thank you to cicada for the inspiration
- This is a very simple tool for personal use. Feel free to do with it as you wish
