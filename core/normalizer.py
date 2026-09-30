import re
import unicodedata

def remove_accents(input_str: str) -> str:
    """Remove acentos de uma string."""
    if not input_str:
        return ""
    nfkd_form = unicodedata.normalize('NFD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def get_version_tags(title: str, album: str = "") -> list:
    """Detecta tags de versão (Ao Vivo, Acústico, Remix, Remaster, etc.) no título ou álbum."""
    text = remove_accents(f"{title} {album}").lower()
    tags = []
    
    if re.search(r'\b(ao vivo|live|en vivo)\b', text):
        tags.append("Ao Vivo")
    if re.search(r'\b(acustico|acoustic|unplugged)\b', text):
        tags.append("Acústico")
    if re.search(r'\b(remix|mixed|club edit)\b', text):
        tags.append("Remix")
    if re.search(r'\b(remaster|remastered|remasterizado)\b', text):
        tags.append("Remaster")
    if re.search(r'\b(radio edit|short edit)\b', text):
        tags.append("Radio Edit")
    if re.search(r'\b(instrumental|karaoke|backing track)\b', text):
        tags.append("Instrumental")
    if re.search(r'\b(deluxe|expanded|anniversary|especial)\b', text):
        tags.append("Deluxe")
    if re.search(r'\b(demo|early version)\b', text):
        tags.append("Demo")
    
    if not tags:
        tags.append("Estúdio / Versão Padrão")
        
    return tags

def normalize_title(title: str) -> str:
    """
    Normaliza o título da música para agrupar variações sob um mesmo nome base.
    Exemplo: 'Evidências (Ao Vivo - 2019)' -> 'evidencias'
    """
    text = remove_accents(title).lower()
    
    # Remove textos entre parênteses ou colchetes contendo palavras-chave comuns de versão
    pattern_parentheses = r'[\(\[\{].*?\b(live|ao vivo|remix|remaster|remastered|remasterizado|acoustic|acustico|deluxe|version|versao|edit|radio edit|instrumental|bonus|demo|extended|mix|feat|ft|part)\b.*?[\)\]\}]'
    text = re.sub(pattern_parentheses, '', text, flags=re.IGNORECASE)
    
    # Remove sufixos após hífen contendo termos de versão
    pattern_dash = r'-\s*.*?\b(live|ao vivo|remix|remaster|remastered|remasterizado|acoustic|acustico|deluxe|version|versao|edit|radio edit|instrumental|bonus|demo|extended|mix|feat|ft|part)\b.*$'
    text = re.sub(pattern_dash, '', text, flags=re.IGNORECASE)
    
    # Remove ano (ex: 2019, 1995) se isolado
    text = re.sub(r'\b(19|20)\d{2}\b', '', text)
    
    # Remove pontuação residual
    text = re.sub(r'[^\w\s]', '', text)
    
    # Remove espaços extras
    text = ' '.join(text.split())
    
    return text

def group_tracks_by_base_song(tracks: list) -> dict:
    """
    Agrupa uma lista de dicionários de faixas pelo seu título normalizado.
    Retorna um dicionário:
    {
        'canonical_key': {
            'display_title': 'Evidências',
            'versions': [
                { 'id': '...', 'title': '...', 'album': '...', 'version_label': 'Estúdio / Versão Padrão', 'is_default': True, ... },
                { 'id': '...', 'title': '...', 'album': '...', 'version_label': 'Ao Vivo', 'is_default': False, ... },
            ]
        }
    }
    """
    groups = {}
    
    for track in tracks:
        raw_title = track.get('title', '').strip()
        album_name = track.get('album', '').strip()
        
        if not raw_title:
            continue
            
        canonical_key = normalize_title(raw_title)
        if not canonical_key:
            canonical_key = remove_accents(raw_title).lower().strip()
            
        tags = get_version_tags(raw_title, album_name)
        version_label = ", ".join(tags)
        
        # Copia dados da faixa e enriquece com version_label
        track_info = dict(track)
        track_info['version_label'] = version_label
        track_info['canonical_key'] = canonical_key
        
        if canonical_key not in groups:
            groups[canonical_key] = {
                'display_title': raw_title,
                'canonical_key': canonical_key,
                'versions': []
            }
            
        groups[canonical_key]['versions'].append(track_info)
        
    # Pós-processamento para definir título de exibição limpo e sugestão padrão para cada grupo
    for key, group in groups.items():
        versions = group['versions']
        
        # Ordenação prioritária:
        # 1. Versão de estúdio original (álbum padrão, sem "ao vivo" ou "remix" no título)
        # 2. Álbum do tipo 'album' > 'single' > 'compilation'
        # 3. Data de lançamento mais antiga
        def priority_score(v):
            is_studio = 1 if "Estúdio" in v['version_label'] else 0
            album_type = v.get('album_type', 'album').lower()
            album_score = 3 if album_type == 'album' else (2 if album_type == 'single' else 1)
            release_date = str(v.get('release_date', '9999'))
            title_length = len(v.get('title', ''))
            return (-is_studio, -album_score, release_date, title_length)
            
        versions.sort(key=priority_score)
        
        # O melhor título de exibição é o do primeiro candidato (mais limpo/estúdio)
        best_title = versions[0]['title']
        # Tenta pegar versão limpa sem sufixos
        clean_best = re.sub(r'[\(\[\{].*?[\)\]\}]', '', best_title).split(' - ')[0].strip()
        if len(clean_best) >= 2:
            group['display_title'] = clean_best
        else:
            group['display_title'] = best_title
            
        # Marca a primeira como a sugestão selecionada por padrão
        for i, v in enumerate(versions):
            v['is_default'] = (i == 0)
            
    return groups
