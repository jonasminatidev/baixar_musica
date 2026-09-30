import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import logging

def format_duration(ms: int) -> str:
    """Converte milissegundos para o formato MM:SS."""
    if not ms:
        return "00:00"
    seconds = int((ms / 1000) % 60)
    minutes = int((ms / (1000 * 60)) % 60)
    return f"{minutes:02d}:{seconds:02d}"

def search_artist_spotify(artist_name: str, client_id: str, client_secret: str) -> dict:
    """Busca discografia completa usando a API oficial do Spotify via Spotipy."""
    try:
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        # Busca artista
        results = sp.search(q=artist_name, type='artist', limit=1)
        items = results.get('artists', {}).get('items', [])
        if not items:
            return None
            
        artist = items[0]
        artist_id = artist['id']
        artist_info = {
            'name': artist['name'],
            'image_url': artist['images'][0]['url'] if artist.get('images') else None,
            'genres': ", ".join(artist.get('genres', [])[:3]),
            'popularity': artist.get('popularity', 0),
            'source': 'Spotify'
        }
        
        # Busca álbuns do artista (álbuns, singles, compilizações)
        albums = []
        album_types = ['album', 'single', 'compilation']
        for atype in album_types:
            res = sp.artist_albums(artist_id, album_type=atype, limit=50)
            albums.extend(res.get('items', []))
            while res.get('next'):
                res = sp.next(res)
                albums.extend(res.get('items', []))
                
        # Deduplica álbuns pelo ID
        seen_album_ids = set()
        unique_albums = []
        for alb in albums:
            if alb['id'] not in seen_album_ids:
                seen_album_ids.add(alb['id'])
                unique_albums.append(alb)
                
        all_tracks = []
        seen_track_signatures = set()
        
        for alb in unique_albums:
            cover_url = alb['images'][0]['url'] if alb.get('images') else None
            album_name = alb['name']
            album_type = alb.get('album_type', 'album')
            release_date = alb.get('release_date', '')[:4]
            
            # Busca faixas do álbum
            t_res = sp.album_tracks(alb['id'], limit=50)
            t_items = t_res.get('items', [])
            while t_res.get('next'):
                t_res = sp.next(t_res)
                t_items.extend(t_res.get('items', []))
                
            for track in t_items:
                track_title = track['name']
                sig = f"{track_title.lower()}||{album_name.lower()}"
                if sig in seen_track_signatures:
                    continue
                seen_track_signatures.add(sig)
                
                all_tracks.append({
                    'id': f"sp_{track['id']}",
                    'title': track_title,
                    'artist': artist['name'],
                    'album': album_name,
                    'album_type': album_type,
                    'release_date': release_date,
                    'cover_url': cover_url,
                    'duration_ms': track.get('duration_ms', 0),
                    'duration_str': format_duration(track.get('duration_ms', 0)),
                    'track_number': track.get('track_number', 1),
                    'source': 'Spotify'
                })
                
        return {
            'artist': artist_info,
            'tracks': all_tracks
        }
    except Exception as e:
        logging.error(f"Erro na API do Spotify: {e}")
        return None

def search_artist_itunes(artist_name: str) -> dict:
    """Busca faixas do artista via API pública do iTunes (fallback sem necessidade de chaves)."""
    try:
        url = f"https://itunes.apple.com/search?term={requests.utils.quote(artist_name)}&entity=song&limit=200"
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None
            
        data = resp.json()
        results = data.get('results', [])
        if not results:
            return None
            
        # Filtra pelo artista mais relevante
        exact_artist = results[0]['artistName']
        artist_img = results[0].get('artworkUrl100', '').replace('100x100bb', '600x600bb')
        
        artist_info = {
            'name': exact_artist,
            'image_url': artist_img,
            'genres': results[0].get('primaryGenreName', 'Música'),
            'popularity': 80,
            'source': 'iTunes API (Fallback)'
        }
        
        tracks = []
        seen_sigs = set()
        
        for r in results:
            # Garante que pertence ao artista (ou colaboração)
            if artist_name.lower() not in r.get('artistName', '').lower() and exact_artist.lower() not in r.get('artistName', '').lower():
                continue
                
            title = r.get('trackName', '')
            album = r.get('collectionName', 'Single / Álbum Desconhecido')
            sig = f"{title.lower()}||{album.lower()}"
            if sig in seen_sigs:
                continue
            seen_sigs.add(sig)
            
            cover = r.get('artworkUrl100', '').replace('100x100bb', '600x600bb')
            release = r.get('releaseDate', '')[:4]
            dur_ms = r.get('trackTimeMillis', 0)
            
            tracks.append({
                'id': f"itunes_{r.get('trackId', hash(title))}",
                'title': title,
                'artist': r.get('artistName', exact_artist),
                'album': album,
                'album_type': 'album',
                'release_date': release,
                'cover_url': cover,
                'duration_ms': dur_ms,
                'duration_str': format_duration(dur_ms),
                'track_number': r.get('trackNumber', 1),
                'source': 'iTunes API'
            })
            
        return {
            'artist': artist_info,
            'tracks': tracks
        }
    except Exception as e:
        logging.error(f"Erro na API do iTunes: {e}")
        return None

def get_artist_discography(artist_name: str, spotify_client_id: str = None, spotify_client_secret: str = None) -> dict:
    """
    Função principal de busca.
    Tenta primeiro o Spotify API se as credenciais estiverem preenchidas.
    Faz fallback para iTunes API automaticamente se necessário.
    """
    if spotify_client_id and spotify_client_secret:
        spotify_res = search_artist_spotify(artist_name, spotify_client_id, spotify_client_secret)
        if spotify_res and spotify_res.get('tracks'):
            return spotify_res
            
    # Fallback
    itunes_res = search_artist_itunes(artist_name)
    if itunes_res and itunes_res.get('tracks'):
        return itunes_res
        
    return None
