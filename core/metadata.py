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

def search_spotify(query: str, client_id: str, client_secret: str) -> dict:
    """Busca artista ou música usando a API oficial do Spotify."""
    try:
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        # Tenta primeiro como artista
        results = sp.search(q=query, type='artist', limit=1)
        items = results.get('artists', {}).get('items', [])
        
        if items:
            artist = items[0]
            artist_id = artist['id']
            artist_info = {
                'name': artist['name'],
                'image_url': artist['images'][0]['url'] if artist.get('images') else None,
                'genres': ", ".join(artist.get('genres', [])[:3]),
                'popularity': artist.get('popularity', 0),
                'source': 'Spotify API'
            }
            
            albums = []
            album_types = ['album', 'single', 'compilation']
            for atype in album_types:
                res = sp.artist_albums(artist_id, album_type=atype, limit=50)
                albums.extend(res.get('items', []))
                while res.get('next'):
                    res = sp.next(res)
                    albums.extend(res.get('items', []))
                    
            seen_album_ids = set()
            unique_albums = [alb for alb in albums if not (alb['id'] in seen_album_ids or seen_album_ids.add(alb['id']))]
            
            all_tracks = []
            seen_sigs = set()
            
            for alb in unique_albums:
                cover_url = alb['images'][0]['url'] if alb.get('images') else None
                album_name = alb['name']
                album_type = alb.get('album_type', 'album')
                release_date = alb.get('release_date', '')[:4]
                
                t_res = sp.album_tracks(alb['id'], limit=50)
                t_items = t_res.get('items', [])
                while t_res.get('next'):
                    t_res = sp.next(t_res)
                    t_items.extend(t_res.get('items', []))
                    
                for track in t_items:
                    track_title = track['name']
                    sig = f"{track_title.lower()}||{album_name.lower()}"
                    if sig in seen_sigs:
                        continue
                    seen_sigs.add(sig)
                    
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
                        'source': 'Spotify API'
                    })
                    
            return {'artist': artist_info, 'tracks': all_tracks}
            
        # Se não encontrou artista, busca como música específica
        t_search = sp.search(q=query, type='track', limit=50)
        t_items = t_search.get('tracks', {}).get('items', [])
        if not t_items:
            return None
            
        first_track = t_items[0]
        artist_info = {
            'name': f"Busca: '{query}'",
            'image_url': first_track['album']['images'][0]['url'] if first_track['album'].get('images') else None,
            'genres': 'Música Específica',
            'popularity': 90,
            'source': 'Spotify API'
        }
        
        all_tracks = []
        seen_sigs = set()
        for track in t_items:
            track_title = track['name']
            art_name = track['artists'][0]['name'] if track.get('artists') else 'Desconhecido'
            alb_name = track['album']['name']
            sig = f"{track_title.lower()}||{art_name.lower()}||{alb_name.lower()}"
            if sig in seen_sigs:
                continue
            seen_sigs.add(sig)
            
            all_tracks.append({
                'id': f"sp_{track['id']}",
                'title': track_title,
                'artist': art_name,
                'album': alb_name,
                'album_type': track['album'].get('album_type', 'album'),
                'release_date': track['album'].get('release_date', '')[:4],
                'cover_url': track['album']['images'][0]['url'] if track['album'].get('images') else None,
                'duration_ms': track.get('duration_ms', 0),
                'duration_str': format_duration(track.get('duration_ms', 0)),
                'track_number': track.get('track_number', 1),
                'source': 'Spotify API'
            })
            
        return {'artist': artist_info, 'tracks': all_tracks}
    except Exception as e:
        logging.error(f"Erro na API do Spotify: {e}")
        return None

def search_itunes(query: str) -> dict:
    """Busca artista ou música específica via API pública do iTunes (fallback sem necessidade de chaves)."""
    try:
        url = f"https://itunes.apple.com/search?term={requests.utils.quote(query)}&entity=song&limit=200"
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None
            
        data = resp.json()
        results = data.get('results', [])
        if not results:
            return None
            
        # Determina o nome principal do cabeçalho
        first_artist = results[0]['artistName']
        query_lower = query.lower()
        
        # Verifica se o termo procurado é mais próximo de um artista ou de um título de música
        is_artist_match = any(query_lower in r.get('artistName', '').lower() for r in results[:5])
        
        if is_artist_match:
            header_name = first_artist
            genres = results[0].get('primaryGenreName', 'Música')
        else:
            header_name = f"Resultados para: '{query}'"
            genres = "Música / Faixa Específica"
            
        artist_img = results[0].get('artworkUrl100', '').replace('100x100bb', '600x600bb')
        
        artist_info = {
            'name': header_name,
            'image_url': artist_img,
            'genres': genres,
            'popularity': 85,
            'source': 'iTunes API (Fallback)'
        }
        
        tracks = []
        seen_sigs = set()
        
        for r in results:
            title = r.get('trackName', '')
            art_name = r.get('artistName', first_artist)
            album = r.get('collectionName', 'Single / Álbum Desconhecido')
            
            sig = f"{title.lower()}||{art_name.lower()}||{album.lower()}"
            if sig in seen_sigs:
                continue
            seen_sigs.add(sig)
            
            cover = r.get('artworkUrl100', '').replace('100x100bb', '600x600bb')
            release = r.get('releaseDate', '')[:4]
            dur_ms = r.get('trackTimeMillis', 0)
            
            tracks.append({
                'id': f"itunes_{r.get('trackId', hash(title))}",
                'title': title,
                'artist': art_name,
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

def get_artist_discography(query: str, spotify_client_id: str = None, spotify_client_secret: str = None) -> dict:
    """
    Busca discografia completa de um artista OU uma música específica.
    Tenta o Spotify API primeiro se as credenciais estiverem preenchidas, ou faz fallback para o iTunes.
    """
    if spotify_client_id and spotify_client_secret:
        sp_res = search_spotify(query, spotify_client_id, spotify_client_secret)
        if sp_res and sp_res.get('tracks'):
            return sp_res
            
    itunes_res = search_itunes(query)
    if itunes_res and itunes_res.get('tracks'):
        return itunes_res
        
    return None
