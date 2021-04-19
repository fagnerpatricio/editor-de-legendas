import ntpath
import os
import shutil
import natsort
import requests
import re
import json
import xml.etree.ElementTree as ET

import pysubs2
from tabulate import tabulate
#from matplotlib import font_manager

# Bloco de Configurações
CONFIG = {"dirLegendaAntiga": "Legendas Originais"}
RELAORIO_DE_FONTES = {}

fontes_legendas_otaku = {
    'Arial': 'Roboto',
    'Comic Sans MS': 'Comic Neue',
    'Times New Roman': 'Roboto Slab',
    'Trebuchet MS': 'Trebuchet MS',
    'Verdana': 'Arimo'
}

fontes_legendas_otaku_extendido = {
    'Arial': 'Roboto',
    'Comic Sans MS': 'Comic Neue',
    'Times New Roman': 'Roboto Slab',
    'TimesNewRoman': 'Roboto Slab',
    'Verdana': 'Arimo',
    'Ad Hoc': 'Metal Mania',
    'Franklin Gothic Book': 'Libre Franklin',
    'Utopia Std Display': 'Playfair Display',
    'Source Sans Pro Black' : 'Roboto',
    'Source Sans Pro': 'Roboto'
}

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

SoFonte = {"fontname": "Trebuchet MS"}

estilos = {'Default': Padrao, 'Itálico': Italico}

CONFIG_ESTILOS_LEGENDAS = json.loads(json.dumps(estilos))

# ==================================================================================================
'''
    Funções Comuns a Todos
'''
# ==================================================================================================


def trocar_caractere(texto):
    replacements = {"?": "^", "/": "~"}
    # replacements = {"-":"~"}

    return "".join([replacements.get(c, c) for c in texto])


def exibe_previa(lista_de_nomes_de_episodios, dir_legendas, dir_episodios):
    print(
        tabulate(
            [list(ele) for ele in zip(lista_de_nomes_de_episodios, dir_legendas, dir_episodios)],
            headers=['Novo Nome Dos Arquivos', 'Arquivos de Legendas', 'Arquivo de Vídeo'],
            tablefmt="fancy_grid"
        )
    )


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


# def cheque_fontes_instaladas(subs, arquivo):
#     for style in subs.styles.values():
#         if ntpath.basename(font_manager.findfont(style.fontname.replace('-', " "))) == 'DejaVuSans.ttf':
#             arquivo.write("Fonte: --> " + style.fontname + '\n')

# def cheque_fontes_instaladas(subs):
#     for style in subs.styles.values():
#         if ntpath.basename(font_manager.findfont(style.fontname.replace('-', " "))) == 'DejaVuSans.ttf':
#             RELAORIO_DE_FONTES[style.fontname] = "Faltando"


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
        style.outline = int(style.outline * escala)
        style.shadow = int(style.shadow * escala)
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


# ==================================================================================================
def renomeia_arquivos(dir_trabalho, lista_de_nomes_de_episodios, dir_legendas, dir_episodios, extensao_legendas='.ass', extensao_video='.mkv'):
    # Renomeando os arquivos
    for nn_episodio, tn_leg, tn_ep in zip(lista_de_nomes_de_episodios, dir_legendas, dir_episodios):
        shutil.move(dir_trabalho + '/' + tn_leg, dir_trabalho + '/' + trocar_caractere(nn_episodio.rstrip()) + ".pt" + extensao_legendas)
        shutil.move(dir_trabalho + '/' + tn_ep, dir_trabalho + '/' + trocar_caractere(nn_episodio.rstrip()) + extensao_video)


def renomeia_arquivos_generico(dir_trabalho, lista_de_nomes_novos, lista_de_nomes_antigos, extensao='.mkv'):
    # Renomeando os arquivos
    for nn_arquivo, an_arquivo in zip(lista_de_nomes_novos, lista_de_nomes_antigos):
        shutil.move(dir_trabalho + '/' + an_arquivo, dir_trabalho + '/' + trocar_caractere(nn_arquivo.rstrip()) + extensao)        

