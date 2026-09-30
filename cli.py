import os
import sys
from core.metadata import get_artist_discography
from core.normalizer import group_tracks_by_base_song
from core.downloader import download_track

def main():
    print("=" * 65)
    print(" 🎵 MUSIC VAULT - BAIXADOR INTELIGENTE DE DISCOGRAFIAS (CLI)")
    print("=" * 65)
    
    artist_name = input("\n[?] Digite o nome do artista ou banda: ").strip()
    if not artist_name:
        print("[!] Nenhum artista informado. Encerrando.")
        return

    print(f"\n[+] Buscando discografia de '{artist_name}'...")
    res = get_artist_discography(artist_name)
    
    if not res or not res.get('tracks'):
        print("[!] Nenhum resultado encontrado.")
        return

    artist_info = res['artist']
    tracks = res['tracks']
    
    print(f"\n[✓] Artista: {artist_info['name']} ({artist_info.get('genres', 'Música')})")
    print(f"[✓] Total de faixas brutas encontradas: {len(tracks)}")
    
    # Agrupamento de versões
    groups = group_tracks_by_base_song(tracks)
    print(f"[✓] Músicas únicas identificadas: {len(groups)}")
    
    print("\n" + "-" * 65)
    print(" MODO DE SELEÇÃO DE MÚSICAS:")
    print(" 1. Baixar versão padrão/estúdio recomendada de cada música (Modo Rápido)")
    print(" 2. Revisar e escolher versão para cada faixa manualmente")
    print("-" * 65)
    
    choice = input("Escolha uma opção (1 ou 2) [Padrão: 1]: ").strip()
    
    selected_tracks = []
    
    if choice == "2":
        for key, grp in groups.items():
            disp_title = grp['display_title']
            versions = grp['versions']
            
            print(f"\n--- Música: {disp_title} ({len(versions)} versão/ões) ---")
            print(" 0: [Pular esta música]")
            for idx, v in enumerate(versions, start=1):
                default_tag = " (Recomendada)" if v['is_default'] else ""
                print(f" {idx}: {v['title']} | Álbum: {v['album']} ({v.get('release_date', 'N/A')}) [{v['version_label']}]{default_tag}")
                
            v_choice = input(f"Selecione a versão (0-{len(versions)}) [Padrão: 1]: ").strip()
            if not v_choice:
                v_choice = "1"
                
            try:
                idx_sel = int(v_choice)
                if idx_sel > 0 and idx_sel <= len(versions):
                    selected_tracks.append(versions[idx_sel - 1])
                else:
                    print("-> Música pulada.")
            except ValueError:
                print("-> Opção inválida. Música pulada.")
    else:
        # Seleção padrão automática
        for key, grp in groups.items():
            def_v = next((v for v in grp['versions'] if v['is_default']), grp['versions'][0])
            selected_tracks.append(def_v)
            
    print(f"\n[+] Total de músicas selecionadas para download: {len(selected_tracks)}")
    if not selected_tracks:
        print("[!] Nenhuma música selecionada. Encerrando.")
        return

    output_dir = os.path.abspath("downloads")
    confirm = input(f"\n[?] Confirmar download em '{output_dir}'? (S/n): ").strip().lower()
    if confirm and confirm != 's' and confirm != 'y':
        print("[!] Download cancelado.")
        return

    print("\n[🚀] Iniciando downloads...\n")
    for idx, trk in enumerate(selected_tracks, start=1):
        print(f"[{idx}/{len(selected_tracks)}] Baixando '{trk['title']}'...")
        res_dl = download_track(trk, artist_info['name'], output_dir)
        if res_dl['status'] in ('success', 'already_exists'):
            print(f" -> {res_dl['message']}: {res_dl['file_path']}")
        else:
            print(f" -> ERRO: {res_dl['message']}")

    print("\n[🎉] Processo concluído com sucesso!")

if __name__ == '__main__':
    main()
