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
    page_title="Music Vault - Baixador Inteligente de Discografias",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Customizada de Alto Padrão
st.markdown("""
<style>
    /* Estilo Global Dark Mode */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Header Principal */
    .main-header {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        border: 1px solid #374151;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .main-header h1 {
        color: #f3f4f6;
        margin: 0;
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .main-header p {
        color: #9ca3af;
        margin-top: 0.2rem;
        font-size: 1rem;
    }
    
    /* Card de Artista */
    .artist-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
        display: flex;
        gap: 1.5rem;
        align-items: center;
    }
    .artist-img {
        width: 110px;
        height: 110px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #6366f1;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);
    }
    .artist-name {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
    }
    
    /* Badges e Tags */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 20px;
        margin-right: 0.5rem;
    }
    .badge-spotify { background: #1ed760; color: #000000; }
    .badge-itunes { background: #fa2d48; color: #ffffff; }
    .badge-studio { background: #059669; color: #ffffff; }
    .badge-live { background: #d97706; color: #ffffff; }
    .badge-remix { background: #7c3aed; color: #ffffff; }
    
    /* Stat Metric Box */
    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #6366f1;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #8b949e;
    }
    
    /* Botões Customizados */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
</style>
""", unsafe_allow_html=True)

# Header Superior
st.markdown("""
<div class="main-header">
    <div>
        <h1>🎵 Music Vault & Curator</h1>
        <p>Baixador de discografia sem músicas duplicadas • Escolha a versão ideal de cada faixa</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar - Configurações de API e Download
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Credenciais do Spotify
    with st.expander("🔑 Credenciais do Spotify (Opcional)", expanded=False):
        spotify_client_id = st.text_input("Spotify Client ID", type="password", key="sp_id")
        spotify_client_secret = st.text_input("Spotify Client Secret", type="password", key="sp_secret")
        st.caption("Se deixado em branco, o sistema usará a API gratuita do iTunes/Deezer como fallback automático.")

    # Diretório de Saída
    st.subheader("📁 Pasta de Destino")
    download_folder = st.text_input("Diretório de Download", value=os.path.abspath("downloads"))
    
    st.markdown("---")
    st.caption("Desenvolvido para organizar e baixar discografias sem arquivos repetidos.")

# Inicialização do Estado da Sessão
if "discography" not in st.session_state:
    st.session_state.discography = None
if "groups" not in st.session_state:
    st.session_state.groups = None
if "selected_versions" not in st.session_state:
    st.session_state.selected_versions = {}
if "last_searched_artist" not in st.session_state:
    st.session_state.last_searched_artist = ""

# Formulário de Busca por Artista
col_search, col_btn = st.columns([4, 1])
with col_search:
    artist_name_input = st.text_input("Digite o nome do artista ou banda:", placeholder="Ex: Chitãozinho & Xororó, Pink Floyd, Anitta...", label_visibility="collapsed")
with col_btn:
    search_clicked = st.button("🔍 Buscar Discografia", use_container_width=True, type="primary")

# Ação de Busca
if (search_clicked or (artist_name_input and artist_name_input != st.session_state.last_searched_artist and search_clicked)):
    if not artist_name_input.strip():
        st.warning("Por favor, digite o nome de um artista para buscar.")
    else:
        with st.spinner(f"Buscando discografia completa de '{artist_name_input}'..."):
            sp_id = st.session_state.get("sp_id", "").strip() or None
            sp_secret = st.session_state.get("sp_secret", "").strip() or None
            
            res = get_artist_discography(artist_name_input, spotify_client_id=sp_id, spotify_client_secret=sp_secret)
            
            if not res or not res.get('tracks'):
                st.error(f"Nenhum resultado encontrado para '{artist_name_input}'. Tente refinar a busca.")
                st.session_state.discography = None
                st.session_state.groups = None
            else:
                st.session_state.discography = res
                st.session_state.last_searched_artist = artist_name_input
                # Executa agrupamento normalizado de versões
                groups = group_tracks_by_base_song(res['tracks'])
                st.session_state.groups = groups
                
                # Inicializa seleção padrão (seleciona a versão marcada como default para cada música)
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
    
    # Card do Artista
    img_html = f'<img src="{artist_info["image_url"]}" class="artist-img"/>' if artist_info.get("image_url") else ''
    source_badge = '<span class="badge badge-spotify">Spotify API</span>' if 'Spotify' in artist_info['source'] else '<span class="badge badge-itunes">iTunes API</span>'
    
    st.markdown(f"""
    <div class="artist-card">
        {img_html}
        <div>
            <div class="artist-name">{artist_info['name']}</div>
            <p style="margin: 0.3rem 0; color: #8b949e;">Gênero: {artist_info.get('genres', 'Música')} | {source_badge}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas da Discografia
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(tracks)}</div><div class="metric-label">Músicas Coletadas</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(groups)}</div><div class="metric-label">Músicas Únicas</div></div>', unsafe_allow_html=True)
    with m3:
        duplicates_count = len(tracks) - len(groups)
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#eab308;">{duplicates_count}</div><div class="metric-label">Versões Alternativas/Duplicadas</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#22c55e;">{len(st.session_state.selected_versions)}</div><div class="metric-label">Prontas p/ Download</div></div>', unsafe_allow_html=True)
        
    st.markdown("### 🎛️ Curadoria de Versões (Evite Repetições)")
    st.info("O sistema identificou as versões de cada música. Escolha qual versão deseja baixar para cada faixa ou selecione **'Não baixar'** para ignorar.")
    
    # Ações Rápidas de Seleção
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        if st.button("🎯 Selecionar Apenas Estúdio Original (Padrão)", use_container_width=True):
            for k, grp in groups.items():
                def_v = next((v for v in grp['versions'] if "Estúdio" in v['version_label']), grp['versions'][0])
                st.session_state.selected_versions[k] = def_v['id']
            st.rerun()
    with btn_col2:
        if st.button("✅ Selecionar Padrão Recomendado", use_container_width=True):
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
    form_selection = {}
    
    for key, grp in groups.items():
        disp_title = grp['display_title']
        versions = grp['versions']
        num_versions = len(versions)
        
        # Subtítulo formatado com tags
        has_multiple = num_versions > 1
        accordion_title = f"{disp_title} ({num_versions} versão)" if num_versions == 1 else f"⚡ {disp_title} — ({num_versions} versões disponíveis)"
        
        with st.expander(accordion_title, expanded=False):
            # Cria as opções para o radio button
            options_map = {"skip": "🚫 Não baixar esta música"}
            
            for v in versions:
                opt_label = f"🎵 {v['title']} | Álbum: {v['album']} ({v.get('release_date', 'N/A')}) — [{v['version_label']}]"
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
    
    # Filtra faixas selecionadas (ignorando as que estão marcadas como 'skip')
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
                    artist_name=artist_info['name'],
                    download_dir=download_folder
                )
                
                results_summary.append(res)
                
                with log_container:
                    if res['status'] == 'success':
                        st.success(f"✅ {res['title']} -> {os.path.basename(res['file_path'])}")
                    elif res['status'] == 'already_exists':
                        st.info(f"ℹ️ {res['title']} (Já existia no disco)")
                    else:
                        st.error(f"❌ Erro em {res['title']}: {res['message']}")
                        
            status_text.markdown("### 🎉 Todos os downloads foram concluídos!")
            st.balloons()
            
            # Tabela de Resumo Final
            st.markdown(f"**Arquivos salvos em:** `{os.path.join(download_folder, artist_info['name'])}`")
