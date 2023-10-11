from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import re
from datetime import timedelta,datetime
import os


def buscar_bloque(driver, since):
    #Los volumenes estan agrupados según su año en bloques desplegables. Esta funcion se encarga de buscar el adecuado segun la fecha introducida.
    #Si encuentra un bloque del mismo año que la fecha, devuelve el numero de orden del bloque. Si no, devuelve 0, que significa que se debe cambiar de pagina
    i = 1
    bloque_malo = 0
    pattern = r"\b(19|20)\d{2}\b"
    while(i<=20):
        time.sleep(1)
        titulo_bloque = driver.find_element(By.XPATH, f'//*[@id="all-issues"]/div[1]/ol/li[{i}]').text
        match = re.search(pattern, titulo_bloque)
        year_bloque = match.group()
        print("Buscando en volumenes de ", year_bloque, "...")
        if(int(year_bloque)<=since.year):
            bloque_bueno = i
            return bloque_bueno
        else: 
            i+=1
    return bloque_malo

def contar_volumenes(driver, li):
    #Esta funcion devuelve el numero de volumenes que hay dentro de un bloque
    volumenes = driver.find_elements(By.XPATH, f'//*[@id="all-issues"]/div[1]/ol/li[{li}]/div/section/div')
    return len(volumenes)

def contar_articulos(driver):
    #Esta funcion devuelve el numero de articulos que hay dentro de un volumen
    articulos = driver.find_elements(By.XPATH, '//*[@id="article-list"]/form/div/div[2]/ol/li')
    return len(articulos)

def avanzar_pagina(driver, page):
    #Esta funcion avanza una pagina para poder buscar por bloques mas antiguos
    page+=1
    driver.get(f"https://www.sciencedirect.com/journal/information-sciences/issues?page={page}")
    time.sleep(0.5)
    return page

def buscar_volumen(driver, since, li):
    #se busca el volumen que tenga una fecha acorde con el since que nos dan
        num_volumen = 0
        no_hay_volumen = 0
        num_volumes_en_ano = contar_volumenes(driver, li)
        for num_volumen in range(num_volumes_en_ano):
            fecha = driver.find_element(By.XPATH, f'//*[@id="all-issues"]/div[1]/ol/li[{li}]/div/section/div[{num_volumen+1}]/span/h3').text
            patron = r'(\d{1,2} \w+ \d{4})'
            formato_fecha = "%d %B %Y"
            if not re.search(patron, fecha):
                patron = r'(\w+ \d{4})'
                formato_fecha = "%B %Y"
                if not re.search(patron, fecha):
                    patron = r'(\d{4})'
                    formato_fecha = "%Y"
                    if not re.search(patron, fecha):
                        print('formato no pensado')          

            fecha_texto = re.search(patron, fecha).group()
            fecha_final = datetime.strptime(fecha_texto, formato_fecha)
            print(fecha_final)
            if fecha_final > since:
                num_volumen+=1
            elif fecha_final <= since:
                num_volumen = num_volumen + 1
                return num_volumen
            
        return no_hay_volumen

def entrar_en_volumen(driver, li, volumen):
    #Esta funcion entra en un volumen y lo coloca en una nueva pestaña
    volumen = driver.find_element(By.XPATH, f'//*[@id="all-issues"]/div[1]/ol/li[{li}]/div/section/div[{volumen}]/a')
    volumen.send_keys(Keys.CONTROL + Keys.RETURN)
    driver.switch_to.window(driver.window_handles[1])
    time.sleep(2)
    return 

def entrar_en_articulo(driver, articulo):
    #Esta funcion entra en un articulo y lo coloca en una nueva pestaña
    elemento = driver.find_element(By.XPATH, f'//*[@id="article-list"]/form/div[1]/div[2]/ol/li[{articulo}]/dl/dt/h3/a')
    elemento.send_keys(Keys.CONTROL + Keys.RETURN)
    driver.switch_to.window(driver.window_handles[2])
    time.sleep(1)
    return

