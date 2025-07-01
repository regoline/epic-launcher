# Sobre

## Epic! Launcher
O [Epic! Launcher](https://epic-shard.com/launcher) é um aplicativo utilizado para fazer o download e manter os arquivos atualizados para se jogar Ultima Online no servidor [Epic! Shard](https://epic-shard.com)
Atualmente o launcher oficial suporta apenas o sistema operacional Windows.

## Epic! Launcher Linux
Ainda que seja possível instalar o Epic! Launcher em outros sistemas operacionais com a ajuda de softwares terceiros (por exemplo, [Wine](https://www.winehq.org/)), a idéia foi criar um software nativo para Linux, que funcionasse como um executável, sem muitas intervenções dos usuários.


<p align="center">
  <img src="https://github.com/user-attachments/assets/aaca649c-55e1-4c89-b477-af1c476bc17c" />
</p>


## Como funciona

Basicamente é um script em Python, utilizando Tk/Tkinter para a parte gráfica, que faz o download dos arquivos do servidor do Epic! Shard.
Ele também faz uma comparação do hash dos arquivos baixados com o hash dos arquivos no servidor e, caso sejam diferentes, efetua o download do novo arquivo, mantendo assim os arquivos atualizados.

Após os arquivos baixados, ele executa o [ClassicUO](https://www.classicuo.eu) nativo do Linux.

> [!NOTE]  
> Ele também gera 2 arquivos e um diretório no seu diretório /home/usuario/
> 
> /home/usuario/.epic_shard_launcher/ - Diretório que armazerá arquivos .json
> 
> /home/usuario/.epic_shard_launcher/state.json que contém os hashes dos arquivos que você baixou
> 
> /home/usuario/.epic_shard_launcher/config.json que vai salvar o diretório que você escolheu para sua instalação.

## Como rodar o binário (releases)

### Versão Beta e Superiores

É preciso ter o Python instalado em sua máquina para rodá-lo.

Para distribuições ubuntu:
```
sudo apt install python3
```

A parte gráfica foi criada usando PyQt5, portanto é necessário instalar os módulos necessários para funcionar:
```
sudo apt install libxcb-xinerama0
sudo apt install libxkbcommon-x11-0
sudo apt install libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xfixes0
sudo apt install libcanberra-gtk-module
```
Com as dependências instaladas, basta executar o binário dando duplo click nele, ou via console rodando ./epic_launcher

### Versão Alpha

É preciso ter o Python e instalado em sua máquina para compilar o programa.

Para distribuições ubuntu:
```
sudo apt install python3
```

Com as dependências instaladas, basta executar o binário dando duplo click nele, ou via console rodando ./epic_launcher


## Como compilar o Epic! Launcher Linux

### Dependências

### Versão Beta e Superiores

É preciso ter o Python e o PIP instalados em sua máquina para compilar o programa.

Para distribuições ubuntu:
```
sudo apt install python3 pip
```

A parte gráfica foi criada usando PyQt5, portanto é necessário instalar os módulos necessários para funcionar:
```
sudo apt install libxcb-xinerama0
sudo apt install libxkbcommon-x11-0
sudo apt install libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xfixes0
sudo apt install libcanberra-gtk-module
```

Como esse aplicativo utiliza alguns módulos do python, é preciso instalá-los também.
```
pip install PyQt5 pyinstaller requests
```

### Versão Alpha

É preciso ter o Python e o PIP instalados em sua máquina para compilar o programa.

Para distribuições ubuntu:
```
sudo apt install python3 pip
```

Como esse aplicativo utiliza alguns módulos do python, é preciso instalá-los também.
```
pip install cx_Freeze pillow requests
```

## Rodando e gerando o executável

### Versão Beta e Superiores

Com as dependências instaladas, você pode rodar o launcher.py:

```
python3 launcher.py
```

Caso queira gerar um executável
```
pyinstaller --name=launcher --onefile --windowed --add-data="media:media" --add-data="config:config" launcher.py
```

Isso gerará uma pasta chamada dist e lá você encontrará o launcher.
Para executar o launcher, dê duplo clique nele, ou execute via linha de comando:

```
./launcher
```


### Versão Alpha

Com as dependências instaladas, você pode rodar o main.py:

```
python3 main.py
```

Caso queira gerar um executável
```
python3 setup.py build
```

Isso gerará uma pasta chamada build e lá você encontrará o launcher.
Para executar o launcher, dê duplo clique nele, ou execute via linha de comando:

```
./launcher
```


## Problemas e limitações conhecidas

1. Caso tenha algum problema em instalar os módulos do Python (eu tive para o pillow) tente criar um venv no diretório onde está o código fonte:

#### Versão Beta e Superiores

```
python3 -m venv epic_launcher_env
source epic_launcher_env/bin/activate
pip install PyQt5 pyinstaller requests
```

#### Versão Alpha

```
python3 -m venv epic_launcher_env
source epic_launcher_env/bin/activate
pip install cx_Freeze pillow requests
```

2. Atualmente ele está rodando a versão 1.0.0 do ClassicUO que não é a mais recente. Mas essa é a versão que é baixada do servidor.

3. Ele usa o ClassicUO e não o ZanUO (Cliente utilizado pelo Epic! Launcher para Windows), portanto algumas funcionalidades podem faltar.

4. Alguns erros de hashing podem acontecer, pois não batem com o hash do servidor, mas isso não deve ser um problema por hora e está fora do alcance desse software (a tabela de hash do lado do servidor parece estar desatualizada)
 
### Erros de driver / visualização

Caso receba o erro:
```
MESA: error: ZINK: failed to choose pdev
glx: failed to create drisw screen
```

Você pode tentar atualizar as bibliotecas do mesa/glx (sob sua conta e risco)
```
sudo apt install libgl1-mesa-glx libgl1-mesa-dri libglu1-mesa
sudo apt install mesa-utils
```

### Verifique seus drivers gráficos!

Para GPUs Intel: 
```
sudo apt install xserver-xorg-video-intel
```

Para GPUs NVIDIA:
```
sudo apt install nvidia-driver-<version>
```

Para GPUs AMD:

```
sudo apt install xserver-xorg-video-amdgpu
```


## Instalação do Razor

O [Razor](https://www.razorce.com) é um aplicativo que permite aos jogadores mais funções dentro do Ultima Online, inclusive programar macros para tarefas mais complexas ou repetitivas.
O Epic! Launcher - Linux possui uma opção (marcada por padrão) que já faz o download da versão 1.9.77.0 do Razor e o deixa configurado para executá-lo.

No entanto, para que o Razor funciona é necessário que o usuário siga os passos disponíveis no [site oficial](https://www.razorce.com/install/linux/).

De qualquer maneira, aqui estão os passos para Ubuntu (e derivações):

### Instalar o Mono

Abra a console e adicione o repositório do Mono ao sistema

```
sudo apt install gnupg ca-certificates
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF
echo "deb https://download.mono-project.com/repo/ubuntu stable-bionic main" | sudo tee /etc/apt/sources.list.d/mono-official-stable.list
sudo apt update
```

Instale a última versão do Mono
```
sudo apt install -y mono-complete
```

Execute os comandos abaixo na console

```
sudo apt-get install -y libmono-system-windows-forms4.0-cil
sudo apt-get install -y libmono-system-net-http4.0-cil
sudo apt-get install -y libmono-system-runtime-serialization4.0-cil
```

### Instalar libz

```
sudo apt-get install -y libz-dev
```

Com esses passos sendo executados, o Razor deve abrir um pouco antes do ClassicUO.

## Agradecimentos

- [Epic! Shard](https://epic-shard.com) por fazer esse jogo fantástico.
- [@IgorTurano](https://github.com/igorrturano) por me deixar fazer isso, sem nem pedir :P
- [DeepSeek](https://deepseek.com) por me ajudar com as dúvidas
- [Iconoir](https://iconoir.com) pelos icones que usei e usarei.

