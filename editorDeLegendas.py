#!/usr/bin/env python3

# Importações do Sistema
import argparse
import os
import shutil
import natsort
import re
import shutil
import requests
from tabulate import tabulate

# Importações Personalizadas
import LibAniHubSub

EXT_LEG = ".ass"
EXT_MKV = ".mkv"
EXT_MP4 = ".mp4"


# Funções
def dir_bak_leg(dir_trabalho=None, arquivos_de_legenda=None, dir_backup='Legendas Originais', extensao_legenda='.ass'):
    # Criando o Diretório onde ficaram as legendas originais da Crunchroll
    try:
        original_umask = os.umask(0)
        os.mkdir(dir_trabalho + '/' + dir_backup)
    except OSError:
        print("Falha na cricao do diretorio porque ele ja existe" + dir_trabalho + '/' + dir_backup)
    else:
        print("Successfully created the directory %s " + dir_trabalho + '/' + dir_backup)
    finally:
        os.umask(original_umask)

    # Move os arquivos de legendas para o diretorio de Backup
    for arquivo_de_legenda in arquivos_de_legenda:
        if arquivo_de_legenda.endswith(extensao_legenda):
            try:
                shutil.move(dir_trabalho + '/' + arquivo_de_legenda, dir_trabalho + '/' + dir_backup)
            except OSError:
                print("Arquivo já existe no destino" + arquivo_de_legenda)

# Programa Principal
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Um programa de exemplo.', argument_default=argparse.SUPPRESS)

    parser.add_argument(
        '-c',
        action='store',
        dest='cod_tvmaze',
        required=True,
        default=None,
        help='Indica o código do animes para buscar as informações no site da TVMaze'
    )

    parser.add_argument(
        '-t',
        action='store',
        dest='temporada',
        type=str,
        required=False,
        default="1",
        help='Indica a temporada do anime'
    )

    parser.add_argument(
        '-d',
        action='store',
        dest='dir_trabalho',
        required=True,
        help='Indica o diretorio que os arquivos estão'
    )

    parser.add_argument(
        '-rx',
        action='store',
        dest='res_x',
        required=False,
        default=640,
        help='Indica a resolução em X'
    )

    parser.add_argument(
        '-ry',
        action='store',
        dest='res_y',
        required=False,
        default=360,
        help='Indica a resolução em Y'
    )

    parser.add_argument(
        '-ts',
        action='store',
        dest='titulo',
        required=False,
        help='Indica o título que será usado no arquivos: titulo.S01E01.mkv'
    )

    parser.add_argument(
        '-ext',
        action='store',
        dest='extensao',
        required=False,
        default=".ass",
        help='Indica a extensao do arquivo a ser renomeado'
    )

    argumentos = parser.parse_args()

    show = requests.get('http://api.tvmaze.com/shows/' + argumentos.cod_tvmaze + '?embed[]=episodes&embed[]=seasons', verify=True).json()

    nomes_atuais_episodios = [x for x in os.listdir(argumentos.dir_trabalho) if x.endswith(argumentos.extensao)]
    nomes_atuais_episodios = natsort.natsorted(nomes_atuais_episodios, reverse=False)

    def f(x): return x if x != "" else show['name']
    if argumentos.extensao == ".ass":
        nomes_novos_episodios = [f(show['_embedded']['seasons'][int(argumentos.temporada) - 1]['name']) + " (" + show['_embedded']['seasons'][int(
            argumentos.temporada) - 1]['premiereDate'].split("-")[0] + ") S" + argumentos.temporada.zfill(2) + "E" + str(c).zfill(2) + ".pt-br" for c, a in enumerate(nomes_atuais_episodios, 1)]
    else:
        nomes_novos_episodios = [f(show['_embedded']['seasons'][int(argumentos.temporada) - 1]['name']) + " (" + show['_embedded']['seasons'][int(
            argumentos.temporada) - 1]['premiereDate'].split("-")[0] + ") S" + argumentos.temporada.zfill(2) + "E" + str(c).zfill(2) for c, a in enumerate(nomes_atuais_episodios, 1)]

    if argumentos.extensao == EXT_LEG:

        dir_bak_leg(
            dir_trabalho=argumentos.dir_trabalho,
            arquivos_de_legenda=os.listdir(argumentos.dir_trabalho)
        )

        LibAniHubSub.tratamento_legendas(
            dir_trabalho=argumentos.dir_trabalho,
            arquivos_de_legenda=os.listdir(argumentos.dir_trabalho + '/' + LibAniHubSub.CONFIG["dirLegendaAntiga"]),
            res_x=argumentos.res_x,
            res_y=argumentos.res_y
        )

    print(
        tabulate(
            [list(ele) for ele in zip(nomes_atuais_episodios, nomes_novos_episodios)],
            headers=['Nomes Antigos', 'Novos Nomes'],
            tablefmt="fancy_grid"
        )
    )

    r = input("Aperte Enter para contirnuar:")

    LibAniHubSub.renomeia_arquivos_generico(
        dir_trabalho=argumentos.dir_trabalho,
        lista_de_nomes_antigos=nomes_atuais_episodios,
        lista_de_nomes_novos=nomes_novos_episodios,
        extensao=argumentos.extensao
    )

    dirNameShow = show['name'] + " (" + show['premiered'].split("-")[0] + ")"

    try:
        # Create target Directory
        os.mkdir(argumentos.dir_trabalho + '/' + dirNameShow)
        print("Directory ", argumentos.dir_trabalho + '/' + dirNameShow,  " Created ")
    except FileExistsError:
        print("Directory ", argumentos.dir_trabalho + '/' + dirNameShow,  " already exists")

    dirNameTemporada = "Season " + argumentos.temporada

    try:
        # Create target Directory
        os.mkdir(argumentos.dir_trabalho + '/' + dirNameShow + '/' + dirNameTemporada)
        print("Directory ", argumentos.dir_trabalho + '/' + dirNameShow + '/' + dirNameTemporada,  " Created ")
    except FileExistsError:
        print("Directory ", argumentos.dir_trabalho + '/' + dirNameShow + '/' + dirNameTemporada,  " already exists")

    for arquivo in nomes_novos_episodios:
        shutil.move(argumentos.dir_trabalho + '/' + LibAniHubSub.trocar_caractere(arquivo) + argumentos.extensao,
                    argumentos.dir_trabalho + '/' + dirNameShow + '/' + dirNameTemporada + '/' + LibAniHubSub.trocar_caractere(arquivo) + argumentos.extensao)
    
    dir_backup='Legendas Originais'

    if argumentos.extensao == ".ass":
        shutil.move(argumentos.dir_trabalho + '/' + dir_backup, argumentos.dir_trabalho + '/' + dirNameShow + '/' + dirNameTemporada)

    print("SUCESSO")
