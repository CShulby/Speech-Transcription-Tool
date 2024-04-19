import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import matplotlib.pyplot as plt
from scipy.io import wavfile
import os
import json
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from tkinter import messagebox
from pydub import AudioSegment
import simpleaudio as sa
import time

# Globals
current_playback_line = None
playback_line_id = None
global AXES1, canvas, start_position
AXES1 = None
canvas = None
start_position = 0
playback_object = None
transcriptions_df = pd.DataFrame()


# Define styling constants
BUTTON_COLOR = "#0078D7"
BUTTON_FONT = ("Helvetica", 10)
LABEL_FONT = ("Helvetica", 12)
ENTRY_FONT = ("Helvetica", 12)
WIDGET_BG_COLOR = "#F0F0F0"


def load_annotations():
    """
    Loads annotations from a specified CSV file into a pandas DataFrame. If the file does not exist, initializes an empty DataFrame with predefined columns.

    Globals:
    - transcriptions_df (pd.DataFrame): DataFrame used to store and access the transcription data.

    Effects:
    - Initializes or updates the 'transcriptions_df' global variable with transcription data from a CSV file.
    """
    global transcriptions_df
    if os.path.exists(CURRENT_CSV_FILENAME):
        transcriptions_df = pd.read_csv(CURRENT_CSV_FILENAME, sep='|')
        transcriptions_df.sort_values('Filename', inplace=True)  # Sort the DataFrame by the Filename column
    else:
        transcriptions_df = pd.DataFrame(columns=["Filename", "Transcription"])


# Transcription management#
def get_transcription(filepath):
    """
    Retrieves the transcription associated with a specific audio file from the global DataFrame.

    Parameters:
    - filepath (str): The path to the audio file for which the transcription is requested.

    Returns:
    - str: The transcription text if found, else an empty string.
    """
    transcription = transcriptions_df[transcriptions_df["Filename"] == filepath][
        "Transcription"
    ]
    return transcription.iloc[0] if not transcription.empty else ""


def update_transcription_display():
    """
    Updates the transcription text entry widget with the transcription of the currently displayed audio file.

    Effects:
    - Sets the value of the 'ANNOTATION_ENTRY_VAR' tkinter StringVar to the current file's transcription.
    """
    if FILES_LEFT_TO_ANNOTATE:
        current_file = FILES_LEFT_TO_ANNOTATE[CURRENT_INDEX]
        current_transcription = get_transcription(current_file)
        ANNOTATION_ENTRY_VAR.set(current_transcription)


# Initaliazing Tkinter  Window#
root = tk.Tk()
root.title("Speech Transcription Tool")

# Create the main frame and have it fill the whole root window using grid
mainframe = tk.Frame(root, bg=WIDGET_BG_COLOR)
mainframe.grid(row=0, column=0, sticky="nsew")
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Reading configurations from JSON file
with open("config_app.json", "r") as jsonfile_obj:
    data_json = jsonfile_obj.read()
datajson_obj = json.loads(data_json)

BUTTONS_HEIGHT = datajson_obj["ButtonsParams"]["Height"]
BUTTONS_WIDTH = datajson_obj["ButtonsParams"]["Width"]
CURRENT_CSV_FILENAME = datajson_obj["TranscriptionFile"]["TranscriptionFile"]


# Initialize constants
CURRENT_INDEX = 0
FOLDER_WAV_FILES = []
FILES_LEFT_TO_ANNOTATE = []
FOLDER_TO_SAVE_ANNOTATIONS = ""
ANNOTATION_ENTRY_VAR = tk.StringVar(mainframe)

# Initializing constants
CURRENT_INDEX = 0
FOLDER_WAV_FILES = []
FILES_LEFT_TO_ANNOTATE = []
FOLDER_TO_SAVE_ANNOTATIONS = ""
ANNOTATION_ENTRY_VAR = tk.StringVar(mainframe)


