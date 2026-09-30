import os
import sys
import streamlit as st
from PIL import Image

# Importa módulos internos do core
from core.metadata import get_artist_discography
from core.normalizer import group_tracks_by_base_song
from core.downloader import download_track

# Configuração da Página
st.set_page_config(
    page_title="Baixa Música - Download de Discografias e Faixas",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Funções auxiliares
def open_native_folder_dialog(current_path: str) -> str:
    """Abre o explorador de arquivos nativo do Windows/OS para escolher a pasta de download."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes('-topmost', 1)
        selected = filedialog.askdirectory(
            title="Selecione a Pasta para Salvar as Músicas",
            initialdir=current_path if os.path.exists(current_path) else os.path.expanduser("~")
        )
        root.destroy()
        return selected if selected else current_path
    except Exception as e:
        st.error(f"Não foi possível abrir o navegador de arquivos nativo: {e}")
        return current_path

# Estilização CSS Customizada (Compatível com Tema Claro e Tema Escuro)
st.markdown("""
<style>
    /* Adaptação Dinâmica de Tema (Light & Dark Mode) */
    .main-header {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #9333ea 100%);
        padding: 1.8rem 2.2rem;
        border-radius: 14px;
        color: #ffffff !important;
        box-shadow: 0 10px 20px -5px rgba(79, 70, 229, 0.3);
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: #ffffff !important;
        margin: 0;
        font-size: 2.3rem;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #e0e7ff !important;
        margin-top: 0.4rem;
        font-size: 1.05rem;
    }
    
    /* Card do Artista / Busca */
    .artist-card {
        background-color: var(--secondary-background-color, #f3f4f6);
        border: 1px solid rgba(156, 163, 175, 0.3);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.5rem;
        display: flex;
        gap: 1.5rem;
        align-items: center;
    }
    .artist-img {
        width: 105px;
        height: 105px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #6366f1;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }
    .artist-name {
        font-size: 1.7rem;
        font-weight: 700;
        margin: 0;
        color: var(--text-color, #111827);
    }
    
    /* Stat Metric Box */
    .metric-card {
        background-color: var(--secondary-background-color, #f3f4f6);
        border: 1px solid rgba(156, 163, 175, 0.3);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #4f46e5;
    }
    .metric-label {
        font-size: 0.85rem;
        opacity: 0.8;
    }
    
    /* Botões Customizados - Azul/Índigo Suave (Sem vermelho forte) */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        border: none;
        transition: all 0.2s ease-in-out;
    }
    
    /* Botão Principal Indigo */
    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(90deg, #4f46e5 0%, #6366f1 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 10px rgba(79, 70, 229, 0.25);
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background: linear-gradient(90deg, #4338ca 0%, #4f46e5 100%) !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 15px rgba(79, 70, 229, 0.35);
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 20px;
        margin-right: 0.5rem;
    }
    .badge-spotify { background: #10b981; color: #ffffff; }
    .badge-itunes { background: #3b82f6; color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# Header Superior
st.markdown("""
<div class="main-header">
    <div>
        <h1>🎵 Baixa Música</h1>
        <p>Baixe discografias completas ou músicas avulsas sem arquivos repetidos • Seleção de versões inteligentes</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Inicialização da Pasta de Destino na Sessão
if "download_folder" not in st.session_state:
    st.session_state.download_folder = os.path.abspath("downloads")

# Sidebar - Configurações de Download e API
with st.sidebar:
    st.header("⚙️ Configurações")
    
    st.subheader("📁 Pasta onde salvar os arquivos")
    
    # Exibe o caminho atual da pasta
    folder_input = st.text_input("Caminho do diretório:", value=st.session_state.download_folder, key="folder_path_input")
    st.session_state.download_folder = folder_input
    
    # Botão Intuitivo para abrir o Explorador de Arquivos do Windows
    if st.button("📂 Procurar Pasta no Computador", use_container_width=True):
        new_folder = open_native_folder_dialog(st.session_state.download_folder)
        if new_folder and new_folder != st.session_state.download_folder:
            st.session_state.download_folder = new_folder
            st.rerun()

    st.markdown("---")
    
    # Credenciais do Spotify
    with st.expander("🔑 Credenciais do Spotify (Opcional)", expanded=False):
        spotify_client_id = st.text_input("Spotify Client ID", type="password", key="sp_id")
        spotify_client_secret = st.text_input("Spotify Client Secret", type="password", key="sp_secret")
        st.caption("Se deixado em branco, o sistema usará a API gratuita do iTunes/Deezer como fallback automático sem precisar de cadastro.")

    st.caption("💡 O programa agrupa automaticamente regravações, álbuns ao vivo e remixes para você baixar apenas a versão que desejar.")

# Inicialização do Estado da Sessão
if "discography" not in st.session_state:
    st.session_state.discography = None
if "groups" not in st.session_state:
    st.session_state.groups = None
if "selected_versions" not in st.session_state:
    st.session_state.selected_versions = {}
if "last_query" not in st.session_state:
    st.session_state.last_query = ""

# Seção de Busca com Explicação Clara (Artista OU Música Específica)
st.markdown("### 🔍 O que você deseja baixar?")
st.caption("Você pode digitar o **nome de um artista/banda** para baixar a discografia completa, ou o **nome de uma música específica**.")

col_search, col_btn = st.columns([4, 1])
with col_search:
    search_query_input = st.text_input(
        "Digite o nome do Artista OU o Nome da Música:",
        placeholder="Ex: Chitãozinho & Xororó, Evidências, Coldplay, Hotel California...",
        label_visibility="collapsed"
    )
with col_btn:
    search_clicked = st.button("🔍 Buscar Músicas", use_container_width=True, type="primary")

# Ação de Busca
if (search_clicked or (search_query_input and search_query_input != st.session_state.last_query and search_clicked)):
    if not search_query_input.strip():
        st.warning("Por favor, digite o nome de um artista ou música para buscar.")
    else:
        with st.spinner(f"Buscando resultados para '{search_query_input}'..."):
            sp_id = st.session_state.get("sp_id", "").strip() or None
            sp_secret = st.session_state.get("sp_secret", "").strip() or None
            
            res = get_artist_discography(search_query_input, spotify_client_id=sp_id, spotify_client_secret=sp_secret)
            
            if not res or not res.get('tracks'):
                st.error(f"Nenhum resultado encontrado para '{search_query_input}'. Verifique a grafia e tente novamente.")
                st.session_state.discography = None
                st.session_state.groups = None
            else:
                st.session_state.discography = res
                st.session_state.last_query = search_query_input
                # Executa agrupamento normalizado de versões
                groups = group_tracks_by_base_song(res['tracks'])
                st.session_state.groups = groups
                
                # Inicializa seleção padrão (marca a versão default recomendada)
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
    source_badge = '<span class="badge badge-spotify">Spotify API</span>' if 'Spotify' in artist_info['source'] else '<span class="badge badge-itunes">iTunes API</span>'
    
    st.markdown(f"""
    <div class="artist-card">
        {img_html}
        <div>
            <div class="artist-name">{artist_info['name']}</div>
            <p style="margin: 0.3rem 0; opacity: 0.85;">Categoria: {artist_info.get('genres', 'Música')} | {source_badge}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas da Discografia / Busca
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(tracks)}</div><div class="metric-label">Faixas Encontradas</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(groups)}</div><div class="metric-label">Músicas Únicas</div></div>', unsafe_allow_html=True)
    with m3:
        duplicates_count = len(tracks) - len(groups)
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#6366f1;">{duplicates_count}</div><div class="metric-label">Outras Versões/Remixes</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#10b981;">{len(st.session_state.selected_versions)}</div><div class="metric-label">Prontas p/ Download</div></div>', unsafe_allow_html=True)
        
    st.markdown("### 🎛️ Escolha as Versões Desejadas")
    st.info("Para evitar repetições, cada música possui suas versões agrupadas abaixo. Selecione qual versão baixar ou marque **'Não baixar'** para ignorar.")
    
    # Ações Rápidas de Seleção
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
    
    # Lista de Grupos de Músicas com Accordion / Menu de Seleção
    for key, grp in groups.items():
        disp_title = grp['display_title']
        versions = grp['versions']
        num_versions = len(versions)
        
        accordion_title = f"🎵 {disp_title} ({num_versions} versão)" if num_versions == 1 else f"⚡ {disp_title} — ({num_versions} versões disponíveis: Estúdio, Ao Vivo, Remix...)"
        
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
            
            # Detalhes visuais das versões com capa
            cols = st.columns(min(num_versions, 3))
            for idx, v in enumerate(versions):
                with cols[idx % 3]:
                    if v.get('cover_url'):
                        st.image(v['cover_url'], width=95)
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
                
    st.markdown(f"### 📥 Resumo do Download: **{len(tracks_to_download)}** músicas selecionadas")
    
    if len(tracks_to_download) == 0:
        st.warning("Nenhuma música selecionada para download.")
    else:
        target_save_folder = st.session_state.download_folder
        if st.button(f"🚀 Iniciar Download ({len(tracks_to_download)} Músicas)", type="primary", use_container_width=True):
            st.markdown("#### ⏳ Processando Downloads...")
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
                        
            status_text.markdown("### 🎉 Todos os downloads foram concluídos com sucesso!")
            st.balloons()
            
            st.markdown(f"📍 **Arquivos salvos em:** `{os.path.abspath(target_save_folder)}`")
