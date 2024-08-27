import sys
import os
import re
from PySide6.QtCore import QMetaObject
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QButtonGroup
from PySide6.QtUiTools import QUiLoader
from pytube import YouTube, Playlist

class YouTubeDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        loader = QUiLoader()
        ui_file = os.path.join(os.path.dirname(__file__), "ui", "main.ui")
        self.ui = loader.load(ui_file, self)
        self.setWindowTitle('YouTube Video Downloader')
        self.setGeometry(100, 100, 700, 400)
        # Set fixed size
        self.setFixedSize(700, 400)
        
        from PySide6.QtGui import QIcon
        self.setWindowIcon(QIcon('assets/icons/icon.png'))
        self.setStyleSheet(open("qss/style.qss").read())

        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.ui.videoButton)
        self.button_group.addButton(self.ui.audioButton)
        self.button_group.addButton(self.ui.playlistVideoButton)
        self.button_group.addButton(self.ui.playlistAudioButton)

        self.ui.pick_folder_button.clicked.connect(self.pick_folder)
        self.ui.download_button.clicked.connect(self.download)
        self.ui.open_folder_button.clicked.connect(self.open_folder)
        self.connect_buttons()


    def pick_folder(self):
        self.folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder', os.path.expanduser('C:/Users/%username%/Downloads'))
        if self.folder_path:
            self.ui.status_label.setText(f'Selected Folder: {self.folder_path}')

    def open_folder(self):
        if not hasattr(self, 'folder_path') or not self.folder_path:
            self.ui.status_label.setText('Please select a destination folder.')
            return
        download_folder = os.path.realpath(self.folder_path)
        os.startfile(download_folder)
        

    def download(self):
        url = self.ui.url_input.text()
        mode = self.get_current_mode()

        if mode == 'Select a Mode':
            self.ui.status_label.setText('Please select a mode.')
            return

        if not url:
            self.ui.status_label.setText('Please enter a YouTube URL.')
            return

        if not hasattr(self, 'folder_path') or not self.folder_path:
            self.ui.status_label.setText('Please select a destination folder.')
            return

        try:
            mode = self.get_current_mode()
            if mode == 'Video' or mode == 'Audio':
                yt = YouTube(url, on_progress_callback=self.progress_function)
                if mode == 'Video':
                    video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                    video_title = re.sub(r'[\\/*?:"<>|]', "", yt.title)
                    if not video_title.endswith(".mp4"):
                        video_title += ".mp4"
                    video.download(output_path=self.folder_path, filename=video_title)
                    self.ui.status_label.setText(f'Download complete: {video_title}')
                elif mode == 'Audio':
                    video = yt.streams.filter(only_audio=True).first()
                    audio_title = re.sub(r'[\\/*?:"<>|]', "", yt.title)
                    if not audio_title.endswith(".mp3"):
                        audio_title += ".mp3"
                    video.download(output_path=self.folder_path, filename=audio_title)
                    self.audio_conversion(audio_title)
                    self.ui.status_label.setText(f'Download complete: {audio_title}')
            elif mode == 'Playlist Video' or mode == 'Playlist Audio':
                playlist = Playlist(url)
                playlist._video_regex = re.compile(r"\"url\":\"(/watch\?v=[\w-]*)")
                total_videos = len(playlist.video_urls)
                for index, video_url in enumerate(playlist.video_urls):
                    yt = YouTube(video_url, on_progress_callback=self.progress_function)
                    video_title = re.sub(r'[\\/*?:"<>|]', "", yt.title)
                    if mode == 'Playlist Video':
                        if not video_title.endswith(".mp4"):
                            video_title += ".mp4"
                        yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download(output_path=self.folder_path, filename=video_title)
                    elif mode == 'Playlist Audio':
                        if not video_title.endswith(".mp3"):
                            video_title += ".mp3"
                        yt.streams.filter(only_audio=True).first().download(output_path=self.folder_path, filename=video_title)
                        self.audio_conversion(video_title)
                    self.update_progress_bar_playlist(index + 1, total_videos)
                    self.ui.status_label.setText(f'Download complete: {video_title}')
        except Exception as e:
            self.ui.status_label.setText(f'Error: {str(e)}')

    def progress_function(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_of_completion = bytes_downloaded / total_size * 100
        self.ui.progress_bar.setValue(int(percentage_of_completion))

    def update_progress_bar_playlist(self, current_video_index, total_videos):
        percentage_of_completion = (current_video_index / total_videos) * 100
        self.ui.progress_bar.setValue(int(percentage_of_completion))

    def audio_conversion(self, filename):
        # TODO: Implement audio conversion logic
        pass

    def get_current_mode(self):
        if self.ui.videoButton.isChecked():
            return 'Video'
        elif self.ui.audioButton.isChecked():
            return 'Audio'
        elif self.ui.playlistVideoButton.isChecked():
            return 'Playlist Video'
        elif self.ui.playlistAudioButton.isChecked():
            return 'Playlist Audio'
        return 'Select a Mode'

    def switch_mode(self, mode, description, label):
        self.ui.mode_label.setText(f'{mode}')
        self.ui.description_label.setText(f'{description}')
        self.ui.label.setText(f'{label}')
        self.ui.status_label.setText('')
        self.ui.progress_bar.setValue(0)

    def connect_buttons(self):
        self.ui.videoButton.clicked.connect(lambda: self.switch_mode('Video','From a YouTube video URL, download the video in MP4 video format.','(in highest available quality)'))
        self.ui.audioButton.clicked.connect(lambda: self.switch_mode('Audio','From a YouTube video URL, download the video in MP3 audio format.','(in highest available quality)'))
        self.ui.playlistVideoButton.clicked.connect(lambda: self.switch_mode('Playlist Video','From a YouTube video playlist URL, download each videos in the playlist in MP4 video format.','(in highest available quality)'))
        self.ui.playlistAudioButton.clicked.connect(lambda: self.switch_mode('Playlist Audio','From a YouTube video playlist URL, download each videos in the playlist in MP3 audio format.','(in highest available quality)'))
        self.ui.download_button.clicked.connect(self.download)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Load QSS file
    with open("qss/style.qss", "r") as file:
        app.setStyleSheet(file.read())

    downloader = YouTubeDownloader()
    downloader.ui.progress_bar.setValue(0)  # Set progress bar to 0%
    downloader.switch_mode('Select a Mode','','')
    downloader.show()
    sys.exit(app.exec())
