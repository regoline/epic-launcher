import os
import json
import hashlib
import time
import sys
import shutil
import socket
import zipfile
import requests
from urllib.request import urlretrieve
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QProgressBar, QCheckBox, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap, QColor, QFont, QIcon, QMovie


# Determine if the application is running as a bundled executable
if getattr(sys, 'frozen', False):
    # Running in a bundle (PyInstaller)
    base_path = sys._MEIPASS
else:
    # Running in a normal Python environment
    base_path = os.path.dirname(os.path.abspath(__file__))

# Constants
BACKGROUND_IMAGE_PATH = os.path.join(base_path,"media", "fundo_launcher.png")
FOLDER_ICON_PATH = os.path.join(base_path, "media", "folder.png")
PENCIL_ICON_PATH = os.path.join(base_path, "media", "pencil.png")
SAVE_ICON_PATH = os.path.join(base_path, "media", "save.png")
START_ICON_PATH = os.path.join(base_path, "media", "start.png")
STOP_ICON_PATH = os.path.join(base_path, "media", "stop.png")
CLOSE_ICON_PATH = os.path.join(base_path, "media", "close.png")
LOADING_GIF_PATH = os.path.join(base_path, "media", "loading.gif")  # Path to a loading GIF
SETTINGS_PATH = os.path.join(base_path, "config", "settings.json")
SETTINGS_NO_RAZOR_PATH = os.path.join(base_path, "config", "settings_no_razor.json")

CONFIG_PATH = os.path.expanduser("~/.epic_shard_launcher/config.json")
STATE_PATH = os.path.expanduser("~/.epic_shard_launcher/state.json")
SERVER_HOSTNAME = "epic-shard.com"
SERVER_PORT = 2595
SERVER_IP = socket.gethostbyname(SERVER_HOSTNAME)


