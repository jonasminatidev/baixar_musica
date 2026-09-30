import os
import sys
import base64
import subprocess
import streamlit as st

# Importa módulos internos do core
from core.metadata import get_artist_discography
from core.normalizer import group_tracks_by_base_song
from core.downloader import download_track

# Configuração da Página
st.set_page_config(
    page_title="Baixa Música - Download Inteligente",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_base64_image(image_path: str) -> str:
    """Converte uma imagem local em string Base64 para uso em CSS."""
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

def open_native_folder_dialog(current_path: str) -> str:
    """
    Abre o explorador de arquivos nativo do Windows usando PowerShell.
    Evita o erro 'main thread is not in main loop' do Tkinter.
    """
    try:
        ps_cmd = (
            "[System.Reflection.Assembly]::LoadWithPartialName('System.windows.forms') | Out-Null; "
            "$dialog = New-Object System.Windows.Forms.FolderBrowserDialog; "
            "$dialog.Description = 'Selecione a pasta para salvar as músicas'; "
            "$dialog.ShowNewFolderButton = $true; "
            "if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { "
            "Write-Output $dialog.SelectedPath "
            "}"
        )
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        selected = proc.stdout.strip()
        if selected and os.path.exists(selected):
            return selected
    except Exception as e:
        st.error(f"Erro ao abrir o navegador de arquivos: {e}")
    return current_path

# Carrega imagem de fundo em base64
bg_base64 = get_base64_image("assets/bg.jpg")
bg_css = ""
if bg_base64:
    bg_css = f"""
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(10, 15, 30, 0.92) 100%), 
                    url("data:image/jpeg;base64,{bg_base64}") no-repeat center center fixed !important;
        background-size: cover !important;
    """

# Injeção de Ícones Font Awesome 6 + Estilização Glassmorphism de Alto Padrão
st.markdown(f"""
<!-- Font Awesome 6 CDN para ícones ultra-modernos -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">

<style>
    /* Fonte Moderna */
    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', sans-serif;
    }}

    /* Background Global com Imagem Borrada */
    .stApp {{
        {bg_css}
        color: #f1f5f9;
    }}
    
    /* Header Estilo Glassmorphism Premium */
    .main-header {{
        background: linear-gradient(135deg, rgba(79, 70, 229, 0.8) 0%, rgba(124, 58, 237, 0.75) 50%, rgba(147, 51, 234, 0.8) 100%) !important;
        backdrop-filter: blur(16px) saturate(180%);
        -webkit-backdrop-filter: blur(16px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        color: #ffffff !important;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
        margin-bottom: 2rem;
    }}
    .main-header h1 {{
        color: #ffffff !important;
        margin: 0;
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }}
    .main-header p {{
        color: #e0e7ff !important;
        margin-top: 0.4rem;
        font-size: 1.1rem;
        font-weight: 500;
    }}
    
    /* Cards de Conteúdo em Vidro (Glassmorphism) */
    .artist-card, .metric-card, .glass-card {{
        background: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(12px) saturate(160%);
        -webkit-backdrop-filter: blur(12px) saturate(160%);
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }}
    
    .artist-card {{
        display: flex;
        gap: 1.5rem;
        align-items: center;
    }}
    
    .artist-img {{
        width: 110px;
        height: 110px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #6366f1;
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
    }}
    .artist-name {{
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0;
        color: #ffffff;
    }}
    
    /* Stat Metric Box */
    .metric-card {{
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }}
    .metric-card:hover {{
        transform: translateY(-3px);
        border-color: rgba(99, 102, 241, 0.4) !important;
    }}
    .metric-value {{
        font-size: 2rem;
        font-weight: 800;
        color: #818cf8;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }}
    .metric-label {{
        font-size: 0.85rem;
        color: #94a3b8;
        font-weight: 600;
        margin-top: 0.2rem;
    }}
    
    /* Badges com Ícones Modernos */
    .badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.3rem 0.75rem;
        font-size: 0.8rem;
        font-weight: 700;
        border-radius: 20px;
        margin-right: 0.5rem;
    }}
    .badge-spotify {{ background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); }}
    .badge-itunes {{ background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(96, 165, 250, 0.3); }}
    .badge-studio {{ background: rgba(99, 102, 241, 0.2); color: #a5b4fc; border: 1px solid rgba(165, 180, 252, 0.3); }}
    .badge-live {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }}
    
    /* Botões Personalizados */
    .stButton>button {{
        border-radius: 10px !important;
        font-weight: 700 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        transition: all 0.2s ease-in-out !important;
    }}
    
    /* Botão Principal */
    div[data-testid="stButton"] button[kind="primary"] {{
        background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35) !important;
    }}
    div[data-testid="stButton"] button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #4338ca 0%, #4f46e5 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.5) !important;
    }}
</style>
""", unsafe_allow_html=True)

# Header Superior
st.markdown("""
<div class="main-header">
    <div>
        <h1><i class="fa-solid fa-compact-disc fa-spin-pulse" style="--fa-animation-duration: 6s; color: #a855f7;"></i> Baixa Música</h1>
        <p><i class="fa-solid fa-cloud-arrow-down"></i> Download inteligente de discografias completas e faixas avulsas • Sem repetições de músicas</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Inicialização da Pasta no Estado da Sessão
if "download_folder" not in st.session_state:
    st.session_state.download_folder = os.path.abspath("downloads")

# Sidebar - Configurações de Download e API
with st.sidebar:
    st.markdown("### <i class='fa-solid fa-sliders'></i> Configurações", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("##### <i class='fa-solid fa-folder-open' style='color:#818cf8;'></i> Pasta de Download", unsafe_allow_html=True)
    
    # Campo de texto da pasta
    folder_input = st.text_input(
        "Caminho no computador:",
        value=st.session_state.download_folder,
        key="folder_path_input"
    )
    st.session_state.download_folder = folder_input
    
    # Botão com Navegador Nativo do Windows (Sem erro de Tkinter!)
    if st.button("📂 Abrir Explorador de Pastas", use_container_width=True):
        new_folder = open_native_folder_dialog(st.session_state.download_folder)
        if new_folder and new_folder != st.session_state.download_folder:
            st.session_state.download_folder = new_folder
            st.rerun()

    st.markdown("---")
    
    # Credenciais do Spotify
    with st.expander("🔑 API do Spotify (Opcional)", expanded=False):
        spotify_client_id = st.text_input("Spotify Client ID", type="password", key="sp_id")
        spotify_client_secret = st.text_input("Spotify Client Secret", type="password", key="sp_secret")
        st.caption("Se não informado, o app usa a busca pública do iTunes/Deezer como fallback automático.")

    st.caption("✨ O sistema remove acentos, sufixos 'Ao Vivo', 'Remix' e agrupa variações sob um único nome base.")

# Inicialização do Estado da Sessão
if "discography" not in st.session_state:
    st.session_state.discography = None
if "groups" not in st.session_state:
    st.session_state.groups = None
if "selected_versions" not in st.session_state:
    st.session_state.selected_versions = {}
if "last_query" not in st.session_state:
    st.session_state.last_query = ""

# Seção de Busca
st.markdown("### <i class='fa-solid fa-magnifying-glass' style='color:#818cf8;'></i> Digite o que deseja buscar", unsafe_allow_html=True)
st.caption("Você pode buscar por um **Artista/Banda** (para carregar a discografia inteira) ou por um **Nome de Música** específico.")

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
                
                # Inicializa seleção com a versão de estúdio recomendada
                init_selection = {}
                for key, grp in groups.items():
                    default_ver = next((v for v in grp['versions'] if v['is_default']), grp['versions'][0])
                    init_selection[key] = default_ver['id']
                st.session_state.selected_versions = init_selection

# Exibição dos Resultados e Curadoria de Versões
if st.session_state.discography and st.session_state.groups:
    artist_info = st.session_state.discography['artist']
    tracks = st.session_state.discography['tracks']
    groups = st.session_state.groups
    
    # Card do Artista / Resultado da Busca
    img_html = f'<img src="{artist_info["image_url"]}" class="artist-img"/>' if artist_info.get("image_url") else ''
    source_badge = '<span class="badge badge-spotify"><i class="fa-brands fa-spotify"></i> Spotify API</span>' if 'Spotify' in artist_info['source'] else '<span class="badge badge-itunes"><i class="fa-brands fa-apple"></i> iTunes API</span>'
    
    st.markdown(f"""
    <div class="artist-card">
        {img_html}
        <div>
            <div class="artist-name">{artist_info['name']}</div>
            <p style="margin: 0.4rem 0; opacity: 0.9;"><i class="fa-solid fa-guitar" style="color:#818cf8;"></i> Categoria: {artist_info.get('genres', 'Música')} | {source_badge}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas Visuais da Busca
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-card"><div class="metric-value"><i class="fa-solid fa-music"></i> {len(tracks)}</div><div class="metric-label">Faixas Encontradas</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><div class="metric-value"><i class="fa-solid fa-layer-group"></i> {len(groups)}</div><div class="metric-label">Músicas Únicas</div></div>', unsafe_allow_html=True)
    with m3:
        duplicates_count = len(tracks) - len(groups)
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#c084fc;"><i class="fa-solid fa-object-ungroup"></i> {duplicates_count}</div><div class="metric-label">Outras Versões/Ao Vivo</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#34d399;"><i class="fa-solid fa-circle-check"></i> {len(st.session_state.selected_versions)}</div><div class="metric-label">Prontas p/ Download</div></div>', unsafe_allow_html=True)
        
    st.markdown("### <i class='fa-solid fa-list-check' style='color:#818cf8;'></i> Curadoria e Escolha de Versões", unsafe_allow_html=True)
    st.info("Para evitar músicas repetidas, as variações estão agrupadas abaixo. Escolha a versão desejada de cada faixa ou marque 'Não baixar'.")
    
    # Botões de Seleção Rápida
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        if st.button("🎯 Selecionar Apenas Estúdio Original (Recomendado)", use_container_width=True):
            for k, grp in groups.items():
                def_v = next((v for v in grp['versions'] if "Estúdio" in v['version_label']), grp['versions'][0])
                st.session_state.selected_versions[k] = def_v['id']
            st.rerun()
    with btn_col2:
        if st.button("✅ Selecionar Padrão de Todas", use_container_width=True):
            for k, grp in groups.items():
                st.session_state.selected_versions[k] = grp['versions'][0]['id']
            st.rerun()
    with btn_col3:
        if st.button("❌ Desmarcar Todas as Músicas", use_container_width=True):
            for k in groups.keys():
                st.session_state.selected_versions[k] = "skip"
            st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Lista de Grupos de Músicas com Accordion
    for key, grp in groups.items():
        disp_title = grp['display_title']
        versions = grp['versions']
        num_versions = len(versions)
        
        if num_versions == 1:
            accordion_title = f"🎵 {disp_title} (1 versão encontrada)"
        else:
            accordion_title = f"⚡ {disp_title} — ({num_versions} versões: Estúdio, Ao Vivo, Remix...)"
        
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
            
            # Detalhes das versões com capa
            cols = st.columns(min(num_versions, 3))
            for idx, v in enumerate(versions):
                with cols[idx % 3]:
                    if v.get('cover_url'):
                        st.image(v['cover_url'], width=100)
                    st.caption(f"**{v['title']}**\n\nÁlbum: {v['album']}\n\nAno: {v.get('release_date','N/A')} | Duração: {v.get('duration_str','--:--')}")

    # Painel de Confirmação e Download
    st.markdown("---")
    
    tracks_to_download = []
    for k, ver_id in st.session_state.selected_versions.items():
        if ver_id != "skip":
            grp = groups[k]
            matched_v = next((v for v in grp['versions'] if v['id'] == ver_id), None)
            if matched_v:
                tracks_to_download.append(matched_v)
                
    st.markdown(f"### <i class='fa-solid fa-cloud-arrow-down' style='color:#818cf8;'></i> Resumo do Download: **{len(tracks_to_download)}** músicas selecionadas", unsafe_allow_html=True)
    
    if len(tracks_to_download) == 0:
        st.warning("Nenhuma música selecionada para download.")
    else:
        target_save_folder = st.session_state.download_folder
        if st.button(f"🚀 Iniciar Download ({len(tracks_to_download)} Músicas)", type="primary", use_container_width=True):
            st.markdown("#### <i class='fa-solid fa-spinner fa-spin'></i> Processando Downloads...", unsafe_allow_html=True)
            progress_bar = st.progress(0)
            status_text = st.empty()
            log_container = st.container()
            
            results_summary = []
            total_count = len(tracks_to_download)
            
            for idx, trk in enumerate(tracks_to_download):
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
                        
            status_text.markdown("### <i class='fa-solid fa-circle-check' style='color:#34d399;'></i> Todos os downloads foram concluídos com sucesso!", unsafe_allow_html=True)
            st.balloons()
            
            st.markdown(f"📍 **Arquivos salvos em:** `{os.path.abspath(target_save_folder)}`")