# Spectrogram Function
def plot_wav_file(path_wavfile, type_spec="psd"):
    """
    Plots the spectrogram of a WAV file in a tkinter frame using matplotlib.

    Parameters:
    - path_wavfile (str): Path to the WAV file to plot.
    - type_spec (str): Type of spectrogram to display; defaults to 'psd' for power spectral density.

    Effects:
    - Displays the spectrogram of the specified audio file in the GUI.
    """
    global AXES1, canvas
    fig = Figure(figsize=(12, 6))
    sample_rate, samples = wavfile.read(path_wavfile)
    if samples.ndim > 1:
        samples = samples[:, 0]

    # Spectrogram plotting
    AXES1 = fig.add_subplot(111)
    AXES1.specgram(
        samples, Fs=sample_rate, mode=type_spec, cmap=plt.get_cmap("viridis")
    )
    AXES1.set_ylabel("Frequency [Hz]")
    AXES1.set_xlabel("Time [sec]")

    # Embedding in Tkinter
    if canvas:
        canvas.get_tk_widget().destroy()  # Remove old canvas to avoid overlay issues

    canvas = FigureCanvasTkAgg(fig, master=mainframe)
    canvas.draw()
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.grid(row=2, column=0, columnspan=6, padx=10, pady=10)

    # Reconnect the click event handler
    canvas.mpl_connect("button_press_event", on_click)


def update_line_position(x_position):
    global current_playback_line, AXES1, canvas, start_position
    if current_playback_line:
        current_playback_line.remove()
    current_playback_line = AXES1.axvline(
        x=x_position, color="lime", linewidth=2, linestyle="--"
    )
    canvas.draw_idle()
    start_position = x_position


def on_click(event):
    """
    Handles click events on the spectrogram plot, allowing the user to start or stop playback or adjust the playback starting point.

    Parameters:
    - event: The mouse event that triggered the function.

    Effects:
    - Adjusts playback behavior or starting position based on the location of the click within the spectrogram.
    """
    global current_playback_line, start_position, playback_object
    if event.inaxes == AXES1:
        clicked_x_position = event.xdata  # Time in seconds where the user clicked
        start_position = clicked_x_position  # Update global start position

        if current_playback_line:
            line_xdata = current_playback_line.get_xdata()[0]
            if abs(clicked_x_position - line_xdata) < 0.5:  # Close to the line
                if playback_object and playback_object.is_playing():
                    playback_object.stop()  # Stop playback if playing
                else:
                    play_audio(CURRENT_INDEX)  # Restart or continue playing
            else:
                update_line_position(clicked_x_position)
        else:
            update_line_position(clicked_x_position)


# Quits Tkinter  Window
def _quit():
    """
    Terminates the application and stops any ongoing audio playback.

    Effects:
    - Stops playback if it is running.
    - Closes the application window and destroys all associated resources.
    """
    stop_playback()
    root.quit()
    root.destroy()


# Selects Folder to save
def browse_folder_to_save_annotations():
    """
    Opens a dialog to select a folder where the audio transcriptions will be saved, and updates the global variable with the selected folder.

    Globals:
    - FOLDER_TO_SAVE_ANNOTATIONS (str): Path to the folder where annotations will be saved.

    Effects:
    - Sets the global variable 'FOLDER_TO_SAVE_ANNOTATIONS' to the selected folder path.
    - Displays a message box confirming the selected folder.
    """
    filename = filedialog.askdirectory()
    global FOLDER_TO_SAVE_ANNOTATIONS
    FOLDER_TO_SAVE_ANNOTATIONS = filename
    messagebox.showinfo(
        "Folder Selected",
        "Annotations will be saved at: "
        + "\n"
        + os.path.join(filename, CURRENT_CSV_FILENAME),
    )


# Next Audio Update
def next_audio_update_index():
    """
    Advances to the next audio file in the list, updates the transcription display, and starts playback.

    Globals:
    - CURRENT_INDEX (int): The current index in the list of audio files.

    Effects:
    - Increments the 'CURRENT_INDEX'.
    - Updates the display to show the spectrogram of the next audio file.
    - Updates the transcription display for the new audio file.
    """
    global CURRENT_INDEX
    stop_playback()

    # Save any changes to the transcription before moving to the next audio file
    save_annotations(CURRENT_INDEX)

    if CURRENT_INDEX < len(FOLDER_WAV_FILES) - 1:
        CURRENT_INDEX += 1
        plot_wav_file(FILES_LEFT_TO_ANNOTATE[CURRENT_INDEX], "psd")
        update_transcription_display()
        display_path = format_path_display(FILES_LEFT_TO_ANNOTATE[CURRENT_INDEX])
        current_file_label.config(text=display_path)
        play_audio(CURRENT_INDEX)
    else:
        messagebox.showinfo("End", "No more files in the folder.")