def buscar_articulos(driver, articulos_pedidos, lista_info_articulos, since):
    #Esta funcion mira los articulos dentro de un volumen. Si el articulo es de tipo "Research article", comprueba su fecha.
    #Dependiendo de la fecha introducida el articulo es aceptado o no
    #Si el articulo es aceptado, lo mete en la lista de articulos deseados
    #La funcion busca articulos en el volumen hasta que se acaben, o hasta que se alcance el numero de articulos deseados
    articulo = 1
    n_art = articulos_pedidos
    num_articulos = contar_articulos(driver)
    print("\nHay un total de", num_articulos, "articulos\n")
    while(articulo <= num_articulos and n_art > 0):
        tipo = driver.find_element(By.XPATH, f'//*[@id="article-list"]/form/div/div[2]/ol/li[{articulo}]/dl/dd[1]/span[1]').text
        if tipo == 'Research article':
            entrar_en_articulo(driver, articulo)
            info_articulo = extraer_info_articulo(driver)
            if(comprobar_fecha(info_articulo, since) == 1):
                print("\nArticulo aceptado\n")
                lista_info_articulos.append(info_articulo)
                n_art -=1
            else:
                print("\nARTICULO RECHAZADO\n")
            print(n_art, " Articulos restantes")
            driver.close()
            driver.switch_to.window(driver.window_handles[1])
        articulo+=1
    return articulos_pedidos - n_art

def sacar_fecha_articulo(driver):
    #Esta funcion devuelve la fecha de un articulo, normalmente denominada como "Received"
    #Si no tuviese esta denominacion, buscaria por "Available Online"
    #Para buscar la fecha, primero se debe hacer click en el boton desplegable
    time.sleep(1)
    boton_desplegable = driver.find_element(By.XPATH, '//*[@id="show-more-btn"]')
    boton_desplegable.click()
    time.sleep(1)
    fechas_cadena = driver.find_element(By.XPATH, '//*[@id="banner"]/div[1]/p').text
    patron = r"Received\s+(\d+\s+\w+\s+\d{4})"
    try:
        fecha_texto = re.search(patron, fechas_cadena).group(1)
    except:
        patron = r"Available online (\d{1,2} \w+ \d{4})"
    fecha_texto = re.search(patron, fechas_cadena).group(1)
    print("Fecha del articulo: ", fecha_texto)
    formato_fecha = "%d %B %Y"
    fecha_final = datetime.strptime(fecha_texto, formato_fecha)
    return fecha_final

def extraer_info_articulo(driver):
    #Esta funcion devuelve una lista con toda la informacion de un articulo (Nombre, titulo, fecha, abstract y keywords)
    #El nombre sera comun para todos, ya que todos pertenecen a la misma pagina web
    #Hay una pequeñisima probabilidad de que un articulo tenga su abstract dentro de un archivo pdf al que se tendria que acceder.
    #Si esto ocurre, se ignora este abstract
    #Si un articulo tiene keywords, las coloca dentro de una lista. Si no tiene, deja la lista vacia
    nombre = "Information Sciences"
    titulo = titulo = driver.find_element(By.XPATH, '//*[@id="screen-reader-main-title"]/span').text
    fecha = sacar_fecha_articulo(driver)
    try:
        abstract = driver.find_element(By.XPATH, '//div[@class="abstract author"]/div/p').text
    except:
        abstract = "Abstract no disponible"
    keywords = []
    num = driver.find_elements(By.CLASS_NAME, 'keyword')
    keynum = len(num)
    for div in range(keynum):
        try:
            keyword = driver.find_element(By.XPATH, f'//div[{div+1}][@class="keyword"]/span').text
        except:
            continue
        keyword = driver.find_element(By.XPATH, f'//div[{div+1}][@class="keyword"]/span').text
        keywords.append(keyword)
    info_articulo = (nombre, titulo, fecha, abstract, keywords)
    return info_articulo