class DownloadWorker(QObject):
    progress_updated = pyqtSignal(int, int)  # Signal for updating progress
    current_file_updated = pyqtSignal(str)  # Signal for updating the current file label
    hashing_file = pyqtSignal(str)  # Signal for hashing files
    download_finished = pyqtSignal(bool, list)  # Signal for when the download is finished
    error_occurred = pyqtSignal(str)  # Signal for errors
    total_size_calculated = pyqtSignal(int)  # Signal for total download size

    def __init__(self, install_path, download_state, stop_download, download_start_time):
        super().__init__()
        self.install_path = install_path
        self.download_state = download_state
        self.stop_download = stop_download
        self.download_start_time = download_start_time
        self.total_downloaded_bytes = 0  # Initialize total downloaded bytes

    def download_files(self):
        """Download files from the server."""
        try:
            # Calculate the total download size
            #total_size = self.calculate_total_download_size()
            #self.total_size_calculated.emit(total_size)

            # Proceed with downloading files
            manifest_url = f"http://{SERVER_IP}:{SERVER_PORT}/Manifest"
            hashes_url = f"http://{SERVER_IP}:{SERVER_PORT}/Hashes"

            manifest_path = os.path.join(self.install_path, "Manifest")
            hashes_path = os.path.join(self.install_path, "Hashes")

            self.download_file(manifest_url, manifest_path)
            self.download_file(hashes_url, hashes_path)

            with open(manifest_path, "r") as f:
                manifest_files = [line.strip() for line in f.readlines() if line.strip().startswith('/')]

            with open(hashes_path, "r", encoding='utf-8-sig') as f:
                hashes = {}
                for line in f.readlines():
                    line = line.strip()
                    if line:
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            file_path = parts[0].strip()
                            first_hash = parts[1].strip()
                            hashes[file_path] = first_hash

            pending_files = []
            for file_path in manifest_files:
                if file_path.startswith('/-'):
                    continue

                dir_path, file_name = os.path.split(file_path)

                if file_name.startswith('+'):
                    download_file_name = file_name[1:]
                    download_file_path = os.path.join(dir_path, download_file_name)
                    local_file_path = os.path.join(self.install_path, download_file_path.lstrip('/'))
                else:
                    download_file_path = file_path
                    local_file_path = os.path.join(self.install_path, file_path.lstrip('/'))

                if file_name.startswith('+'):
                    if os.path.exists(local_file_path):
                        continue

                if download_file_path in self.download_state["downloaded_files"]:
                    if os.path.exists(local_file_path):
                        current_hash = self.calculate_md5(local_file_path)
                        if current_hash.lower() == self.download_state["downloaded_files"][download_file_path].lower():
                            continue
                        else:
                            print(f"Arquivo {file_path} está desatualizado ou corrompido. Rebaixando...")
                    else:
                        print(f"Arquivo {file_path} está faltando. Rebaixando...")
                pending_files.append(file_path)

            failed_files = []

            for i, file_path in enumerate(pending_files):
                if self.stop_download():
                    break

                self.current_file_updated.emit(f"Baixando: {file_path}")
                try:
                    self.download_or_update_file(file_path, hashes.get(file_path, ""))
                except Exception as e:
                    failed_files.append(file_path)

                self.progress_updated.emit(i + 1, len(pending_files))

            self.download_finished.emit(not self.stop_download(), failed_files)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def calculate_total_download_size(self):
        """Calculate the total size of all files to be downloaded."""
        total_size = 0
        manifest_url = f"http://{SERVER_IP}:{SERVER_PORT}/Manifest"
        manifest_path = os.path.join(self.install_path, "Manifest")

        try:
            # Download the manifest file
            urlretrieve(manifest_url, manifest_path)

            # Read the manifest file
            with open(manifest_path, "r") as f:
                manifest_files = [line.strip() for line in f.readlines() if line.strip().startswith('/')]

            # Calculate the total size of all files
            for file_path in manifest_files:
                if file_path.startswith('/-'):
                    continue

                file_url = f"http://{SERVER_IP}:{SERVER_PORT}/{file_path.lstrip('/')}"
                response = requests.head(file_url)
                if response.status_code == 200:
                    total_size += int(response.headers.get("content-length", 0))

        except Exception as e:
            print(f"Erro ao calcular o tamanho total do download: {e}")

        # Emit the total size
        self.total_size_calculated.emit(total_size)
        return total_size

    def download_or_update_file(self, file_path, expected_hash):
        """Download or update a file."""
        dir_path, file_name = os.path.split(file_path)

        if file_name.startswith('+'):
            download_file_name = file_name[1:]
            download_file_path = os.path.join(dir_path, download_file_name)
            local_file_path = os.path.join(self.install_path, download_file_path.lstrip('/'))
        else:
            download_file_path = file_path
            local_file_path = os.path.join(self.install_path, file_path.lstrip('/'))

        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

        if os.path.exists(local_file_path):
            self.hashing_file.emit(f"Hashing: {file_path}")
            current_hash = self.calculate_md5(local_file_path).lower()

            if current_hash == expected_hash.lower():
                self.download_state["downloaded_files"][download_file_path] = expected_hash
                return
            else:
                print(f"Arquivo {file_path} está corrompido ou desatualizado. Hash esperado: {expected_hash}, Hash atual: {current_hash}")

        self.current_file_updated.emit(f"Baixando: {file_path}")

        file_url = f"http://{SERVER_IP}:{SERVER_PORT}/{download_file_path.lstrip('/')}"
        try:
            self.download_file(file_url, local_file_path)

            self.hashing_file.emit(f"Hashing: {file_path}")
            downloaded_hash = self.calculate_md5(local_file_path).lower()

            if downloaded_hash == expected_hash.lower():
                self.download_state["downloaded_files"][download_file_path] = expected_hash
            else:
                print(f"Erro: O arquivo baixado {download_file_path} está corrompido. Hash esperado: {expected_hash}, Hash baixado: {downloaded_hash}")
                os.remove(local_file_path)
                raise Exception(f"Arquivo {download_file_path} está corrompido após o download.")
        except Exception as e:
            print(f"Falha ao fazer o download de {file_path}: {e}")
            raise
        finally:
            self.save_download_state()

    def download_file(self, url, local_path):
        """Download a file with progress tracking."""
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded_bytes = 0

        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if self.stop_download():
                    raise Exception("Download interrompido pelo jogador")

                if chunk:
                    f.write(chunk)
                    downloaded_bytes += len(chunk)
                    self.total_downloaded_bytes += len(chunk)  # Update total downloaded bytes

                    # Emit progress update
                    self.progress_updated.emit(downloaded_bytes, total_size)

    def save_download_state(self):
        """Save the download state to the state file."""
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        with open(STATE_PATH, "w") as f:
            json.dump(self.download_state, f)

    @staticmethod
    def calculate_md5(file_path):
        """Calculate the MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


class GameLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EPIC Shard Launcher - Beta 1.0")
        self.setGeometry(100, 100, 659, 519)

        # Load background image
        self.background = QPixmap(BACKGROUND_IMAGE_PATH)
        self.background_label = QLabel(self)
        self.background_label.setPixmap(self.background)
        self.background_label.setGeometry(0, 0, 659, 519)

        # Initialize variables
        self.install_path = self.load_install_path()
        self.download_state = self.load_download_state()
        self.stop_download = False
        self.download_thread = None
        self.download_worker = None
        self.download_start_time = None
        self.all_files_downloaded = False
        self.edit_mode = False
        self.total_download_size = 0  # Total size of all files to download

        # Create widgets
        self.create_widgets()

    def load_install_path(self):
        """Load the installation path from the config file."""
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
                return data.get("install_path", "")
        return ""

    def load_download_state(self):
        """Load the download state from the state file."""
        if os.path.exists(STATE_PATH):
            with open(STATE_PATH, "r") as f:
                return json.load(f)
        return {"downloaded_files": {}, "pending_files": []}

    def save_download_state(self):
        """Save the download state to the state file."""
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        with open(STATE_PATH, "w") as f:
            json.dump(self.download_state, f)

    def get_background_color_at(self, x, y):
        """Get the background color at a specific position."""
        try:
            # Convert QPixmap to QImage to access pixel data
            image = self.background.toImage()
            color = QColor(image.pixel(x, y))
            return f"rgb({color.red()}, {color.green()}, {color.blue()})"
        except Exception as e:
            print(f"Failed to get background color: {e}")
            return "black"

    def create_widgets(self):
        """Create all the widgets for the launcher."""
        text_color = "white"
        bg_color = self.get_background_color_at(80, 230)

        # Style for buttons
        button_style = """
            QPushButton {
                background: #800080;
                color: white;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background: #A000A0;
            }
            QPushButton:pressed {
                background: #600060;
            }
        """

        # Server Info
        self.server_info_label = QLabel("Servidor de Download:", self)
        self.server_info_label.setGeometry(385, 400, 200, 20)
        self.server_info_label.setStyleSheet(f"color: {text_color}; background: transparent;")

        self.server_info_text = QLineEdit(f"{SERVER_HOSTNAME}:{SERVER_PORT}", self)
        self.server_info_text.setGeometry(385, 420, 215, 20)
        self.server_info_text.setReadOnly(True)
        self.server_info_text.setStyleSheet(
            f"background: rgba(255, 255, 255, 100); color: {text_color}; border-radius: 5px; padding: 5px;"
        )

        self.edit_save_button = QPushButton(self)
        self.edit_save_button.setGeometry(575, 420, 30, 20)
        self.edit_save_button.setIcon(QIcon(PENCIL_ICON_PATH))
        self.edit_save_button.setStyleSheet(
            "background: transparent; border: none;"
        )
        self.edit_save_button.clicked.connect(self.toggle_edit_mode)

        # Install Path
        self.install_path_label = QLabel("Caminho da Instalação:", self)
        self.install_path_label.setGeometry(50, 400, 200, 20)
        self.install_path_label.setStyleSheet(f"color: {text_color}; background: transparent;")

        self.folder_button = QPushButton(self)
        self.folder_button.setGeometry(45, 420, 30, 20)
        self.folder_button.setIcon(QIcon(FOLDER_ICON_PATH))
        self.folder_button.setStyleSheet( 
            "background: transparent; border: none;"
        )
        self.folder_button.clicked.connect(self.select_install_folder)

        self.path_label = QLabel(self.install_path or "Não definido", self)
        self.path_label.setGeometry(75, 420, 200, 20)
        self.path_label.setStyleSheet(f"color: {text_color}; background: transparent;")

        # Progress Bars
        #self.overall_progress_label = QLabel("Progresso Total:", self)
        #self.overall_progress_label.setGeometry(50, 425, 200, 20)
        #self.overall_progress_label.setStyleSheet(f"color: {text_color}; background: transparent;")

        #self.overall_progress_bar = QProgressBar(self)
        #self.overall_progress_bar.setGeometry(200, 425, 400, 20)
        #self.overall_progress_bar.setStyleSheet(
        #    """
        #    QProgressBar {
        #        border: 1px solid grey;
        #        border-radius: 5px;
        #        background: rgba(255, 255, 255, 100);
        #        text-align: right;
        #        color: white;
        #    }
        #    QProgressBar::chunk {
        #        background: #6c42a7;
        #        border-radius: 5px;
        #    }
        #    """
        #)

        self.file_progress_label = QLabel("Progresso do Arquivo:", self)
        self.file_progress_label.setGeometry(50, 446, 200, 20)
        self.file_progress_label.setStyleSheet(f"color: {text_color}; background: transparent;")

        self.file_progress_bar = QProgressBar(self)
        self.file_progress_bar.setGeometry(200, 446, 400, 20)
        self.file_progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid grey;
                border-radius: 5px;
                background: rgba(255, 255, 255, 100);
                text-align: right;
                color: white;
            }
            QProgressBar::chunk {
                background: #6c42a7;
                border-radius: 5px;
            }
            """
        )

        # Buttons
        self.start_update_button = QPushButton("Patch", self)
        self.start_update_button.setGeometry(250, 330, 150, 50)
        self.start_update_button.setStyleSheet(button_style)
        self.start_update_button.clicked.connect(self.start_update)

        # Loading Animation
        self.loading_label = QLabel(self)
        self.loading_label.setGeometry(43, 470, 20, 20)
        self.loading_label.hide()  # Hide initially

        # Load the loading GIF
        self.loading_movie = QMovie(LOADING_GIF_PATH)
        self.loading_label.setMovie(self.loading_movie)

        # Razor Checkbox
        self.razor_checkbox = QCheckBox("Razor? Desmarque se o client não abrir", self)
        self.razor_checkbox.setGeometry(45, 490, 250, 20)
        self.razor_checkbox.setStyleSheet(f"color: {text_color}; background: transparent;")
        self.razor_checkbox.setChecked(True)  # Enabled by default

        # Close Button
        self.close_button = QPushButton(self)
        self.close_button.setGeometry(580, 20, 30, 30)
        self.close_button.setIcon(QIcon(CLOSE_ICON_PATH))
        self.close_button.setStyleSheet(
            "background: transparent; border: none;"
        )
        self.close_button.clicked.connect(self.close)
        
        # Download Speed Label
        self.download_speed_label = QLabel("", self)
        self.download_speed_label.setGeometry(530, 470, 100, 20)
        self.download_speed_label.setStyleSheet(f"color: white; background: transparent;")
        
        # Current File Label
        self.current_file_label = QLabel("", self)
        self.current_file_label.setGeometry(63, 470, 400, 20)
        self.current_file_label.setStyleSheet(f"color: white; background: transparent;")

    def toggle_edit_mode(self):
        """Toggle edit mode for server info."""
        if not self.edit_mode:
            self.server_info_text.setReadOnly(False)
            self.edit_save_button.setIcon(QIcon(SAVE_ICON_PATH))
            self.edit_mode = True
        else:
            new_server_info = self.server_info_text.text()
            if ":" not in new_server_info:
                QMessageBox.critical(self, "Erro", "Coloque no formato: hostname:porta - exemplo: epic-shard.com:2595")
                return

            try:
                hostname, port = new_server_info.split(":")
                port = int(port)
                if not (0 < port <= 65535):
                    raise ValueError("Porta deve estar entre 1 e 65535")

                global SERVER_HOSTNAME, SERVER_PORT, SERVER_IP
                SERVER_HOSTNAME = hostname
                SERVER_PORT = port
                SERVER_IP = socket.gethostbyname(SERVER_HOSTNAME)
                self.server_info_text.setReadOnly(True)
                self.edit_save_button.setIcon(QIcon(PENCIL_ICON_PATH))
                self.edit_mode = False
            except ValueError as e:
                QMessageBox.critical(self, "Erro", f"Formato inválido: {e}\nColoque no formato: hostname:porta - exemplo: epic-shard.com:2595")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao resolver hostname: {e}")

    def select_install_folder(self):
        """Select the installation folder."""
        folder = QFileDialog.getExistingDirectory(self, "Selecione a pasta de instalação")
        if folder:
            os.makedirs(folder, exist_ok=True)
            self.install_path = folder
            self.path_label.setText(self.install_path)
            self.save_install_path()
            self.start_update_button.setEnabled(True)

    def save_install_path(self):
        """Save the installation path to the config file."""
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump({"install_path": self.install_path}, f)

    def start_update(self):
        """Start the update process."""
        if not self.install_path:
            QMessageBox.critical(self, "Erro", "Não há um diretório de destino selecionado.")
            return

        # Disable the "Patch" button to prevent multiple clicks
        self.start_update_button.setEnabled(False)

        # Show loading animation immediately
        self.loading_label.show()
        self.loading_movie.start()

        # Update the current file label to indicate processing
        self.current_file_label.setText("Calculando tamanho do download... (isso pode demorar alguns segundos)")

        # Initialize variables
        self.stop_download = False
        self.download_start_time = time.time()
        self.total_downloaded_bytes = 0  # Reset total downloaded bytes

        # Create a QThread and DownloadWorker
        self.download_thread = QThread()
        self.download_worker = DownloadWorker(
            self.install_path, self.download_state, lambda: self.stop_download, self.download_start_time
        )
        self.download_worker.moveToThread(self.download_thread)

        # Connect signals and slots
        self.download_worker.progress_updated.connect(self.update_progress)
        self.download_worker.current_file_updated.connect(self.current_file_label.setText)
        self.download_worker.hashing_file.connect(self.current_file_label.setText)
        self.download_worker.download_finished.connect(self.on_download_finished)
        self.download_worker.error_occurred.connect(self.on_download_error)
        #self.download_worker.total_size_calculated.connect(self.set_total_download_size)

        # Start the download thread
        self.download_thread.started.connect(self.download_worker.download_files)
        self.download_thread.start()

    def set_total_download_size(self, total_size):
        """Set the total download size."""
        self.total_download_size = total_size
        print(f"Total download size: {total_size} bytes")


    def on_download_finished(self, success, failed_files):
        """Handle the download finished signal."""
        # Stop the loading animation
        self.loading_movie.stop()
        self.loading_label.hide()

        if success:
            self.all_files_downloaded = True
            self.start_update_button.setText("Seja Épico!")
            self.start_update_button.setEnabled(True)

            # Set overall progress bar to 100%
            # self.overall_progress_bar.setValue(100)

            self.current_file_label.setText("Concluído!")
            self.download_speed_label.setText("")

            if failed_files:
                QMessageBox.information(
                    self,
                    "Info",
                    f"Alguns arquivos falharam no hash (isso pode não ser um problema):\n\n" + "\n".join(failed_files)
                )
            else:
                QMessageBox.information(self, "Sucesso", "Todos os arquivos baixados e validados!")

            # Perform post-download tasks
            self.post_download_tasks()
            
            # Disconnect any previous connections to avoid multiple connections
            try:
                self.start_update_button.clicked.disconnect()
            except TypeError:
                pass  # If no connections exist, ignore the error
            
            # Connect the button to launch the game
            self.start_update_button.clicked.connect(self.launch_game)
        else:
            self.start_update_button.setEnabled(True)

        # Clean up the download thread
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.quit()
            self.download_thread.wait()

    def on_download_error(self, error_message):
        """Handle the download error signal."""
        # Stop the loading animation
        self.loading_movie.stop()
        self.loading_label.hide()

        QMessageBox.critical(self, "Erro de Download", error_message)
        self.start_update_button.setEnabled(True)

    def post_download_tasks(self):
        """Perform tasks after all files are downloaded."""
        self.download_and_extract_razor()
        self.copy_settings_file()
        self.make_classicuo_executable()

    def download_and_extract_razor(self):
        """Download and extract Razor."""
        razor_url = "https://github.com/markdwags/Razor/releases/download/v1.9.77.0/Razor-x64-1.9.77.0.zip"
        razor_zip_path = os.path.join(self.install_path, "ClassicUO", "Data", "Plugins", "Razor-x64-1.9.77.0.zip")
        razor_extract_path = os.path.join(self.install_path, "ClassicUO", "Data", "Plugins", "Razor-x64-1.9.77.0")

        if os.path.exists(razor_extract_path):
            print(f"Razor já existe em {razor_extract_path}. Pulando download e extração.")
            return

        os.makedirs(razor_extract_path, exist_ok=True)

        try:
            urlretrieve(razor_url, razor_zip_path)
            with zipfile.ZipFile(razor_zip_path, 'r') as zip_ref:
                zip_ref.extractall(razor_extract_path)
            os.remove(razor_zip_path)
        except Exception as e:
            print(f"Erro ao baixar ou extrair Razor: {e}")

    def copy_settings_file(self):
        """Copy settings.json file based on Razor checkbox state."""
        razor_enabled = self.razor_checkbox.isChecked()
        settings_src = SETTINGS_PATH if razor_enabled else SETTINGS_NO_RAZOR_PATH
        settings_dest = os.path.join(self.install_path, "ClassicUO", "settings.json")

        if os.path.exists(settings_src):
            os.makedirs(os.path.dirname(settings_dest), exist_ok=True)
            try:
                shutil.copy2(settings_src, settings_dest)
            except Exception as e:
                print(f"Erro ao copiar {os.path.basename(settings_src)}: {e}")
        else:
            print(f"Arquivo {os.path.basename(settings_src)} não encontrado em {settings_src}")

    def make_classicuo_executable(self):
        """Make ClassicUO executable."""
        classicuo_path = os.path.join(self.install_path, "ClassicUO", "ClassicUO.bin.x86_64")
        
        classicuo_file = ""
        if sys.platform.startswith('linux'):
            classicuo_file = "ClassicUO.bin.x86_64"
        elif sys.platform == 'darwin':  # macOS
            classicuo_file = "ClassicUO.bin.osx"
        else:
            print(f"Sistema operacional não suportado: {sys.platform}")
            return
        
        
        classicuo_path = os.path.join(self.install_path, "ClassicUO", classicuo_file)
        if os.path.exists(classicuo_path):
            try:
                os.chmod(classicuo_path, 0o755)
            except Exception as e:
                print(f"Erro ao marcar {classicuo_file} como executável: {e}")
        else:
            print(f"Arquivo {classicuo_file} não encontrado em {classicuo_path}")

    def launch_game(self):
        """Launch the game."""
        # Stop and clean up the download thread before launching the game
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.quit()
            self.download_thread.wait()

        self.copy_settings_file()
        
        classicuo_file = ""
        if sys.platform.startswith('linux'):
            classicuo_file = "ClassicUO.bin.x86_64"
        elif sys.platform == 'darwin':  # macOS
            classicuo_file = "ClassicUO.bin.osx"
        else:
            QMessageBox.critical(self, "Erro", f"Sistema operacional não suportado: {sys.platform}")
            return

        classicuo_path = os.path.join(self.install_path, "ClassicUO", classicuo_file)
        if os.path.exists(classicuo_path):
            try:
                import subprocess
                # Launch the game in a new process
                subprocess.Popen([classicuo_path], cwd=os.path.dirname(classicuo_path))
                print(f"Jogo executado corretamente: {classicuo_path}")
                
                # Start the countdown after launching the game
                self.start_countdown()
            except Exception as e:
                print(f"Falha ao executar o jogo: {e}")
                QMessageBox.critical(self, "Erro", f"Falha ao iniciar o jogo: {e}")
        else:
            print(f"Executavel não encontrado: {classicuo_path}")
            QMessageBox.critical(self, "Erro", f"Arquivo ClassicUO.bin.x86_64 não encontrado em {classicuo_path}")

    def closeEvent(self, event):
        """Handle the window close event."""
        self.stop_download = True

        # Stop and clean up the download thread before closing the application
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.quit()
            self.download_thread.wait()

        self.save_download_state()
        event.accept()

    def start_countdown(self):
        """Disable the 'Seja Épico' button for 15 seconds."""
        self.start_update_button.setEnabled(False)
        self.start_update_button.setText("Seja Épico! (15)")

        def countdown(seconds):
            if seconds > 0:
                self.start_update_button.setText(f"Seja Épico! ({seconds})")
                QTimer.singleShot(1000, lambda: countdown(seconds - 1))
            else:
                self.start_update_button.setText("Seja Épico!")
                self.start_update_button.setEnabled(True)

        countdown(15)

    def update_progress(self, downloaded_bytes, total_bytes):
        """Update progress bars and download speed label."""
        if total_bytes > 0:
            # Update file progress bar
            file_progress = int((downloaded_bytes / total_bytes) * 100)
            self.file_progress_bar.setValue(file_progress)

            # Update overall progress bar
            #if self.total_download_size > 0:
            #    overall_progress = int((self.download_worker.total_downloaded_bytes / self.total_download_size) * 100)
            #    self.overall_progress_bar.setValue(overall_progress)
            #    print(f"Overall progress: {overall_progress}%")

            # Update download speed label
            elapsed_time = time.time() - self.download_start_time
            if elapsed_time > 0:
                download_speed = self.download_worker.total_downloaded_bytes / (1024 * 1024 * elapsed_time)
                self.download_speed_label.setText(f" {download_speed:.2f} MB/s")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = GameLauncher()
    launcher.show()
    sys.exit(app.exec_())