def format_path_display(filepath):
    """
        Formats a file path to display only the last three directories plus the filename.

        This function simplifies file paths for display purposes by extracting and showing
        only the last three directories and the filename from a given file path. If the path has fewer
        than three directories, it displays the complete path.

        Parameters:
        - filepath (str): The full path to a file.

        Returns:
        - str: A shortened file path containing only the last three directories and the filename.
    """
    # Split the filepath into its components
    parts = filepath.split(os.sep)
    # Determine the number of parts to include (up to the last three directories plus the filename)
    num_parts_to_include = min(4, len(parts))
    # Include only the necessary parts
    display_path = os.sep.join(parts[-num_parts_to_include:])
    return display_path


# Previous Audio
def previous_audio_update_index():
    """
    Moves to the previous audio file in the list, updates the transcription display, and starts playback.

    Globals:
    - CURRENT_INDEX (int): The current index in the list of audio files.

    Effects:
    - Decrements the 'CURRENT_INDEX'.
    - Updates the display to show the spectrogram of the previous audio file.
    - Updates the transcription display for the new audio file.
    """
    global CURRENT_INDEX
    stop_playback()

    if CURRENT_INDEX > 0:
        CURRENT_INDEX -= 1
        plot_wav_file(FILES_LEFT_TO_ANNOTATE[CURRENT_INDEX], "psd")
        update_transcription_display()
        display_path = format_path_display(FILES_LEFT_TO_ANNOTATE[CURRENT_INDEX])
        current_file_label.config(text=display_path)
    else:
        messagebox.showinfo("Start", "This is the first file.")


# Browse Wav file folder
def browse_wav_files():
    """
    Opens a dialog to select a folder and loads all WAV files from the selected folder into a global list.

    Globals:
    - FOLDER_WAV_FILES (list): A list of paths to WAV files.
    - FILES_LEFT_TO_ANNOTATE (list): A list of files left to annotate, initially the same as FOLDER_WAV_FILES.

    Effects:
    - Populates 'FOLDER_WAV_FILES' and 'FILES_LEFT_TO_ANNOTATE' with paths to WAV files from the selected directory.
    - Updates the GUI to display the spectrogram of the first audio file and its transcription.
    """
    filename = filedialog.askdirectory()
    global FILES_LEFT_TO_ANNOTATE, FOLDER_WAV_FILES, current_file_label
    FOLDER_WAV_FILES.clear()  # Clear the list before appending new files
    list_files = list(os.walk(filename))
    for root, dirs, files in list_files:
        for file in files:
            if file.endswith((".wav", ".WAV")):  # Check for WAV files (case-sensitive)
                FOLDER_WAV_FILES.append(os.path.join(root, file))

    FOLDER_WAV_FILES.sort()  # Sort the list of files alphabetically

    if len(FOLDER_WAV_FILES) == 0:
        messagebox.showerror("Error", "No WAV files found in the selected path")
    else:
        FILES_LEFT_TO_ANNOTATE = FOLDER_WAV_FILES[:]
        display_path = format_path_display(FOLDER_WAV_FILES[0])
        plot_wav_file(FOLDER_WAV_FILES[0], "psd")
        current_file_label = tk.Label(mainframe, text=display_path)
        current_file_label.grid(row=1, column=3)
        update_transcription_display()  # Update transcription display for the first file

        if os.path.exists(CURRENT_CSV_FILENAME):
            annotated_files = pd.read_csv(CURRENT_CSV_FILENAME, error_bad_lines=False)
            annotated_files = annotated_files["Filename"].tolist()
            FILES_LEFT_TO_ANNOTATE = [
                f for f in FOLDER_WAV_FILES if os.path.basename(f) not in annotated_files
            ]
            track_annotated = len(FOLDER_WAV_FILES) - len(FILES_LEFT_TO_ANNOTATE)
            messagebox.showinfo(
                "Files Found:",
                "Number of audio files found: "
                + str(len(FOLDER_WAV_FILES))
                + "\n"
                + "Files already annotated: "
                + str(track_annotated),
            )
        else:
            messagebox.showinfo(
                "Files Found:",
                "Number of audio files found: " + str(len(FOLDER_WAV_FILES)),
            )


# Play Audio
def play_audio_from_position(path, start_ms):
    """
    Begins playback of an audio file from a specified start point in milliseconds.

    Parameters:
    - path (str): Path to the audio file.
    - start_ms (int): Start point of playback in milliseconds.

    Globals:
    - playback_object (simpleaudio.PlayObject): Handles the audio playback.
    - playback_start_time (float): Timestamp when the playback was started.

    Effects:
    - Initiates audio playback from the specified position and records the start time.
    """
    global playback_object, playback_start_time
    sound = AudioSegment.from_file(path, format="wav")
    play_sound = sound[start_ms:]
    playback_object = sa.play_buffer(
        play_sound.raw_data,
        num_channels=play_sound.channels,
        bytes_per_sample=play_sound.sample_width,
        sample_rate=play_sound.frame_rate,
    )
    playback_start_time = time.time()  # Record the start time of playback


