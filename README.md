# 🎵 Music Vault & Curator

> Sistema automatizado para busca, agrupamento inteligente e download de discografias completas de artistas, com filtro de duplicidades e curadoria de versões.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red?logo=streamlit)
![yt-dlp](https://img.shields.io/badge/yt--dlp-2026.8-green)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Supported-black?logo=ffmpeg)

---

## 🎯 Sobre o Projeto

Este projeto resolve o problema clássico de baixar a discografia de um artista e acabar com arquivos repetidos em diferentes versões (*Ao Vivo*, *Acústico*, *Remix*, *Remaster*, etc.).

O programa coleta os metadados oficiais do artista, normaliza os títulos usando expressões regulares e inteligência de agrupamento, permitindo que você decida exatamente qual versão deseja baixar antes de gerar os arquivos **MP3** com capas de álbum e tags ID3 completas.

---

## ✨ Funcionalidades

- **Coleta Inteligente de Metadados**: Integração nativa com a API do **Spotify** (via `spotipy`) e fallback automático para **iTunes/Deezer API** (sem necessidade de chaves).
- **Engine de Agrupamento & Normalização**: Identifica e agrupa faixas idênticas sob um nome base limpo (ex: *"Evidências (Ao Vivo)"* e *"Evidências (Remastered)"* agrupadas sob *"Evidências"*).
- **Interface Web Moderna (Streamlit)**: Menu expansível por música com seleção por rádio/checkbox, filtros rápidos (*Apenas Estúdio*, *Padrão*, *Desmarcar*) e capas dos álbuns.
- **Interface de Linha de Comando (CLI)**: Opção para rodar diretamente no terminal.
- **Automação de Download (yt-dlp + FFmpeg)**: Converte áudio para **MP3 192kbps** com prevenção contra erros HTTP 403.
- **Tagging ID3 Automático**: Incorpora Título, Artista, Álbum, Ano e a Capa Frontal do álbum direto no arquivo MP3.

---

## 📁 Estrutura do Projeto

```text
Baixador de Musicas Artistas/
├── core/
│   ├── metadata.py       # Busca de discografia no Spotify / iTunes
│   ├── normalizer.py     # Engine de agrupamento e limpeza de nomes
│   └── downloader.py     # Download via yt-dlp, conversão FFmpeg e ID3 tagging
├── app.py                # Interface Web interativa em Streamlit
├── cli.py                # Interface interativa de linha de comando
├── plano.txt             # Especificação técnica do projeto
├── requirements.txt      # Dependências Python
└── README.md             # Documentação oficial
```

---

## 🚀 Como Executar

### 1. Pré-requisitos
- **Python 3.10+** instalado.
- **FFmpeg** instalado e adicionado às variáveis de ambiente (PATH).

### 2. Instalação
Clone este repositório e instale as dependências:
```bash
git clone https://github.com/jonasminatidev/baixar_musica.git
cd baixar_musica
pip install -r requirements.txt
```

### 3. Execução

#### 🌐 Interface Web (Streamlit):
```bash
streamlit run app.py
```
Acesse `http://localhost:8501` no seu navegador.

#### 💻 Interface de Linha de Comando (CLI):
```bash
python cli.py
```

---

## 📜 Licença

Este projeto é disponibilizado sob a licença [MIT](LICENSE).