def tratamento_legendas_crunchroll(dir_trabalho=None, dir_legenda=None, dir_backup='Legendas Originais', extensao_legenda='.ass'):

    for arquivo_de_legenda in dir_legenda:
        if arquivo_de_legenda.endswith(extensao_legenda):
            subs = pysubs2.load(dir_trabalho + '/' + dir_backup + '/' + arquivo_de_legenda, encoding="utf-8")
            corrigi_estilos_crunchroll(subs)
            # cheque_fontes_instaladas(subs)
            subs.save(dir_trabalho + '/' + arquivo_de_legenda)


def tratamento_legendas(dir_trabalho=None, arquivos_de_legenda=None, dir_backup='Legendas Originais', res_x=640, res_y=360):

    for arquivo_de_legenda in arquivos_de_legenda:
        subs = pysubs2.load(dir_trabalho + '/' + dir_backup + '/' + arquivo_de_legenda, encoding="utf-8")
        resize_subs(subs, res_x_dest=res_x)
        corrigi_estilos(subs, res_x=res_x, res_y=res_y)
        # cheque_fontes_instaladas(subs)
        subs.save(dir_trabalho + '/' + arquivo_de_legenda)

    with open('file.txt', 'w') as file:
        file.write(json.dumps(RELAORIO_DE_FONTES))


def tratamento_legendas_tvmaze(dir_trabalho=None, arquivos_de_legenda=None, dir_backup='Legendas Originais', extensao_legenda='.ass', res_x=640, res_y=360):

    for arquivo_de_legenda in arquivos_de_legenda:
        if arquivo_de_legenda.endswith(extensao_legenda):
            subs = pysubs2.load(dir_trabalho + '/' + dir_backup + '/' + arquivo_de_legenda, encoding="utf-8")
            resize_subs(subs, res_x_dest=res_x)
            corrigi_estilos(subs, res_x=res_x, res_y=res_y)
            # cheque_fontes_instaladas(subs)
            subs.save(dir_trabalho + '/' + arquivo_de_legenda)


def tratamento_legendas_anidb(dir_trabalho=None, arquivos_de_legenda=None, dir_backup='Legendas Originais', extensao_legenda='.ass', res_x=640, res_y=360):

    for arquivo_de_legenda in arquivos_de_legenda:
        if arquivo_de_legenda.endswith(extensao_legenda):
            subs = pysubs2.load(dir_trabalho + '/' + dir_backup + '/' + arquivo_de_legenda, encoding="utf-8")
            resize_subs(subs, res_x_dest=res_x)
            corrigi_estilos(subs, res_x=res_x, res_y=res_y)
            # cheque_fontes_instaladas(subs)
            subs.save(dir_trabalho + '/' + arquivo_de_legenda)


# ==================================================================================================


def corrigi_estilos_crunchroll(subs):
    subs.info = {
        "Title": "[Legendas-Otaku] Português (Brasil)",
        "PlayResX": subs.info["PlayResX"],
        "PlayResY": subs.info["PlayResY"],
        "ScriptType": "v4.00+",
        "WrapStyle": "0"
    }

    subs.aegisub_project = {}
    lista_com_contadores_de_estilos = {}

    # Verifica se um Stylo está sendo usado
    for nome_estilo, estilo in zip(subs.styles.keys(), subs.styles.values()):
        contador = 0
        for line in subs:
            if nome_estilo == line.style:
                contador += 1

        lista_com_contadores_de_estilos[nome_estilo] = contador

        try:
            estilo.fontname = fontes_legendas_otaku[estilo.fontname]
        except:
            continue

    # Remove o estilo caso ele não esteja sendo usado
    for estilo in lista_com_contadores_de_estilos:
        if lista_com_contadores_de_estilos[estilo] == 0:
            subs.styles.pop(estilo)


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

        try:
            estilo.fontname = fontes_legendas_otaku_extendido[estilo.fontname]
        except:
            None

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