def update_line():
    """
    Updates the playback position line on the spectrogram based on the elapsed playback time.

    Globals:
    - current_playback_line (matplotlib line object): Line indicating current playback position.
    - AXES1 (matplotlib axes object): The axes object of the plot.
    - canvas (FigureCanvasTkAgg): Tkinter canvas used for the matplotlib plot.
    - playback_start_time (float): Time when the playback started.
    - start_position (float): Starting position of the playback in seconds.

    Effects:
    - Moves the playback position line on the plot to reflect the current playback time.
    """
    global current_playback_line, AXES1, canvas, playback_start_time, start_position

    if playback_object and playback_object.is_playing():
        elapsed_time = (
            time.time() - playback_start_time
        )  # Calculate elapsed time in seconds
        current_time = start_position + elapsed_time  # Current position in the audio
        if current_playback_line:
            current_playback_line.set_xdata([current_time, current_time])
        else:
            current_playback_line = AXES1.axvline(
                x=current_time, color="lime", linewidth=2, linestyle="--"
            )
        canvas.draw_idle()
        root.after(50, update_line)  # Continue updating every 50 ms
    elif current_playback_line:
        current_playback_line.remove()
        current_playback_line = None
        canvas.draw_idle()


def play_audio(index_value):
    """
    Initiates playback of an audio file from the start or a paused position based on the current index of the audio file list.

    Parameters:
    - index_value (int): Index in the global list 'FILES_LEFT_TO_ANNOTATE' to identify which audio file to play.

    Globals:
    - playback_object (simpleaudio.PlayObject): The current playback object used for playing audio.
    - current_playback_line (matplotlib line object): Visual indicator on the spectrogram showing current playback position.
    - start_position (float): The start position in seconds where the audio playback should begin.

    Effects:
    - Starts or resumes audio playback from the specified or last known position.
    - Manages the visualization of the playback progress on the spectrogram.
    """
    global playback_object, current_playback_line, start_position

    path_wavfile = FILES_LEFT_TO_ANNOTATE[index_value]
    start_milliseconds = int(start_position * 1000)  # Convert seconds to milliseconds

    # Stop previous playback if exists
    if playback_object and playback_object.is_playing():
        playback_object.stop()

    # Remove existing line if exists
    if current_playback_line:
        current_playback_line.remove()
        current_playback_line = None

    # Start playback and visual update
    play_audio_from_position(path_wavfile, start_milliseconds)
    update_line()


def stop_playback():
    """
    Stops the current audio playback and removes the playback position line from the spectrogram.

    Globals:
    - playback_object (simpleaudio.PlayObject): Handles the audio playback.
    - current_playback_line (matplotlib line object): Line indicating current playback position.
    - canvas (FigureCanvasTkAgg): Tkinter canvas used for the matplotlib plot.

    Effects:
    - Stops the audio playback and removes the line from the plot.
    """
    global playback_object, current_playback_line
    if (
        "playback_object" in globals()
        and playback_object
        and playback_object.is_playing()
    ):
        playback_object.stop()
    if "current_playback_line" in globals() and current_playback_line:
        current_playback_line.remove()
        canvas.draw_idle()
        current_playback_line = None


def stop_audio():
    """
    Stops the current audio playback.

    Globals:
    - playback_object (simpleaudio.PlayObject): Handles the audio playback.

    Effects:
    - Stops the audio playback without affecting other GUI elements.
    """
    global playback_object
    if playback_object.is_playing():
        playback_object.stop()


