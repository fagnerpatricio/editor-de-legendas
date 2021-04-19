#!/usr/bin/env python3

# Importações do Sistema
import argparse
import os
import shutil
import natsort
import re
import shutil
import requests
import pysubs2
import json
from tabulate import tabulate

# Importações Personalizadas
import LibAniHubSub

# Configurações
EXT_LEG = ".ass"
EXT_MKV = ".mkv"
EXT_MP4 = ".mp4"

Padrao = {
    "fontname": "Trebuchet MS",
    "fontsize": 21,
    "backcolor": [0, 0, 0, 0],
    "outlinecolor": [25, 25, 25, 0],
    "secondarycolor": [0, 0, 255, 0],
    "primarycolor": [255, 255, 255, 0],
    "bold": -1,
    "italic": 0,
    "underline": 0,
    "strikeout": 0,
    "scalex": 100,
    "scaley": 100,
    "spacing": 0,
    "angle": 0,
    "borderstyle": 1,
    "outline": 2,
    "shadow": 1,
    "alignment": 2,
    "marginl": 40,
    "marginr": 40,
    "marginv": 15,
    "encoding": 0
}

Italico = {
    "fontname": "Trebuchet MS",
    "fontsize": 21,
    "backcolor": [0, 0, 0, 0],
    "outlinecolor": [25, 25, 25, 0],
    "secondarycolor": [0, 0, 255, 0],
    "primarycolor": [255, 255, 255, 0],
    "bold": -1,
    "italic": -1,
    "underline": 0,
    "strikeout": 0,
    "scalex": 100,
    "scaley": 100,
    "spacing": 0,
    "angle": 0,
    "borderstyle": 1,
    "outline": 2,
    "shadow": 1,
    "alignment": 2,
    "marginl": 40,
    "marginr": 40,
    "marginv": 15,
    "encoding": 0
}

estilos = {'Default': Padrao, 'Itálico': Italico}

CONFIG_ESTILOS_LEGENDAS = json.loads(json.dumps(estilos))
RELAORIO_DE_FONTES = {}


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


def resize_subs(subs, res_x_dest=640):
    res_x_src = int(subs.info["PlayResX"])
    # res_y_src = int(subs.info["PlayResY"])
    escala = float(res_x_dest) / float(res_x_src)
    # res_y_dest = int(escala * res_y_src)

    for style in subs.styles.values():
        style.fontsize = int(style.fontsize * escala)
        style.marginl = int(style.marginl * escala)
        style.marginr = int(style.marginr * escala)
        style.marginv = int(style.marginv * escala)
        # style.outline = int(style.outline * escala)
        # style.shadow = int(style.shadow * escala)
        style.spacing = int(style.spacing * escala)

    def n(v): return str("{:.3f}".format(float(v) * escala)) if v.replace('.', '').lstrip('-').isdigit() else v

    def j(x): return " ".join([n(c) for c in re.split(r'[,\s]\s*', x[-1:][0])]
                              ) if x[0] == 'm' else ",".join([n(c) for c in re.split(r'[,\s]\s*', x[-1:][0])])

    for line in subs:
        busca_de_padroes = [
            tuple(i for i in m if i) for m in re.findall(
                r'(move|clip|pos|org)(\()(-?(?:\d+(?:\.\d*)?|\.\d+)(?:,-?(?:\d+(?:\.\d*)?|\.\d+)){0,3})|}(m)(\s[^\{\)\n]+)|(fs)(\d+\.?\d+)',
                line.text)
        ]
        for padrao in busca_de_padroes:
            try:
                line.text = line.text.replace("".join(padrao), "".join(padrao[:-1]) + j(padrao))
            except:
                continue