def siguiente_volumen(driver, li, volumen_actual, page):
    #Esta funcion sirve para saltar de un volumen al siguiente
    #Si estamos en el ultimo volumen de un bloque, se salta al siguiente y se coloca en el primer volumen
    #Si ademas estamos en el ultimo bloque de la pagina, avanza a la siguiente y se coloca en el primer bloque
    #Ya que el primer bloque de cada pagina aparece ya desplegado por defecto, no hace falta hacer click.
    #A partir de este, en todos los bloques es necesario hacer click para desplegarlos antes de acceder a ellos
    volumen = volumen_actual
    num_volumenes = contar_volumenes(driver, li)
    if(volumen == num_volumenes): 
        li += 1
        volumen = 1
    else:
        volumen += 1
    if(li > 20):
        page = avanzar_pagina(driver, page)
        li = 1
    if(li != 1):
        bloque = driver.find_element(By.XPATH, f'//*[@id="all-issues"]/div[1]/ol/li[{li}]')
        bloque.click()
    entrar_en_volumen(driver, li, volumen)
    return page

def comprobar_fecha(info_articulo, fecha_input):
    #Esta funcion se encarga de aceptar o rechazar los articulos segun su fecha y la fecha introducida
    fecha_articulo = info_articulo[2]
    if(fecha_articulo > fecha_input):
        return 0
    else:
        return 1

def extract(n_art, since=None):
    #Esta funcion se encarga de iniciar el driver de chrome y de buscar los articulos deseados segun la fecha introducida, haciendo uso del resto de funciones
    #Si se pide un numero de articulos menor o igual que 0, se saca siempre al menos 1 articulo
    #si no se especifica fecha, se busca segun la fecha actual
    page = 1
    lista_info_articulos = []
    if(since == None):
        since = datetime.now()
    if(n_art <= 0):
        n_art = 1
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(f"https://www.sciencedirect.com/journal/information-sciences/issues?page={page}")
    time.sleep(1)
    li = buscar_bloque(driver, since)
    while(li == 0):
        page+=1
        driver.get(f"https://www.sciencedirect.com/journal/information-sciences/issues?page={page}")
        time.sleep(1)
        li = buscar_bloque(driver, since)
    if(li != 1):
        bloque = driver.find_element(By.XPATH, f'//*[@id="all-issues"]/div[1]/ol/li[{li}]')
        bloque.click()
    volumen = buscar_volumen(driver, since, li)
    if(volumen == 0):
        li += 1
        volumen = 1
        if(li>20):
            li = 1
            page = avanzar_pagina(driver, page)
        else:
            bloque = driver.find_element(By.XPATH, f'//*[@id="all-issues"]/div[1]/ol/li[{li}]')
            bloque.click()
    entrar_en_volumen(driver, li, volumen)

    while(n_art > 0):
        articulos_encontrados = buscar_articulos(driver, n_art, lista_info_articulos, since)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        page = siguiente_volumen(driver, li, volumen, page)
        n_art = n_art - articulos_encontrados
    driver.close()
    return lista_info_articulos

def iniciar():
    #Esta funcion se encarga de configurar la busqueda de articulos, como el numero de estos que se quiere sacar y a partir de que fecha
    #Si no se quiere introducir ninguna fecha, se selecciona la fecha actual por defecto
    print("¿Cuantos articulos quieres sacar?")
    n_art = round(float(input()))
    while(n_art <= 0):
        print("Por favor, introduce un numero mayor que 0\n")
        n_art = round(float(input()))
    print("¿Quieres introducir una fecha? (s/n)")
    quiere_fecha = input()
    if(quiere_fecha == "s"):
        print("Pues introdúcela siguendo el formato DD Month YYYY.\nPor ejemplo, '1 January 2023'")
        fecha_input = input()
        fecha = datetime.strptime(fecha_input, "%d %B %Y") + timedelta(days=365)
    else:
        fecha = datetime.now()
    since = fecha 
    print("Buscando desde ", since, "\n")
    lista_final = extract(n_art, since)
    return lista_final

#main

resultado = iniciar()

def imprimir_informacion(lista_info_articulos):
    #Esta funcion crea un archivo txt en el mismo directorio en el que se encuentre el archivo py de este programa
    #En el, imprime la informacion recopilada de todos los articulos que han sido aceptados
    path = os.path.abspath(__file__)
    dir = os.path.dirname(path)
    file_path = os.path.join(dir, 'Information_Sciences.txt')
    print("\nImprimiendo informacion...\n")
    with open(file_path, "w", encoding="utf-8") as f:
        for elemento in lista_info_articulos:
            f.write(str(elemento) + "\n\n")

imprimir_informacion(resultado)

