import os

from PyQt6 import uic
from PyQt6.QtCore import QDir
from PyQt6.QtWidgets import QDialog, QApplication, QFileDialog, QMessageBox, QComboBox


class FormError(Exception):
    def __init__(self, parent):
        self.parent = parent
        self.title = 'Что-то произошло'

    def show_error(self):
        QMessageBox.warning(
            self.parent,
            "Ошибка",
            f"{self.title}"
        )


class ImagePathError(FormError):
    def __init__(self, parent):
        super().__init__(parent)
        self.title = 'Указанный файл изображения не существует или не найдено'


class AudioPathError(FormError):
    def __init__(self, parent):
        super().__init__(parent)
        self.title = 'Указанного аудиофайла не существует или не найдено'


class TitleError(FormError):
    def __init__(self, parent):
        super().__init__(parent)
        self.title = 'Ошибка в имени произведения'


class AuthorError(FormError):
    def __init__(self, parent):
        super().__init__(parent)
        self.title = 'Ошибка в имени автора'


class DurationError(FormError):
    def __init__(self, parent):
        super().__init__(parent)
        self.title = 'Ошибка в указании длительности\nВалидные значения от 1 до 1200 секунд'


class MusicDialog(QDialog):
    def __init__(self, conn, edit_mode=False, audio_data=None):
        super().__init__()

        uic.loadUi('./ui/dialog_form.ui', self)

        self.setFixedSize(self.width(), self.height())
        self.setWindowTitle('Добавление' if not edit_mode else 'Редактирование')

        self.conn = conn
        self.audio_data = audio_data
        self.current_dir = QDir.current()

        self.ch_audio_path_button.clicked.connect(self.add_audio_path)
        self.ch_image_path_button.clicked.connect(self.add_image_path)

        self.ok_button.clicked.connect(self.ok_function)

        self.load_genres()

        print('dalsdkadkasjd;kj')

        if edit_mode and audio_data:
            self.fill_fields(audio_data)

    def fill_fields(self, audio_data):

        self.title_line.setText(audio_data[0])
        self.author_line.setText(audio_data[1])
        self.genre_box.setCurrentText(audio_data[2])
        self.duration_line.setText(str(audio_data[3]))

        if audio_data[4]:
            self.image_path_line.setText(audio_data[4].split('/')[-1])

        if audio_data[5]:
            self.audio_path_line.setText(audio_data[5].split('/')[-1])

    def load_genres(self):
        cur = self.conn.cursor()
        genres = cur.execute("SELECT GENRE FROM GENRES").fetchall()
        self.genre_box.addItems([genre[0] for genre in genres])

    def add_audio_path(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть аудиофайл",
            "./musics/",
            "Аудиофайлы (*.wav *.mp3 *.flac *.ogg);;Все файлы (*)"
        )

        if file_name:
            relative_path = self.current_dir.relativeFilePath(file_name)

            print(relative_path)

            self.audio_path_line.setText(relative_path.split('/')[1])

    def add_image_path(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть изображение",
            "./images/",
            "Изображения (*.png *.jpg *.bmp);;Все файлы (*)"
        )

        if file_name:
            relative_path = self.current_dir.relativeFilePath(file_name)

            self.image_path_line.setText(relative_path.split('/')[1])

    def ok_function(self):
        try:
            self.title = self.title_line.text().strip()
            if not self.title:
                raise TitleError(self)

            self.author = self.author_line.text().strip()
            if not self.author:
                raise AuthorError(self)

            self.duration = self.duration_line.text()

            if not self.duration:
                raise DurationError(self)
            else:
                self.duration = int(self.duration)
                if (self.duration < 1) or (self.duration > 1200):
                    raise DurationError(self)

            self.audio_file = self.audio_path_line.text().strip()
            if not self.audio_file or not os.path.exists(f"./musics/{self.audio_file}"):
                raise AudioPathError(self)

            self.image_file = self.image_path_line.text().strip()

            if self.image_file and not os.path.exists(f"./images/{self.image_file}"):
                raise ImagePathError(self)

            self.accept()

        except TitleError as e:
            e.show_error()
        except AuthorError as e:
            e.show_error()
        except DurationError as e:
            e.show_error()
        except ImagePathError as e:
            e.show_error()
        except AudioPathError as e:
            e.show_error()