# ==================================================================================================


def renomeia_crunchroll(dir_trabalho):
    # LerAquivos
    dir_episodios = [x for x in os.listdir(dir_trabalho) if (x.endswith(".mp4") or x.endswith(".mkv"))]
    dir_legendas = [x for x in os.listdir(dir_trabalho) if x.endswith(".ass")]

    # Ordena Nomes
    dir_episodios = natsort.natsorted(dir_episodios, reverse=False)
    dir_legendas = natsort.natsorted(dir_legendas, reverse=False)

    # Criar Lista de nomes de Episódios
    lista_de_nomes_de_episodios = []
    lista_de_nomes_de_episodios = ['#' + os.path.splitext(x.split('Episódio ')[1])[0].replace(".ptBR", "") for x in dir_legendas]
    lista_de_nomes_de_episodios = natsort.natsorted(lista_de_nomes_de_episodios, reverse=False)

    # Exibe prévia
    exibe_previa(lista_de_nomes_de_episodios, dir_legendas, dir_episodios)

    input('Aperte \'Enter\' para contirnuar:')

    renomeia_arquivos(dir_trabalho=dir_trabalho, lista_de_nomes_de_episodios=lista_de_nomes_de_episodios,
                      dir_legendas=dir_legendas, dir_episodios=dir_episodios)


def renomeia_tvmaze(dir_trabalho, lista_de_episodios_tvmaze, temporada_episodios=1):
    # LerAquivos
    dir_episodios = [x for x in os.listdir(dir_trabalho) if x.endswith(".mkv")]
    dir_legendas = [x for x in os.listdir(dir_trabalho) if x.endswith(".ass")]

    # Ordena Nomes
    dir_episodios = natsort.natsorted(dir_episodios, reverse=False)
    dir_legendas = natsort.natsorted(dir_legendas, reverse=False)

    lista_de_nomes_de_episodios = []

    # Criar Lista de nomes de Episódios
    for episodio in lista_de_episodios_tvmaze:
        if episodio["number"] != None and episodio["season"] == temporada_episodios:
            lista_de_nomes_de_episodios.append("#" + str(episodio["number"]) + ' - ' + episodio["name"])
    # Exibe prévia
    exibe_previa(lista_de_nomes_de_episodios, dir_legendas, dir_episodios)

    input('Aperte \'Enter\' para contirnuar:')

    renomeia_arquivos(dir_trabalho=dir_trabalho, lista_de_nomes_de_episodios=lista_de_nomes_de_episodios,
                      dir_legendas=dir_legendas, dir_episodios=dir_episodios)

def renomeia_tvmaze_kodi(dir_trabalho, info_serie ,lista_de_episodios_tvmaze, temporada_episodios=1):
    # LerAquivos
    dir_episodios = [x for x in os.listdir(dir_trabalho) if x.endswith(".mkv")]
    dir_legendas = [x for x in os.listdir(dir_trabalho) if x.endswith(".ass")]

    # Ordena Nomes
    dir_episodios = natsort.natsorted(dir_episodios, reverse=False)
    dir_legendas = natsort.natsorted(dir_legendas, reverse=False)

    lista_de_nomes_de_episodios = []

    # Criar Lista de nomes de Episódios
    for episodio in lista_de_episodios_tvmaze:
        if episodio["number"] != None and episodio["season"] == temporada_episodios:
            lista_de_nomes_de_episodios.append("#" + str(episodio["number"]) + ' - ' + episodio["name"])
    # Exibe prévia
    exibe_previa(lista_de_nomes_de_episodios, dir_legendas, dir_episodios)

    input('Aperte \'Enter\' para contirnuar:')

    renomeia_arquivos(dir_trabalho=dir_trabalho, lista_de_nomes_de_episodios=lista_de_nomes_de_episodios,
                      dir_legendas=dir_legendas, dir_episodios=dir_episodios)