def corrigi_estilos(subs, res_x=640, res_y=360):
    subs.info = {
        "Title": "[Legendas-Otaku] Português (Brasil)",
        "PlayResX": res_x,
        "PlayResY": res_y,
        "ScriptType": "v4.00+",
        "WrapStyle": "0"
    }

    subs.aegisub_project = {}

    lista_com_contadores_de_estilos = {}

    def altera_elementos(x, y): return x if x else y
    def altera_cor(x, y): return pysubs2.Color(*x) if True else y

    for nome_estilo, estilo in zip(subs.styles.keys(), subs.styles.values()):
        for atributo in frozenset(estilo.FIELDS):
            try:
                if any(x == atributo for x in ["backcolor", "outlinecolor", "secondarycolor", "primarycolor"]):
                    vars(estilo)[atributo] = altera_cor(CONFIG_ESTILOS_LEGENDAS[nome_estilo][atributo], vars(estilo)[atributo])
                else:
                    vars(estilo)[atributo] = altera_elementos(CONFIG_ESTILOS_LEGENDAS[nome_estilo][atributo], vars(estilo)[atributo])
            except:
                continue        

        # Verifica se um Stylo está sendo usado
        contador = 0
        for line in subs:
            if nome_estilo == line.style:
                contador += 1

        lista_com_contadores_de_estilos[nome_estilo] = contador

    # Remove o estilo caso ele não esteja sendo usado
    for estilo in lista_com_contadores_de_estilos:
        if lista_com_contadores_de_estilos[estilo] == 0:
            subs.styles.pop(estilo)


def tratamento_legendas(dir_trabalho=None, arquivos_de_legenda=None, dir_backup='Legendas Originais', res_x=640, res_y=360):

    for arquivo_de_legenda in arquivos_de_legenda:
        subs = pysubs2.load(dir_trabalho + '/' + dir_backup + '/' + arquivo_de_legenda, encoding="utf-8")
        resize_subs(subs, res_x_dest=res_x)
        corrigi_estilos(subs, res_x=res_x, res_y=res_y)        
        subs.save(dir_trabalho + '/' + arquivo_de_legenda)

    with open('file.txt', 'w') as file:
        file.write(json.dumps(RELAORIO_DE_FONTES))


def trocar_caractere(texto):
    replacements = {"?": "^", "/": "~"}
    # replacements = {"-":"~"}

    return "".join([replacements.get(c, c) for c in texto])


def renomeia_arquivos_generico(dir_trabalho, lista_de_nomes_novos, lista_de_nomes_antigos, extensao='.mkv'):
    # Renomeando os arquivos
    for nn_arquivo, an_arquivo in zip(lista_de_nomes_novos, lista_de_nomes_antigos):
        shutil.move(dir_trabalho + '/' + an_arquivo, dir_trabalho + '/' + trocar_caractere(nn_arquivo.rstrip()) + extensao)        

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

        tratamento_legendas(
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

    renomeia_arquivos_generico(
        dir_trabalho=argumentos.dir_trabalho,
        lista_de_nomes_antigos=nomes_atuais_episodios,
        lista_de_nomes_novos=nomes_novos_episodios,
        extensao=argumentos.extensao
    )

    dirNameShow = show['name'] + " (" + show['premiered'].split("-")[0] + ")"

    try:
        # Create target Directory
        os.mkdir(argumentos.dir_trabalho + '/' + dirNameShow)
        print("Directory ", argumentos.dir_trabalho + '/' + dirNameShow,  " Criado ")
    except FileExistsError:
        print("Directory ", argumentos.dir_trabalho + '/' + dirNameShow,  " Já Existe")

    dirNameTemporada = "Season " + argumentos.temporada

    try:
        # Create target Directory
        os.mkdir(argumentos.dir_trabalho + '/' + dirNameShow + '/' + dirNameTemporada)
        print("Directory ", argumentos.dir_trabalho + '/' + dirNameShow + '/' + dirNameTemporada,  " Criado ")
    except FileExistsError:
        print("Directory ", argumentos.dir_trabalho + '/' + dirNameShow + '/' + dirNameTemporada,  " Já Existe ")

    for arquivo in nomes_novos_episodios:
        shutil.move(argumentos.dir_trabalho + '/' + LibAniHubSub.trocar_caractere(arquivo) + argumentos.extensao,
                    argumentos.dir_trabalho + '/' + dirNameShow + '/' + dirNameTemporada + '/' + LibAniHubSub.trocar_caractere(arquivo) + argumentos.extensao)
    
    dir_backup='Legendas Originais'

    if argumentos.extensao == ".ass":
        shutil.move(argumentos.dir_trabalho + '/' + dir_backup, argumentos.dir_trabalho + '/' + dirNameShow + '/' + dirNameTemporada)

    print("SUCESSO")
