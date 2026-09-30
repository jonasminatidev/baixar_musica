import os
import re
import requests
import yt_dlp
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, APIC, ID3NoHeaderError
import logging

def sanitize_filename(filename: str) -> str:
    """Remove caracteres inválidos para nomes de arquivos no Windows/Linux."""
    return re.sub(r'[\\/*?:"<>|]', "", filename).strip()

def embed_metadata(mp3_filepath: str, title: str, artist: str, album: str, release_date: str = "", cover_url: str = None):
    """Insere metadados ID3 (título, artista, álbum, ano e capa) no arquivo MP3."""
    try:
        try:
            audio = MP3(mp3_filepath, ID3=ID3)
        except ID3NoHeaderError:
            audio = MP3(mp3_filepath)
            audio.add_tags()
            
        tags = audio.tags
        
        tags.add(TIT2(encoding=3, text=title))
        tags.add(TPE1(encoding=3, text=artist))
        if album:
            tags.add(TALB(encoding=3, text=album))
        if release_date:
            tags.add(TDRC(encoding=3, text=str(release_date)))
            
        # Baixa e insere a capa se fornecida
        if cover_url:
            try:
                img_data = requests.get(cover_url, timeout=10).content
                tags.add(APIC(
                    encoding=3,
                    mime='image/jpeg' if cover_url.lower().endswith(('.jpg', '.jpeg')) else 'image/png',
                    type=3,  # Front Cover
                    desc=u'Cover',
                    data=img_data
                ))
            except Exception as e:
                logging.warning(f"Não foi possível incorporar capa do álbum: {e}")
                
        audio.save()
    except Exception as e:
        logging.error(f"Erro ao inserir metadados no arquivo {mp3_filepath}: {e}")

def download_track(track_info: dict, artist_name: str, download_dir: str, progress_hook=None) -> dict:
    """
    Baixa uma faixa específica via yt-dlp, converte para MP3 com FFmpeg e aplica tags ID3.
    """
    try:
        title = track_info.get('title', 'Musica')
        album = track_info.get('album', '')
        version_label = track_info.get('version_label', '')
        cover_url = track_info.get('cover_url')
        release_date = track_info.get('release_date', '')
        
        # Cria diretório específico para o artista
        artist_folder_name = sanitize_filename(artist_name)
        target_dir = os.path.join(download_dir, artist_folder_name)
        os.makedirs(target_dir, exist_ok=True)
        
        # Nome limpo do arquivo
        clean_title = sanitize_filename(title)
        # Se for versão diferente de estúdio padrão, adiciona sufixo ao nome do arquivo
        if "Estúdio" not in version_label and version_label:
            clean_filename = f"{clean_title} ({sanitize_filename(version_label)}).mp3"
        else:
            clean_filename = f"{clean_title}.mp3"
            
        output_filepath = os.path.join(target_dir, clean_filename)
        
        # Se o arquivo já existe, pula o download
        if os.path.exists(output_filepath) and os.path.getsize(output_filepath) > 100000:
            return {
                'status': 'already_exists',
                'file_path': output_filepath,
                'title': title,
                'message': 'Arquivo já existente'
            }
            
        # Termo de busca no YouTube
        search_query = f"ytsearch1:{artist_name} - {title} audio"
        if "Estúdio" not in version_label and version_label:
            search_query = f"ytsearch1:{artist_name} - {title} {version_label} audio"
            
        # Configurações do yt-dlp otimizadas contra bloqueios HTTP 403 do YouTube
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(target_dir, f"%(title)s.%(ext)s"),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web', 'mweb', 'ios'],
                    'player_skip': ['configs', 'webpage']
                }
            },
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        if progress_hook:
            ydl_opts['progress_hooks'] = [progress_hook]
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=True)
            if 'entries' in info and len(info['entries']) > 0:
                downloaded_file = ydl.prepare_filename(info['entries'][0])
                base_path, _ = os.path.splitext(downloaded_file)
                downloaded_mp3 = base_path + ".mp3"
                
                # Renomeia para o nome padronizado
                if os.path.exists(downloaded_mp3):
                    if downloaded_mp3 != output_filepath:
                        if os.path.exists(output_filepath):
                            os.remove(output_filepath)
                        os.rename(downloaded_mp3, output_filepath)
                elif os.path.exists(downloaded_file):
                    # Fallback caso a extensão não tenha mudado
                    os.rename(downloaded_file, output_filepath)
            else:
                return {
                    'status': 'error',
                    'title': title,
                    'message': 'Nenhum resultado encontrado no YouTube'
                }
                
        # Insere metadados (capa, artista, álbum, ano)
        embed_metadata(
            mp3_filepath=output_filepath,
            title=title,
            artist=artist_name,
            album=album,
            release_date=release_date,
            cover_url=cover_url
        )
        
        return {
            'status': 'success',
            'file_path': output_filepath,
            'title': title,
            'message': 'Download concluído com sucesso'
        }
    except Exception as e:
        logging.error(f"Erro no download da faixa {track_info.get('title')}: {e}")
        return {
            'status': 'error',
            'title': track_info.get('title', 'Faixa'),
            'message': str(e)
        }