# Saves Annotations
def save_annotations(index_value):
    """
    Saves the currently entered transcription into a CSV file and updates the DataFrame storing transcriptions.

    Parameters:
    - index_value (int): Index of the current audio file in the global list of files.

    Effects:
    - Updates the CSV file and the global DataFrame with the new transcription.
    """
    try:
        filepath = FILES_LEFT_TO_ANNOTATE[index_value]
        transcription = ANNOTATION_ENTRY_VAR.get().strip()

        # Check if the CSV file exists and read existing data if it does
        if os.path.exists(CURRENT_CSV_FILENAME):
            existing_data = pd.read_csv(CURRENT_CSV_FILENAME, sep='|')
            # Check if transcription for the current file already exists
            if filepath in existing_data["Filename"].values:
                # Update the existing transcription
                existing_data.loc[existing_data["Filename"] == filepath, "Transcription"] = transcription
            else:
                # Append new transcription
                new_data = pd.DataFrame({"Filename": [filepath], "Transcription": [transcription]})
                existing_data = pd.concat([existing_data, new_data], ignore_index=True)
            # Sort DataFrame before saving
            existing_data.sort_values('Filename', inplace=True)
        else:
            # Create new file with transcription
            existing_data = pd.DataFrame({"Filename": [filepath], "Transcription": [transcription]})

        # Save the DataFrame back to CSV using the pipe delimiter
        existing_data.to_csv(CURRENT_CSV_FILENAME, sep='|', index=False)
        global transcriptions_df
        transcriptions_df = existing_data.copy()
        ANNOTATION_ENTRY_VAR.set(transcription)

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")


# Binding Key Action#
def save_and_next_audio(event):
    """
    Saves the current transcription and moves to the next audio file upon a specific key event (typically the Return key).

    Parameters:
    - event (Event): The key event that triggers this function.

    Effects:
    - Calls the save_annotations function and, upon successful save, updates to the next audio file and starts its playback.
    """
    save_annotations(CURRENT_INDEX)
    next_audio_update_index()
    play_audio(CURRENT_INDEX)


# Header and Title#
header_name = tk.Label(
    mainframe,
    text="Speech Transcription Tool",
    font=("Arial", 16, "bold"),
    bg=WIDGET_BG_COLOR,
)
header_name.grid(row=0, column=1, columnspan=4, pady=(10, 5))


# Rows

audio_files_folder = tk.Button(
    mainframe,
    text="Audio Files Folder",
    bg=BUTTON_COLOR,
    fg="white",
    font=BUTTON_FONT,
    command=browse_wav_files,
)
audio_files_folder.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
quit_option = tk.Button(
    mainframe, text="Quit", bg=BUTTON_COLOR, fg="white", font=BUTTON_FONT, command=_quit
)
quit_option.grid(row=1, column=5, padx=5, pady=5, sticky="e")

next_button = tk.Button(
    mainframe,
    text=" Next >> ",
    fg="green",
    bd=3,
    relief="raised",
    command=next_audio_update_index,
    height=BUTTONS_HEIGHT,
    width=BUTTONS_WIDTH,
)
next_button.grid(row=4, column=6, padx=5, pady=5)
prev_button = tk.Button(
    mainframe,
    text=" << Previous ",
    fg="green",
    bd=3,
    relief="raised",
    command=previous_audio_update_index,
    height=BUTTONS_HEIGHT,
    width=BUTTONS_WIDTH,
)
prev_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="w")

# Text
###############################################################
tk.Label(mainframe, text="Transcription:", font=LABEL_FONT, bg=WIDGET_BG_COLOR).grid(
    row=6, column=0, sticky="w"
)
annotation_text = tk.Entry(
    mainframe, textvariable=ANNOTATION_ENTRY_VAR, font=ENTRY_FONT, relief="sunken"
)
annotation_text.grid(row=7, column=0, columnspan=6, padx=5, pady=5, sticky="ew")


# Play, Stop, & Submit buttons

play_button = tk.Button(
    mainframe,
    text="Play Audio",
    bg=BUTTON_COLOR,
    fg="white",
    font=BUTTON_FONT,
    command=lambda: play_audio(CURRENT_INDEX),
)
play_button.grid(row=8, column=2, padx=5, pady=5, sticky="ew")

stop_button = tk.Button(
    mainframe,
    text="Stop Audio",
    bg=BUTTON_COLOR,
    fg="white",
    font=BUTTON_FONT,
    command=stop_audio,
)
stop_button.grid(row=8, column=3, padx=5, pady=5, sticky="ew")

submit_button = tk.Button(
    mainframe,
    text="Submit to Save",
    bg=BUTTON_COLOR,
    fg="white",
    font=BUTTON_FONT,
    command=lambda: save_annotations(CURRENT_INDEX),
)
submit_button.grid(row=8, column=4, padx=5, pady=5, sticky="ew")

# Configuring row and columns
for i in range(9):
    mainframe.grid_rowconfigure(i, weight=1)
for i in range(6):
    mainframe.grid_columnconfigure(i, weight=1)

# Bind key action for submit
root.bind("<Return>", save_and_next_audio)
load_annotations()

# Main Loop
root.mainloop()
