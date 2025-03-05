import os
import json
import hashlib
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import sys
import shutil
import socket
import zipfile
from urllib.request import urlretrieve
from PIL import Image, ImageTk


BACKGROUND_IMAGE_PATH = os.path.join("media", "fundo_launcher.png")
FOLDER_ICON_PATH = os.path.join("media", "folder.png")
PENCIL_ICON_PATH = os.path.join("media", "pencil.png")
SAVE_ICON_PATH = os.path.join("media", "save.png")

CONFIG_PATH = os.path.expanduser("~/.epic_shard_launcher/config.json")
STATE_PATH = os.path.expanduser("~/.epic_shard_launcher/state.json")
SERVER_HOSTNAME = "epic-shard.com"
SERVER_PORT = 2595
SERVER_IP = socket.gethostbyname(SERVER_HOSTNAME)


class GameLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("EPIC Shard Launcher - Linux Alpha 0.3")

        if os.path.exists(STATE_PATH):
            #print(f"Deleting outdated state file: {STATE_PATH}")
            os.remove(STATE_PATH)


        self.root.geometry("660x520")


        try:
            self.background_image = Image.open(BACKGROUND_IMAGE_PATH)
            self.background_photo = ImageTk.PhotoImage(self.background_image)
        except Exception as e:
            messagebox.showerror("Erro", f"Falhou em carregar imagem de fundo: {e}")
            sys.exit(1)


        try:
            self.folder_icon = Image.open(FOLDER_ICON_PATH)
            self.folder_icon = self.folder_icon.resize((20, 20), Image.Resampling.LANCZOS)
            self.folder_icon = ImageTk.PhotoImage(self.folder_icon)
        except Exception as e:
            messagebox.showerror("Erro", f"Falhou em carregar ícone de pasta: {e}")
            sys.exit(1)


        try:
            self.pencil_icon = Image.open(PENCIL_ICON_PATH)
            self.pencil_icon = self.pencil_icon.resize((15, 15), Image.Resampling.LANCZOS)
            self.pencil_icon = ImageTk.PhotoImage(self.pencil_icon)

            self.save_icon = Image.open(SAVE_ICON_PATH)
            self.save_icon = self.save_icon.resize((15, 15), Image.Resampling.LANCZOS)
            self.save_icon = ImageTk.PhotoImage(self.save_icon)
        except Exception as e:
            messagebox.showerror("Erro", f"Falhou em carregar ícones: {e}")
            sys.exit(1)


        self.canvas = tk.Canvas(root, width=660, height=520)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.background_photo, anchor="nw")


        self.install_path = self.load_install_path()
        self.download_state = self.load_download_state()
        self.stop_download = False
        self.download_thread = None
        self.download_start_time = None
        self.all_files_downloaded = False
        self.edit_mode = False


        self.create_widgets()


        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_install_path(self):

        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
                return data.get("install_path", "")
        return ""

    def load_download_state(self):

        if os.path.exists(STATE_PATH):
            with open(STATE_PATH, "r") as f:
                return json.load(f)
        return {"downloaded_files": {}, "pending_files": []}

    def save_download_state(self):

        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        with open(STATE_PATH, "w") as f:
            json.dump(self.download_state, f)

    def get_background_color_at(self, x, y):


        try:
            pixel_color = self.background_image.getpixel((x, y))

            return f'#{pixel_color[0]:02x}{pixel_color[1]:02x}{pixel_color[2]:02x}'
        except Exception as e:
            #print(f"Failed to get background color: {e}")
            return "black"

    def create_widgets(self):

        text_color = "white"


        bg_color = self.get_background_color_at(80, 230)


        self.server_info_label = tk.Label(
            self.canvas,
            text="Informações do Servidor:",
            fg=text_color,
            bg=bg_color
        )
        self.canvas.create_window(385, 320, window=self.server_info_label, anchor="nw")


        self.server_info_text = tk.Entry(
            self.canvas,
            width=30,
            state="normal"
        )
        self.server_info_text.insert(0, f"{SERVER_HOSTNAME}:{SERVER_PORT}")
        self.server_info_text.config(state="readonly")
        self.canvas.create_window(385, 340, window=self.server_info_text, anchor="nw")


        self.edit_save_button = tk.Label(
            self.canvas,
            image=self.pencil_icon,
            bg=bg_color
        )
        self.edit_save_button.bind("<Button-1>", self.toggle_edit_mode)
        self.canvas.create_window(605, 340, window=self.edit_save_button, anchor="nw")


        self.overall_progress_label = tk.Label(self.canvas, text="Caminho da Instalação:", fg=text_color, bg=bg_color)
        self.canvas.create_window(50, 320, window=self.overall_progress_label, anchor="nw")


        self.folder_button = tk.Label(
            self.canvas,
            image=self.folder_icon,
            bg=bg_color
        )
        self.folder_button.bind("<Button-1>", lambda event: self.select_install_folder())
        self.canvas.create_window(50, 340, window=self.folder_button, anchor="nw")


        self.path_label = tk.Label(
            self.canvas,
            text=self.install_path or "Não definido",
            fg=text_color,
            bg=bg_color
        )
        self.canvas.create_window(80, 340, window=self.path_label, anchor="nw")


        self.start_update_button = ttk.Button(
            self.canvas,
            text="Iniciar Update",
            command=self.start_update,
            state=tk.NORMAL if self.install_path else tk.DISABLED
        )
        self.canvas.create_window(50, 450, window=self.start_update_button, anchor="nw")


        self.stop_button = ttk.Button(
            self.canvas,
            text="Parar Download",
            command=self.stop_update,
            state=tk.DISABLED
        )
        self.canvas.create_window(150, 450, window=self.stop_button, anchor="nw")


        self.razor_checkbox_var = tk.BooleanVar(value=True)
        self.razor_checkbox = ttk.Checkbutton(
            self.canvas,
            variable=self.razor_checkbox_var
        )
        self.canvas.create_window(50, 480, window=self.razor_checkbox, anchor="nw")

        self.razor_label = tk.Label(self.canvas, text="Razor? Desmarque se o client não abrir", fg=text_color, bg=bg_color)
        self.canvas.create_window(65, 480, window=self.razor_label, anchor="nw")


        self.overall_progress_label = tk.Label(self.canvas, text="Progresso Total:", fg=text_color, bg=bg_color)
        self.canvas.create_window(50, 380, window=self.overall_progress_label, anchor="nw")


        self.overall_progress_bar = ttk.Progressbar(self.canvas, orient="horizontal", length=400, mode="determinate")
        self.canvas.create_window(200, 380, window=self.overall_progress_bar, anchor="nw")


        self.file_progress_label = tk.Label(self.canvas, text="Progresso do Arquivo:", fg=text_color, bg=bg_color)
        self.canvas.create_window(50, 400, window=self.file_progress_label, anchor="nw")


        self.file_progress_bar = ttk.Progressbar(self.canvas, orient="horizontal", length=400, mode="determinate")
        self.canvas.create_window(200, 400, window=self.file_progress_bar, anchor="nw")


        self.current_file_label = tk.Label(self.canvas, text="", fg=text_color, bg=bg_color)
        self.canvas.create_window(50, 420, window=self.current_file_label, anchor="nw")


        self.download_speed_label = tk.Label(self.canvas, text="", fg=text_color, bg=bg_color)
        self.canvas.create_window(530, 420, window=self.download_speed_label, anchor="nw")


        close_button = ttk.Button(self.canvas, text="Fechar", command=self.on_close)
        self.canvas.create_window(530, 450, window=close_button, anchor="nw")

    def toggle_edit_mode(self, event):

        if not self.edit_mode:

            self.server_info_text.config(state="normal")
            self.edit_save_button.config(image=self.save_icon)
            self.edit_mode = True
        else:

            new_server_info = self.server_info_text.get()


            if ":" not in new_server_info:
                messagebox.showerror("Erro", "Coloque no formato: hostname:porta - exemplo: epic-shard.com:2595")
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
                self.server_info_text.config(state="readonly")
                self.edit_save_button.config(image=self.pencil_icon)
                self.edit_mode = False
            except ValueError as e:
                messagebox.showerror("Erro",
                                     f"Formato inválido: {e}\nColoque no formato: hostname:porta - exemplo: epic-shard.com:2595")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao resolver hostname: {e}")

    def select_install_folder(self):
        folder = filedialog.askdirectory(mustexist=False)
        if folder:
            os.makedirs(folder, exist_ok=True)
            self.install_path = folder
            self.path_label.config(text=self.install_path)
            self.save_install_path()
            self.start_update_button.config(state=tk.NORMAL)

    def save_install_path(self):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump({"install_path": self.install_path}, f)

    def start_update(self):
        if not self.install_path:
            messagebox.showerror("Erro", "Não há um diretório de destino selecionado.")
            return


        self.start_update_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)


        self.current_file_label.config(text="")
        self.download_speed_label.config(text="")
        self.root.update_idletasks()


        self.stop_download = False
        self.download_thread = threading.Thread(target=self.download_files, daemon=True)
        self.download_thread.start()


        def post_download_tasks():
            self.download_thread.join()
            if self.all_files_downloaded:
                self.download_and_extract_razor()
                self.copy_settings_file()
                self.make_classicuo_executable()
                self.start_update_button.config(command=self.launch_game)


                self.current_file_label.config(text="Concluído!")
                self.download_speed_label.config(text="")
                self.root.update_idletasks()

        threading.Thread(target=post_download_tasks, daemon=True).start()

    def stop_update(self):

        self.stop_download = True
        self.stop_button.config(state=tk.DISABLED)
        self.start_update_button.config(state=tk.NORMAL)
        # messagebox.showinfo("Info", "Processo de download interrompido. Você pode retomar depois.")

    def download_files(self):

        try:

            manifest_url = f"http://{SERVER_IP}:{SERVER_PORT}/Manifest"
            hashes_url = f"http://{SERVER_IP}:{SERVER_PORT}/Hashes"

            manifest_path = os.path.join(self.install_path, "Manifest")
            hashes_path = os.path.join(self.install_path, "Hashes")

            self.download_file(manifest_url, manifest_path)
            self.download_file(hashes_url, hashes_path)


            with open(manifest_path, "r") as f:
                manifest_files = [line.strip() for line in f.readlines() if
                                  line.strip().startswith('/')]

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


            #print("Arquivos no Manifest:", manifest_files)
            #print("Hashes carregados:", hashes)


            pending_files = []
            for file_path in manifest_files:
                if file_path.startswith('/-'):
                    #print(f"Ignorando arquivo {file_path} (inicia com '-')")
                    continue


                dir_path, file_name = os.path.split(file_path)


                if file_name.startswith('+'):
                    download_file_name = file_name[1:]
                    download_file_path = os.path.join(dir_path,
                                                      download_file_name)
                    local_file_path = os.path.join(self.install_path, download_file_path.lstrip('/'))
                else:
                    download_file_path = file_path
                    local_file_path = os.path.join(self.install_path, file_path.lstrip('/'))

                if file_name.startswith('+'):
                    if os.path.exists(local_file_path):
                        #print(f"Arquivo {download_file_path} já existe. Pulando download.")
                        continue

                if download_file_path in self.download_state[
                    "downloaded_files"]:
                    if os.path.exists(local_file_path):
                        current_hash = self.calculate_md5(local_file_path)
                        if current_hash.lower() == self.download_state["downloaded_files"][download_file_path].lower():
                            #print(f"Arquivo {file_path} já está atualizado.")
                            continue
                        else:
                            print(f"Arquivo {file_path} está desatualizado ou corrompido. Rebaixando...")
                    else:
                        print(f"Arquivo {file_path} está faltando. Rebaixando...")
                pending_files.append(file_path)


            self.overall_progress_bar["maximum"] = len(pending_files)
            self.overall_progress_bar["value"] = 0


            failed_files = []


            for i, file_path in enumerate(pending_files):
                if self.stop_download:
                    break


                self.current_file_label.config(text=f"Baixando: {file_path}")
                self.root.update_idletasks()


                try:
                    self.download_or_update_file(file_path, hashes.get(file_path, ""))
                except Exception as e:
                    #print(f"Erro ao processar {file_path}: {e}")
                    failed_files.append(file_path)


                self.overall_progress_bar["value"] = i + 1
                self.root.update_idletasks()


            self.save_download_state()

            if not self.stop_download:
                self.all_files_downloaded = True
                self.start_update_button.config(text="Jogar")
                self.start_update_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)


                self.current_file_label.config(text="Concluído!")
                self.download_speed_label.config(text="")
                self.root.update_idletasks()


                if failed_files:
                    messagebox.showinfo(
                        "Info",
                        f"Alguns arquivos falharam no hash (isso pode não ser um problema):\n\n" + "\n".join(
                            failed_files)
                    )
                else:
                    messagebox.showinfo("Sucesso", "Todos os arquivos baixados e validados!")
        except Exception as e:
            messagebox.showerror("Erro de Download", str(e))

    def download_or_update_file(self, file_path, expected_hash):

        dir_path, file_name = os.path.split(file_path)


        if file_name.startswith('+'):
            download_file_name = file_name[1:]
            download_file_path = os.path.join(dir_path, download_file_name)
            local_file_path = os.path.join(self.install_path, download_file_path.lstrip('/'))
        else:
            download_file_path = file_path
            local_file_path = os.path.join(self.install_path, file_path.lstrip('/'))

        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)


        #print(f"Verificando arquivo: {file_path}")
        #print(f"Hash esperado: {expected_hash}")


        if os.path.exists(local_file_path):

            self.current_file_label.config(text=f"Hashing: {file_path}")
            self.root.update_idletasks()

            current_hash = self.calculate_md5(local_file_path).lower()
            #print(f"Hash atual: {current_hash}")

            if current_hash == expected_hash.lower():
                #print(f"Arquivo {file_path} está atualizado.")

                self.download_state["downloaded_files"][
                    download_file_path] = expected_hash
                self.save_download_state()
                return
            else:
                print(
                    f"Arquivo {file_path} está corrompido ou desatualizado. Hash esperado: {expected_hash}, Hash atual: {current_hash}")


        self.current_file_label.config(text=f"Baixando: {file_path}")
        self.root.update_idletasks()


        file_url = f"http://{SERVER_IP}:{SERVER_PORT}/{download_file_path.lstrip('/')}"
        try:
            #print(f"Baixando arquivo: {file_url}")
            self.download_file(file_url, local_file_path)
            #print(f"Baixado {download_file_path}")


            downloaded_hash = self.calculate_md5(local_file_path).lower()
            #print(f"Hash baixado: {downloaded_hash}")

            if downloaded_hash == expected_hash.lower():

                self.download_state["downloaded_files"][download_file_path] = expected_hash
            else:
                print(
                    f"Erro: O arquivo baixado {download_file_path} está corrompido. Hash esperado: {expected_hash}, Hash baixado: {downloaded_hash}")
                os.remove(local_file_path)
                raise Exception(f"Arquivo {download_file_path} está corrompido após o download.")
        except Exception as e:
            print(f"Falha ao fazer o download de {file_path}: {e}")
            raise
        finally:
            self.save_download_state()

    def download_file(self, url, local_path):
        """Download a file with progress tracking and interrupt support."""
        self.download_start_time = time.time()
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded_bytes = 0

        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if self.stop_download:
                    raise Exception("Download interrompido pelo jogador")

                if chunk:
                    f.write(chunk)
                    downloaded_bytes += len(chunk)


                    if total_size > 0:
                        progress = (downloaded_bytes / total_size) * 100
                        self.file_progress_bar["value"] = progress


                    elapsed_time = time.time() - self.download_start_time
                    if elapsed_time > 0:
                        download_speed = downloaded_bytes / (1024 * 1024 * elapsed_time)
                        self.download_speed_label.config(text=f" {download_speed:.2f} MB/s")

                    self.root.update_idletasks()

    @staticmethod
    def calculate_md5(file_path):

        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def on_close(self):

        self.stop_download = True
        if self.download_thread and self.download_thread.is_alive():
            self.download_thread.join(timeout=1)
        self.save_download_state()
        self.root.destroy()
        sys.exit()

    def copy_settings_file(self):

        razor_enabled = self.razor_checkbox_var.get()
        settings_src = os.path.join("config", "settings.json" if razor_enabled else "settings_no_razor.json")
        settings_dest = os.path.join(self.install_path, "ClassicUO", "settings.json")

        if os.path.exists(settings_src):
            os.makedirs(os.path.dirname(settings_dest), exist_ok=True)
            try:
                shutil.copy2(settings_src, settings_dest)
                #print(f"Arquivo {os.path.basename(settings_src)} copiado para {settings_dest}")
            except Exception as e:
                print(f"Erro ao copiar {os.path.basename(settings_src)}: {e}")
        else:
            print(f"Arquivo {os.path.basename(settings_src)} não encontrado em {settings_src}")

    def make_classicuo_executable(self):

        classicuo_path = os.path.join(self.install_path, "ClassicUO", "ClassicUO.bin.x86_64")
        if os.path.exists(classicuo_path):
            try:
                os.chmod(classicuo_path, 0o755)
                #print(f"Arquivo ClassicUO.bin.x86_64 marcado como executável.")
            except Exception as e:
                print(f"Erro ao marcar ClassicUO.bin.x86_64 como executável: {e}")
        else:
            print(f"Arquivo ClassicUO.bin.x86_64 não encontrado em {classicuo_path}")

    def launch_game(self):


        self.copy_settings_file()

        classicuo_path = os.path.join(self.install_path, "ClassicUO", "ClassicUO.bin.x86_64")
        if os.path.exists(classicuo_path):
            try:
                import subprocess
                subprocess.Popen([classicuo_path], cwd=os.path.dirname(classicuo_path))
                #print(f"Jogo iniciado: {classicuo_path}")
                self.disable_jogar_button()  # Disable the button for 15 seconds
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao iniciar o jogo: {e}")
        else:
            messagebox.showerror("Erro", f"Arquivo ClassicUO.bin.x86_64 não encontrado em {classicuo_path}")


        self.current_file_label.config(text="")
        self.download_speed_label.config(text="")
        self.root.update_idletasks()

    def download_and_extract_razor(self):

        razor_url = "https://github.com/markdwags/Razor/releases/download/v1.9.77.0/Razor-x64-1.9.77.0.zip"
        razor_zip_path = os.path.join(self.install_path, "ClassicUO", "Data", "Plugins", "Razor-x64-1.9.77.0.zip")
        razor_extract_path = os.path.join(self.install_path, "ClassicUO", "Data", "Plugins", "Razor-x64-1.9.77.0")


        if os.path.exists(razor_extract_path):
            print(f"Razor já existe em {razor_extract_path}. Pulando download e extração.")
            return

        os.makedirs(razor_extract_path, exist_ok=True)

        try:

            #print(f"Baixando Razor de {razor_url}...")
            urlretrieve(razor_url, razor_zip_path)
            #print(f"Razor baixado para {razor_zip_path}")


            with zipfile.ZipFile(razor_zip_path, 'r') as zip_ref:
                zip_ref.extractall(razor_extract_path)
            #print(f"Razor extraído para {razor_extract_path}")


            os.remove(razor_zip_path)
            #print(f"Arquivo ZIP removido: {razor_zip_path}")
        except Exception as e:
            print(f"Erro ao baixar ou extrair Razor: {e}")

    def disable_jogar_button(self):

        self.start_update_button.config(state=tk.DISABLED)
        self.start_update_button.config(text="Jogar (15)")

        def countdown(seconds):
            if seconds > 0:
                self.start_update_button.config(text=f"Jogar ({seconds})")
                self.root.after(1000, countdown, seconds - 1)
            else:
                self.start_update_button.config(text="Jogar")
                self.start_update_button.config(state=tk.NORMAL)

        countdown(15)

if __name__ == "__main__":
    root = tk.Tk()
    app = GameLauncher(root)
    root.mainloop()