def renomeia_anidb(dir_trabalho, lista_de_episodios_anidb):
    # LerAquivos
    dir_episodios = [x for x in os.listdir(dir_trabalho) if x.endswith(".mkv")]
    dir_legendas = [x for x in os.listdir(dir_trabalho) if x.endswith(".ass")]

    # Ordena Nomes
    dir_episodios = natsort.natsorted(dir_episodios, reverse=False)
    dir_legendas = natsort.natsorted(dir_legendas, reverse=False)

    lista_de_nomes_de_episodios = []

    # Criar Lista de nomes de Episódios
    for episodio in lista_de_episodios_anidb.iter("episode"):
        for titulo in episodio.findall('title'):
            if titulo.attrib['{http://www.w3.org/XML/1998/namespace}lang'] == 'en':
                try:
                    lista_de_nomes_de_episodios.append('#' + str(int(episodio.find("epno").text)) + ' - ' + titulo.text)
                except:
                    continue

    # Exibe prévia
    exibe_previa(lista_de_nomes_de_episodios, dir_legendas, dir_episodios)

    input('Aperte \'Enter\' para contirnuar:')

    renomeia_arquivos(dir_trabalho=dir_trabalho, lista_de_nomes_de_episodios=lista_de_nomes_de_episodios,
                      dir_legendas=dir_legendas, dir_episodios=dir_episodios)


def renomeia_apenas_tvmaze(dir_trabalho, lista_de_episodios_tvmaze, extensao='.mkv', temporada_episodios=1):
    # LerAquivos
    dir_arquivos = [x for x in os.listdir(dir_trabalho) if x.endswith(extensao)]
    # Ordena Nomes
    dir_arquivos = natsort.natsorted(dir_arquivos, reverse=False)

    lista_de_nomes_de_episodios = []

    # Criar Lista de nomes de Episódios
    for episodio in lista_de_episodios_tvmaze:
        if episodio["number"] != None and episodio["season"] == temporada_episodios:
            lista_de_nomes_de_episodios.append("#" + str(episodio["number"]) + ' - ' + episodio["name"])

    # Exibe prévia
    exibe_previa(lista_de_nomes_de_episodios, dir_arquivos, dir_arquivos)

    input('Aperte \'Enter\' para contirnuar:')

    # renomeia_arquivos_generico(dir_trabalho=dir_trabalho, lista_de_nomes_de_episodios=lista_de_nomes_de_episodios, dir_arquivos=dir_arquivos)



# ==================================================================================================
#
#     Funções Relacionadas a TVMaze
#
# ==================================================================================================


def baixa_tvmaze_legendas(codigo=None):
    return requests.get('http://api.tvmaze.com/shows/' + codigo + '/episodes', verify=True).json()

def baixa_tvmaze_infos(codigo=None):
    show = requests.get('http://api.tvmaze.com/shows/' + codigo, verify=True).json()
    episodios = requests.get('http://api.tvmaze.com/shows/' + codigo + '/episodes', verify=True).json()

    return show, episodios


# ==================================================================================================
#
#     Funções Relacionadas a AniDB
#
# ==================================================================================================


def baixa_anidb_legendas(client=None, clientver=None, codigo=None):
    raiz = ET.fromstring(requests.get(
        "http://api.anidb.net:9001/httpapi?request=anime&client=fagnerpc&clientver=2&protover=1&aid=" + codigo, verify=True).content)
    return raiz


# ==================================================================================================
'''
    Funções Relacionadas a Sincroninações de Tempo
'''
# ==================================================================================================


def desloca_subs(subs, h=0, m=0, s=0, hf=0, mf=0, sf=0, delta_deslocamento=0):
    tempo_inicial = (h * 3600000) + (m * 60000) + (s * 1000)
    tempo_final = (hf * 3600000) + (mf * 60000) + (sf * 1000)
    delta_deslocamento = delta_deslocamento

    for line in subs:
        if (line.start >= tempo_inicial and line.end <= tempo_final):
            line.start += delta_deslocamento
            line.end += delta_deslocamento


