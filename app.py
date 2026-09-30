import os
import sys
import base64
import subprocess
import streamlit as st
from PIL import Image

# Importa módulos internos do core
from core.metadata import get_artist_discography
from core.normalizer import group_tracks_by_base_song
from core.downloader import download_track

# Carrega o ícone personalizado do projeto
_favicon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "musica.ico")
_favicon = Image.open(_favicon_path) if os.path.exists(_favicon_path) else "🎵"

# Configuração da Página
st.set_page_config(
    page_title="Baixa Música - Download Inteligente",
    page_icon=_favicon,
    layout="wide",
    initial_sidebar_state="expanded"
)

def open_native_folder_dialog(current_path: str) -> str:
    """
    Abre o explorador de arquivos nativo do Windows usando PowerShell.
    Usa script .ps1 externo com flag -STA (obrigatório no Windows 10 para diálogos de UI).
    """
    try:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts", "folder_picker.ps1")
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-STA", "-File", script_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=60
        )
        selected = proc.stdout.strip()
        if selected and selected != "CANCELLED" and os.path.exists(selected):
            return selected
    except subprocess.TimeoutExpired:
        pass
    except Exception as e:
        st.error(f"Erro ao abrir o navegador de arquivos: {e}")
    return current_path

# Injeção de Tipografia Inter & Design System Sóbrio/Minimalista
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>
    /* Tipografia Padrão Inter */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: #e2e8f0;
    }

    /* Fundo Global Escuro e Sóbrio */
    .stApp {
        background-color: #0b0f19 !important;
        background-image: none !important;
    }
    
    /* Esconde apenas Deploy, Running e Menu hamburger do Streamlit */
    .stDeployButton,
    [data-testid="stStatusWidget"],
    #MainMenu {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Torna o header transparente mas mantém o botão da sidebar acessível */
    header[data-testid="stHeader"] {
        background: transparent !important;
        border: none !important;
    }
    
    /* Remove overlay fosco ao abrir a sidebar */
    div[data-testid="stOverlay"] {
        display: none !important;
    }
    
    /* Cabeçalho Minimalista Integrado */
    .header-container {
        padding: 0.5rem 0 1.5rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 2rem;
    }
    .header-title {
        font-size: 1.85rem;
        font-weight: 700;
        color: #f8fafc;
        letter-spacing: -0.02em;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .header-subtitle {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-top: 0.3rem;
        font-weight: 400;
    }

    /* Card do Artista Sóbrio */
    .artist-card {
        background: #131926 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.5rem;
        display: flex;
        gap: 1.5rem;
        align-items: center;
    }
    .artist-img {
        width: 90px;
        height: 90px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid rgba(255, 255, 255, 0.15);
    }
    .artist-name {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f8fafc;
        margin: 0;
    }
    .artist-meta {
        font-size: 0.875rem;
        color: #94a3b8;
        margin-top: 0.25rem;
    }
    
    /* Cards de Métricas Minimalistas */
    .metric-card {
        background: #131926 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #f8fafc;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #94a3b8;
        font-weight: 500;
        margin-top: 0.2rem;
    }
    
    /* Badges Sóbrias */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.2rem 0.6rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.06);
        color: #cbd5e1;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Campos de Entrada (Inputs) */
    .stTextInput input {
        background-color: #131926 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        color: #f8fafc !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus {
        border-color: #3b82f6 !important;
        box-shadow: none !important;
    }
    
    /* Padronização dos Botões */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        background-color: #1e293b !important;
        color: #f8fafc !important;
        transition: all 0.15s ease-in-out !important;
    }
    .stButton>button:hover {
        background-color: #334155 !important;
        border-color: rgba(255, 255, 255, 0.25) !important;
    }
    
    /* Botão Principal de Ação (Azul Sóbrio) */
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background-color: #1d4ed8 !important;
    }
    
    /* Ajustes dos Expander Accordions */
    div[data-testid="stExpander"] {
        background-color: #131926 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# Cabeçalho Minimalista Integrado ao Fundo (Fim da faixa roxa)
st.markdown("""
<div class="header-container">
    <div class="header-title">
        <i class="fa-solid fa-compact-disc" style="color: #64748b;"></i> Baixa Música
    </div>
    <div class="header-subtitle">
        Download inteligente de discografias completas e faixas avulsas • Agrupamento sem repetições
    </div>
</div>
""", unsafe_allow_html=True)

# Inicialização da Pasta de Destino na Sessão
if "download_folder" not in st.session_state:
    st.session_state.download_folder = os.path.abspath("downloads")

# Barra Lateral (Sidebar)
with st.sidebar:
    st.markdown("### <i class='fa-solid fa-sliders' style='color:#64748b;'></i> Configurações", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("##### <i class='fa-solid fa-folder' style='color:#64748b;'></i> Pasta de Download", unsafe_allow_html=True)
    
    folder_input = st.text_input(
        "Caminho no computador:",
        value=st.session_state.download_folder,
        key="folder_path_input"
    )
    st.session_state.download_folder = folder_input
    
    if st.button("📂 Selecionar Pasta no Computador", use_container_width=True):
        new_folder = open_native_folder_dialog(st.session_state.download_folder)
        if new_folder and new_folder != st.session_state.download_folder:
            st.session_state.download_folder = new_folder
            st.rerun()

    st.markdown("---")
    
    with st.expander("🔑 Credenciais do Spotify (Opcional)", expanded=False):
        spotify_client_id = st.text_input("Spotify Client ID", type="password", key="sp_id")
        spotify_client_secret = st.text_input("Spotify Client Secret", type="password", key="sp_secret")
        st.caption("Sem credenciais, o app utiliza a busca pública do iTunes como fallback automático.")

    st.caption("O sistema desconsidera acentos e termos como 'Ao Vivo' ou 'Remix' para desduplicar músicas.")

# Estado da Sessão
if "discography" not in st.session_state:
    st.session_state.discography = None
if "groups" not in st.session_state:
    st.session_state.groups = None
if "selected_versions" not in st.session_state:
    st.session_state.selected_versions = {}
if "last_query" not in st.session_state:
    st.session_state.last_query = ""

# Seção de Busca
st.markdown("#### Digite o Artista ou o Nome da Música")
st.caption("Você pode consultar a discografia inteira de um artista ou buscar uma faixa específica.")

col_search, col_btn = st.columns([4, 1])
with col_search:
    search_query_input = st.text_input(
        "Busca de Artista ou Música:",
        placeholder="Ex: Chitãozinho & Xororó, Evidências, Pink Floyd, Hotel California...",
        label_visibility="collapsed"
    )
with col_btn:
    search_clicked = st.button("🔍 Buscar Músicas", use_container_width=True, type="primary")

# Execução da Busca
if (search_clicked or (search_query_input and search_query_input != st.session_state.last_query and search_clicked)):
    if not search_query_input.strip():
        st.warning("Por favor, digite o nome de um artista ou música para buscar.")
    else:
        with st.spinner(f"Buscando metadados de '{search_query_input}'..."):
            sp_id = st.session_state.get("sp_id", "").strip() or None
            sp_secret = st.session_state.get("sp_secret", "").strip() or None
            
            res = get_artist_discography(search_query_input, spotify_client_id=sp_id, spotify_client_secret=sp_secret)
            
            if not res or not res.get('tracks'):
                st.error(f"Nenhum resultado encontrado para '{search_query_input}'. Verifique a digitação.")
                st.session_state.discography = None
                st.session_state.groups = None
            else:
                st.session_state.discography = res
                st.session_state.last_query = search_query_input
                
                groups = group_tracks_by_base_song(res['tracks'])
                st.session_state.groups = groups
                
                init_selection = {}
                for key, grp in groups.items():
                    default_ver = next((v for v in grp['versions'] if v['is_default']), grp['versions'][0])
                    init_selection[key] = default_ver['id']
                st.session_state.selected_versions = init_selection

# Exibição dos Resultados
if st.session_state.discography and st.session_state.groups:
    artist_info = st.session_state.discography['artist']
    tracks = st.session_state.discography['tracks']
    groups = st.session_state.groups
    
    # Card do Artista Sóbrio (Mantendo Avatar)
    img_html = f'<img src="{artist_info["image_url"]}" class="artist-img"/>' if artist_info.get("image_url") else ''
    source_badge = '<span class="badge"><i class="fa-brands fa-spotify"></i> Spotify API</span>' if 'Spotify' in artist_info['source'] else '<span class="badge"><i class="fa-brands fa-apple"></i> iTunes API</span>'
    
    st.markdown(f"""
    <div class="artist-card">
        {img_html}
        <div>
            <div class="artist-name">{artist_info['name']}</div>
            <div class="artist-meta">Categoria: {artist_info.get('genres', 'Música')} &nbsp;•&nbsp; {source_badge}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Cards de Métricas Minimalistas (Sem fundos roxos)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(tracks)}</div><div class="metric-label">Faixas Encontradas</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(groups)}</div><div class="metric-label">Músicas Únicas</div></div>', unsafe_allow_html=True)
    with m3:
        duplicates_count = len(tracks) - len(groups)
        st.markdown(f'<div class="metric-card"><div class="metric-value">{duplicates_count}</div><div class="metric-label">Versões Alternativas</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(st.session_state.selected_versions)}</div><div class="metric-label">Prontas p/ Download</div></div>', unsafe_allow_html=True)
        
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("#### Escolha de Versões por Música")
    st.caption("Selecione qual versão de cada faixa deseja baixar para evitar arquivos repetidos.")
    
    # Botões de Seleção Rápida Padronizados
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        if st.button("🎯 Apenas Estúdio Original (Recomendado)", use_container_width=True):
            for k, grp in groups.items():
                def_v = next((v for v in grp['versions'] if "Estúdio" in v['version_label']), grp['versions'][0])
                st.session_state.selected_versions[k] = def_v['id']
                st.session_state[f"radio_{k}"] = def_v['id']
            st.rerun()
    with btn_col2:
        if st.button("✅ Selecionar Padrão de Todas", use_container_width=True):
            for k, grp in groups.items():
                val = grp['versions'][0]['id']
                st.session_state.selected_versions[k] = val
                st.session_state[f"radio_{k}"] = val
            st.rerun()
    with btn_col3:
        if st.button("❌ Desmarcar Todas", use_container_width=True):
            for k in groups.keys():
                st.session_state.selected_versions[k] = "skip"
                st.session_state[f"radio_{k}"] = "skip"
            st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Lista de Grupos de Músicas
    for key, grp in groups.items():
        disp_title = grp['display_title']
        versions = grp['versions']
        num_versions = len(versions)
        
        if num_versions == 1:
            accordion_title = f"{disp_title} (1 versão)"
        else:
            accordion_title = f"{disp_title} — ({num_versions} versões disponíveis: Estúdio, Ao Vivo, Remix...)"
        
        with st.expander(accordion_title, expanded=False):
            options_map = {"skip": "🚫 Não baixar esta música"}
            
            for v in versions:
                opt_label = f"🎵 {v['title']} (Artista: {v.get('artist','')}) | Álbum: {v['album']} ({v.get('release_date', 'N/A')}) — [{v['version_label']}]"
                options_map[v['id']] = opt_label
                
            current_sel = st.session_state.selected_versions.get(key, versions[0]['id'])
            if current_sel not in options_map:
                current_sel = versions[0]['id']
                
            selected_option = st.radio(
                f"Selecione a versão para '{disp_title}':",
                options=list(options_map.keys()),
                format_func=lambda x: options_map[x],
                index=list(options_map.keys()).index(current_sel),
                key=f"radio_{key}"
            )
            
            st.session_state.selected_versions[key] = selected_option
            
            cols = st.columns(min(num_versions, 3))
            for idx, v in enumerate(versions):
                with cols[idx % 3]:
                    if v.get('cover_url'):
                        st.image(v['cover_url'], width=95)
                    st.caption(f"**{v['title']}**\n\nÁlbum: {v['album']}\n\nAno: {v.get('release_date','N/A')} | Duração: {v.get('duration_str','--:--')}")

    # Painel de Download
    st.markdown("---")
    
    tracks_to_download = []
    for k, ver_id in st.session_state.selected_versions.items():
        if ver_id != "skip":
            grp = groups[k]
            matched_v = next((v for v in grp['versions'] if v['id'] == ver_id), None)
            if matched_v:
                tracks_to_download.append(matched_v)
                
    st.markdown(f"#### Resumo: **{len(tracks_to_download)}** músicas selecionadas")
    
    if len(tracks_to_download) == 0:
        st.warning("Nenhuma música selecionada para download.")
    else:
        target_save_folder = st.session_state.download_folder
        if st.button(f"🚀 Iniciar Download ({len(tracks_to_download)} Músicas)", type="primary", use_container_width=True):
            # Inicializa controle de cancelamento
            st.session_state.download_cancelled = False
            
            st.markdown("##### Processando Downloads...")
            
            # Botão de Cancelar
            cancel_placeholder = st.empty()
            progress_bar = st.progress(0)
            status_text = st.empty()
            log_container = st.container()
            
            results_summary = []
            total_count = len(tracks_to_download)
            cancelled = False
            
            for idx, trk in enumerate(tracks_to_download):
                # Renderiza botão de cancelar a cada iteração
                if cancel_placeholder.button("⛔ Cancelar Downloads Restantes", key=f"cancel_{idx}", use_container_width=True):
                    cancelled = True
                    status_text.markdown(f"### ⚠️ Download interrompido pelo usuário na faixa {idx+1}/{total_count}")
                    break
                
                pct = (idx + 1) / total_count
                progress_bar.progress(pct)
                status_text.markdown(f"**Baixando ({idx+1}/{total_count}):** `{trk['title']}`...")
                
                res = download_track(
                    track_info=trk,
                    artist_name=trk.get('artist', artist_info['name']),
                    download_dir=target_save_folder
                )
                
                results_summary.append(res)
                
                with log_container:
                    if res['status'] == 'success':
                        st.success(f"✅ {res['title']} -> Salvo com sucesso!")
                    elif res['status'] == 'already_exists':
                        st.info(f"ℹ️ {res['title']} (Já existia na pasta)")
                    else:
                        st.error(f"❌ Erro em {res['title']}: {res['message']}")
            
            # Remove o botão de cancelar ao finalizar
            cancel_placeholder.empty()
            
            # Resumo final
            ok_count = sum(1 for r in results_summary if r['status'] in ('success', 'already_exists'))
            err_count = sum(1 for r in results_summary if r['status'] == 'error')
            
            if cancelled:
                remaining = total_count - len(results_summary)
                st.warning(f"Download cancelado. **{ok_count}** baixadas com sucesso, **{err_count}** com erro, **{remaining}** não iniciadas.")
            else:
                status_text.markdown("### 🎉 Todos os downloads foram concluídos com sucesso!")
                st.balloons()
            
            st.markdown(f"📍 **Arquivos salvos em:** `{os.path.abspath(target_save_folder)}`")

