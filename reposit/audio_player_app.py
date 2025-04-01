import sqlite3
import sys

from PyQt6 import uic, QtMultimedia
from PyQt6.QtCore import Qt, QUrl, QTimer, QTime
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QMainWindow, QApplication, QDialog, QMessageBox
from dialog_app import MusicDialog


class PyPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/app_form.ui', self)
        self.conn = sqlite3.connect('./database/audio_player.db')

        self.data_from_db = []
        self.ctrl_f_pressed = False
        self.standard_geometry = (self.width(), self.height())

        self.player = QtMultimedia.QMediaPlayer()
        self.audio_output = QtMultimedia.QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_slider_position)
        self.position_timer.start(100)

        self.choose_right_button.clicked.connect(self.toggle_right_button)
        self.choose_left_button.clicked.connect(self.toggle_left_button)
        self.player_button.clicked.connect(self.player_manager)
        self.duration_slider.sliderMoved.connect(self.set_player_position)

        self.add_button.clicked.connect(self.open_add_dialog)
        self.edit_button.clicked.connect(self.open_edit_dialog)
        self.delete_button.clicked.connect(self.open_delete_dialog)

        self.find_button.clicked.connect(self.filtering)
        self.clear_button.clicked.connect(self.clear_function)

        self.setFixedSize(*self.standard_geometry)
        self.setWindowTitle('Проигрыватель')

        self.player.mediaStatusChanged.connect(self.handle_media_status_changed)
        self.setup_volume_control()

        self.default_pixmap = QPixmap('./images/default.jpg')

        self.start_function()

    def update_data(self):
        cur = self.conn.cursor()
        self.original_data = cur.execute(
            "SELECT al.TITLE, al.AUTHOR, g.GENRE, al.DURATION, al.IMAGE_PATH, al.AUDIO_PATH, al.ID "
            "FROM AUDIO_LIBRARY al "
            "JOIN GENRES g ON g.ID = al.GENRE"
        ).fetchall()

        # По умолчанию используем оригинальные данные
        self.data_from_db = self.original_data.copy()

        if not self.data_from_db:
            self.clear_player_display()

    def start_function(self):
        self.update_data()

        self.current_index = 0

        self.select_visual_info()
        self.update_genre_list()

        if len(self.data_from_db) > 1:
            self.choose_right_button.setEnabled(True)

    def select_visual_info(self):
        self.current_audio = self.data_from_db[self.current_index]

        title = self.current_audio[0]
        author = self.current_audio[1]
        genre = self.current_audio[2]
        image_path = self.current_audio[4]
        audio_path = self.current_audio[5]

        if image_path:
            pixmap = QPixmap(f'.{image_path}')
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setPixmap(self.default_pixmap)

        self.load_wav(f'.{audio_path}')
        self.author_label.setText(f'<b>Автор:</b> {author}')
        self.title_label.setText(f'<b>Название:</b> {title}')
        self.genre_label.setText(f'<b>Жанр:</b> {genre}')

    def toggle_left_button(self):
        self.choose_left_button.setEnabled(True)
        if self.current_index > 0:
            self.current_index -= 1
            self.select_visual_info()
            self.update_buttons()

    def toggle_right_button(self):
        self.choose_right_button.setEnabled(True)
        if self.current_index < len(self.data_from_db) - 1:
            self.current_index += 1
            self.select_visual_info()
            self.update_buttons()

    def update_buttons(self):
        self.choose_left_button.setEnabled(self.current_index > 0)
        self.choose_right_button.setEnabled(self.current_index < len(self.data_from_db) - 1)

    def handle_media_status_changed(self, status):
        if status == QtMultimedia.QMediaPlayer.MediaStatus.LoadedMedia:
            self.duration_slider.setMaximum(self.player.duration() // 1000)

        elif status == QtMultimedia.QMediaPlayer.MediaStatus.EndOfMedia:
            self.duration_slider.setValue(0)
            self.player_button.setText(' ▶ ')

    def update_slider_position(self):
        if self.player.playbackState() == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState:
            current_pos = self.player.position() // 1000
            self.duration_slider.setValue(current_pos)
            self.update_time_display(current_pos)

    def set_player_position(self, position):
        self.player.setPosition(position * 1000)

    def update_genre_list(self):
        self.genre_box.addItem('Все жанры', None)

        cur = self.conn.cursor()

        self.current_genres = cur.execute(
            "SELECT GENRE FROM GENRES"
        ).fetchall()

        for item in sorted(self.current_genres):
            self.genre_box.addItem(f'{item[0]}', str(item[0]))

    def update_time_display(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            if not self.ctrl_f_pressed:
                self.setFixedSize(708, self.height())
                self.ctrl_f_pressed = True
            else:
                self.setFixedSize(*self.standard_geometry)
                self.ctrl_f_pressed = False

    def load_wav(self, filename):
        try:
            media_url = QUrl.fromLocalFile(filename)
            if not media_url.isValid():
                raise ValueError("Некорректный путь к файлу")

            if self.player.playbackState() == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState:
                self.player.stop()
                self.duration_slider.setValue(0)
                self.player.setSource(media_url)
                self.player_button.setText(' ▶ ')
            else:
                self.player.setSource(media_url)
        except Exception as e:
            print(f"Ошибка загрузки файла: {e}")

    def player_manager(self):
        if self.player.playbackState() == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.player_button.setText(' ▶ ')
        else:
            self.player.play()
            self.player_button.setText(' || ')

    def setup_volume_control(self):
        self.loud_slider.setRange(0, 100)

        self.loud_slider.setValue(50)
        self.audio_output.setVolume(0.5)
        self.volume_label.setText(f"{self.loud_slider.value()}%")

        self.loud_slider.valueChanged.connect(self.change_volume)

    def change_volume(self, value):
        volume = value / 100
        self.audio_output.setVolume(volume)

        self.volume_label.setText(f"{value}%")

    def open_add_dialog(self):
        dialog = MusicDialog(self.conn, edit_mode=False, audio_data=None)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            cur = self.conn.cursor()

            genre_id = cur.execute(
                "SELECT ID FROM GENRES WHERE GENRE=?",
                (dialog.genre_box.currentText(),)
            ).fetchone()[0]

            cur.execute(
                "INSERT INTO AUDIO_LIBRARY (TITLE, AUTHOR, GENRE, DURATION, IMAGE_PATH, AUDIO_PATH)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    dialog.title,
                    dialog.author,
                    genre_id,
                    int(dialog.duration),
                    f'/images/{dialog.image_file}' if dialog.image_file else None,
                    f"/musics/{dialog.audio_file}"
                )
            )
        self.conn.commit()
        self.update_data()

        self.current_index = len(self.data_from_db) - 1
        self.select_visual_info()
        self.update_buttons()

        self.player_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        self.edit_button.setEnabled(True)

        if len(self.data_from_db) == 1:
            self.choose_right_button.setEnabled(False)

    def open_edit_dialog(self):

        dialog = MusicDialog(self.conn, True, self.current_audio)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            cur = self.conn.cursor()

            genre_id = cur.execute(
                "SELECT ID FROM GENRES WHERE GENRE=?",
                (dialog.genre_box.currentText(),)
            ).fetchone()[0]

            cur.execute(
                "UPDATE AUDIO_LIBRARY SET TITLE=?, AUTHOR=?, GENRE=?, DURATION=?, IMAGE_PATH=?, AUDIO_PATH=?"
                " WHERE ID=?",
                (
                    dialog.title,
                    dialog.author,
                    genre_id,
                    int(dialog.duration),
                    f'/images/{dialog.image_file}' if dialog.image_file else None,
                    f"/musics/{dialog.audio_file}",
                    self.current_audio[6]
                )
            )
            self.conn.commit()
            self.update_data()
            self.select_visual_info()
            self.update_genre_list()
            QMessageBox.information(self, "Успех", "Изменения сохранены")

    def open_delete_dialog(self):
        if not self.data_from_db:
            return

        reply = QMessageBox.question(
            self, 'Подтверждение',
            'Вы действительно хотите удалить выбранное произведение?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                cur = self.conn.cursor()
                audio_id = self.current_audio[6]
                cur.execute("DELETE FROM AUDIO_LIBRARY WHERE ID = ?", (audio_id,))
                self.conn.commit()

                self.update_data()
                if self.data_from_db:
                    if self.current_index >= len(self.data_from_db):
                        self.current_index = len(self.data_from_db) - 1
                    self.select_visual_info()
                else:
                    self.clear_player_display()
                self.update_buttons()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Ошибка БД", f"Не удалось удалить запись: {str(e)}")

    def clear_player_display(self):
        self.image_label.setPixmap(self.default_pixmap)
        self.author_label.setText('<b>Автор:</b> ')
        self.title_label.setText('<b>Название:</b> ')
        self.genre_label.setText('<b>Жанр:</b> ')
        self.time_label.setText("00:00")
        self.duration_slider.setValue(0)
        self.player.stop()
        self.choose_left_button.setEnabled(False)
        self.choose_right_button.setEnabled(False)
        self.player_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.edit_button.setEnabled(False)
        self.player.setSource(QUrl())

    def filtering(self):
        max_time = self.max_time_edit.time()
        min_time = self.min_time_edit.time()

        author = self.author_line.text()
        title = self.title_line.text()
        genre = self.genre_box.currentText()
        max_duration = max_time.minute() * 60 + max_time.second()
        min_duration = min_time.minute() * 60 + min_time.second()

        # Фильтруем оригинальные данные
        self.filtered_data = filter_tracks(
            self.original_data,
            title,
            author,
            genre,
            min_duration if min_duration > 0 else '',
            max_duration if max_duration > 0 else '')

        if len(self.filtered_data) > 0:
            QMessageBox.information(self,
                                    f'Информация',
                                    f'Найдено {len(self.filtered_data)} произведений')
            self.clear_button.setEnabled(True)

            self.data_from_db = self.filtered_data.copy()
            self.current_index = 0
            self.select_visual_info()
            self.update_buttons()
        else:
            QMessageBox.warning(self,
                                f'Ошибка',
                                f'Не найдено соответствующих фильтрам произведений')
            self.data_from_db = self.original_data.copy()
            self.current_index = 0
            self.select_visual_info()
            self.update_buttons()

    def clear_function(self):
        self.clear_button.setEnabled(False)

        self.data_from_db = self.original_data

        self.author_line.clear()
        self.title_line.clear()
        self.genre_box.setCurrentIndex(0)
        self.max_time_edit.setTime(QTime.fromString("00:00", "mm:ss"))
        self.min_time_edit.setTime(QTime.fromString("00:00", "mm:ss"))

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.loud_slider.setValue(0)
            self.audio_output.setVolume(0)
            self.volume_label.setText(f"{self.loud_slider.value()}%")

        elif event.button() == Qt.MouseButton.LeftButton:
            self.loud_slider.setValue(50)
            self.audio_output.setVolume(0.5)
            self.volume_label.setText(f"{self.loud_slider.value()}%")


def filter_tracks(tracks, title, author, genre,
                  min_duration, max_duration):
    filtered = []
    for track in tracks:
        track_title, track_author, track_genre, track_duration = track[:4]

        match = True

        # Проверка названия
        if title != '' and title.lower() not in track_title.lower():
            match = False

        # Проверка автора
        if author != '' and author.lower() not in track_author.lower():
            match = False

        # Проверка жанра
        if genre != 'Все жанры' and genre.lower() != track_genre.lower():
            match = False

        # Проверка диапазона длительности
        if min_duration != '' and int(track_duration) < int(min_duration):
            match = False

        if max_duration != '' and int(track_duration) > int(max_duration):
            match = False

        if match:
            filtered.append(track)

    return filtered


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PyPlayer()
    ex.show()
    sys.exit(app.exec())