def resincroniza_legendas(dir_trabalho, arquivos_de_legenda, dir_backup='Legendas Originais', extensao_legenda='.ass', h=0, m=0, s=0, hf=0, mf=0, sf=0, delta_deslocamento=0):
    for arquivo_de_legenda in arquivos_de_legenda:
        if arquivo_de_legenda.endswith(extensao_legenda):
            subs = pysubs2.load(dir_trabalho + '/' + dir_backup + '/' + arquivo_de_legenda, encoding="utf-8")
            desloca_subs(subs, h, m, s, hf, mf, sf, delta_deslocamento)
            subs.save(dir_trabalho + '/' + arquivo_de_legenda)

# busca_de_padroes = [tuple(i for i in m if i) for m in re.findall(r'[\\|\(|\|\,}](m)(\s.+?)[\)|\{]|(pos|move|org)(\()(.+?)\)|(fs)(\d+\.?\d+)',line.text)]
# busca_de_padroes = [tuple(i for i in m if i) for m in re.findall(r'(move|clip)(\()((?:\-?\,?\d+\.?\d+\W+?\d+\.?\d+)(?:\-?\,?\d+\.?\d+\W+?\d+\.?\d+)?)|[\\|\(|\}|\,](m)(\s.+?)[\)|\{]|(pos|org)(\()(.+?)\)|(fs)(\d+\.?\d+)',line.text)]
# busca_de_padroes = [tuple(i for i in m if i) for m in re.findall(r'(move|clip|pos|org|fs)(\()?((?:\,?\-?\d+\.?\d+){1,4})|[\\|\(|\}|\,](m)(\s.+?)[\{|\)|\n]',line.text)]
# busca_de_padroes = [tuple(i for i in m if i) for m in re.findall(r'(move|clip|pos|org|fs)(\()?((?:\,?\-?\d+\.?\d+){1,4})|[\\|\(|\}|\,](m)(\s.+\d)[\(|\{]?',line.text)]

# r'(move|clip|pos|org|fs)(\()?(0?,?(?:\-?\d+\,?\.?\d+\,?){1,4})|(m)(\s[^\{\)\n]+)',


# def corrigi_estilos_tvmaze(subs, res_x=640, res_y=360):
#     subs.info = {
#         "Title": "[Legendas-Otaku] Português (Brasil)",
#         "PlayResX": res_x,
#         "PlayResY": res_y,
#         "ScriptType": "v4.00+",
#         "WrapStyle": "0"
#     }

#     subs.aegisub_project = {}

#     lista_com_contadores_de_estilos = {}

#     def altera_elementos(x, y): return x if x else y
#     def altera_cor(x, y): return pysubs2.Color(*x) if True else y

#     for nome_estilo, estilo in zip(subs.styles.keys(), subs.styles.values()):
#         for atributo in frozenset(estilo.FIELDS):
#             try:
#                 if any(x == atributo for x in ["backcolor", "outlinecolor", "secondarycolor", "primarycolor"]):
#                     vars(estilo)[atributo] = altera_cor(CONFIG_ESTILOS_LEGENDAS[nome_estilo][atributo], vars(estilo)[atributo])
#                 else:
#                     vars(estilo)[atributo] = altera_elementos(CONFIG_ESTILOS_LEGENDAS[nome_estilo][atributo], vars(estilo)[atributo])
#             except:
#                 continue

#         try:
#             estilo.fontname = fontes_legendas_otaku_extendido[estilo.fontname]
#         except:
#             continue

#         # Verifica se um Stylo está sendo usado
#         contador = 0
#         for line in subs:
#             if nome_estilo == line.style:
#                 contador += 1

#         lista_com_contadores_de_estilos[nome_estilo] = contador

#     # Remove o estilo caso ele não esteja sendo usado
#     for estilo in lista_com_contadores_de_estilos:
#         if lista_com_contadores_de_estilos[estilo] == 0:
#             subs.styles.pop(estilo)
