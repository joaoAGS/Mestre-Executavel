import time
import os
import pyperclip
import requests
import subprocess
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ==============================================================================
# ⚙️ CONFIGURAÇÕES
# ==============================================================================

# --- AUTO-UPDATE (LINKS) ---
VERSAO_ATUAL = "1.2"
URL_VERSAO = "https://raw.githubusercontent.com/joaoAGS/Mestre-Executavel/refs/heads/main/versao.txt"
URL_EXECUTAVEL = "https://github.com/joaoAGS/Mestre-Executavel/raw/refs/heads/main/Mestre.exe"

# --- CONFIGURAÇÕES DE NAVEGAÇÃO ---
URL_DASHBOARD = "https://paineladmin3.azurewebsites.net/mobfy/dashboard"
URL_MAPA = "https://paineladmin3.azurewebsites.net/mobfy/vermapa"
URL_WHATSAPP = "https://web.whatsapp.com"

NOME_GRUPO_WHATSAPP = "MOBFY Avisos CAÇADOR"
LISTA_CORRIDAS = ["Matheus Wichmann", "Mobfy Canal"]

# TEMPOS (em minutos)
TEMPO_OFFLINE = 3
TEMPO_FROTA = 15
TEMPO_CORRIDAS = 30

# --- CONFIGURAÇÃO DE PASTA (Compatível com .exe e .py) ---
if getattr(sys, 'frozen', False):
    diretorio_base = os.path.dirname(sys.executable)
    exe_atual = sys.executable
else:
    diretorio_base = os.path.dirname(os.path.abspath(__file__))
    exe_atual = os.path.abspath(__file__)

CAMINHO_PERFIL = os.path.join(diretorio_base, "perfil_chrome")

# ==============================================================================
# 🔄 FUNÇÃO DE ATUALIZAÇÃO (CORRIGIDA)
# ==============================================================================
def verificar_atualizacao():
    print(f"🔍 Verificando atualizações... (Versão Atual: {VERSAO_ATUAL})")
    try:
        # Evita erro SSL em redes corporativas
        resposta = requests.get(URL_VERSAO, verify=False)
        versao_online = resposta.text.strip()
        
        if versao_online != VERSAO_ATUAL and versao_online != "":
            print(f"🚀 Nova versão encontrada: {versao_online}! Baixando...")
            
            resposta_exe = requests.get(URL_EXECUTAVEL, verify=False)
            
            # Define caminhos seguros
            nome_novo = os.path.join(diretorio_base, "Mestre_Novo.exe")
            
            # Salva o novo arquivo
            with open(nome_novo, 'wb') as f:
                f.write(resposta_exe.content)
            
            print("✅ Download concluído! Reiniciando para aplicar...")
            
            # CRIA O SCRIPT BAT MAIS ROBUSTO (Usa MOVE /Y para forçar)
            bat_script = f"""
            @echo off
            echo Aguardando fechamento do robo...
            timeout /t 3 /nobreak >nul
            
            echo Substituindo arquivos...
            move /y "{nome_novo}" "{exe_atual}"
            
            echo Reiniciando...
            start "" "{exe_atual}"
            
            del "%~f0"
            """
            
            bat_path = os.path.join(diretorio_base, "atualizador.bat")
            with open(bat_path, "w") as bat:
                bat.write(bat_script)
                
            # Executa o BAT e encerra o Python imediatamente
            subprocess.Popen(bat_path, shell=True)
            sys.exit()
            
        else:
            print("✅ Seu robô está atualizado.")
            
    except Exception as e:
        print(f"⚠️ Erro no Update (Ignorando): {e}")
        time.sleep(2)

# ==============================================================================
# 🛠️ FUNÇÕES DE SUPORTE
# ==============================================================================

def iniciar_driver():
    print("🚀 Iniciando Robô Mestre...")
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-data-dir={CAMINHO_PERFIL}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # Busca Chrome automaticamente
    locais = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]
    
    for caminho in locais:
        if os.path.exists(caminho):
            options.binary_location = caminho
            break

    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def enviar_whatsapp(driver, mensagem, destinatario):
    try:
        driver.switch_to.window(driver.window_handles[3])
        if "WhatsApp" not in driver.title:
            driver.get(URL_WHATSAPP)
            time.sleep(10)

        wait = WebDriverWait(driver, 40)
        
        # Busca
        try:
            box = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')))
            box.click()
            box.send_keys(Keys.CONTROL + "a")
            box.send_keys(Keys.BACKSPACE)
            box.send_keys(destinatario)
            time.sleep(2)
            box.send_keys(Keys.ENTER)
        except:
            print(f"❌ '{destinatario}' não achado.")
            return

        # Envia
        chat = wait.until(EC.presence_of_element_located((By.XPATH, '//footer//div[@contenteditable="true"]')))
        chat.click()
        time.sleep(1)
        pyperclip.copy(mensagem)
        chat.send_keys(Keys.CONTROL, 'v')
        time.sleep(1)
        chat.send_keys(Keys.ENTER)
        print(f"✅ Enviado: {destinatario}")
        time.sleep(2)
        
    except Exception as e:
        print(f"❌ Erro Zap: {e}")

def ler_texto(driver, xpath):
    try:
        el = driver.find_element(By.XPATH, xpath)
        return el.text if el.text else el.get_attribute("textContent")
    except:
        return "0"

def filtrar_dados_offline(texto):
    if not texto: return "Dados ilegíveis"
    nome, celular = "Não identificado", "Não informado"
    for linha in texto.split('\n'):
        if "Nome:" in linha or "Motorista:" in linha: 
            nome = linha.split(":")[-1].strip()
        if "Celular:" in linha or "Telefone:" in linha:
            celular = linha.split(":")[-1].strip()
    return f"🚫 Nome: {nome}\nCelular: {celular}"

# ==============================================================================
# TAREFAS
# ==============================================================================

def tarefa_offline_inteligente(driver):
    print("\n🔍 [OFFLINE] Verificando...")
    try:
        driver.switch_to.window(driver.window_handles[2])
        if driver.current_url != URL_MAPA: driver.get(URL_MAPA)
        else: driver.refresh()
        time.sleep(15)

        amarelos = driver.find_elements(By.CSS_SELECTOR, "img[src*='pin-amarelo.png']")
        qtd = len(amarelos)
        
        if qtd == 0: return

        if qtd >= 16:
            msg = f"🚨 *CRÍTICO: {qtd} OFFLINE* 🚨\nPeçam para reiniciar os celulares."
            enviar_whatsapp(driver, msg, NOME_GRUPO_WHATSAPP)
            return

        lista = []
        for pino in amarelos[:15]:
            try:
                driver.execute_script("arguments[0].click();", pino)
                time.sleep(1)
                xpath = '//*[@id="map"]/div/div[3]/div[1]/div[2]/div/div[4]'
                try:
                    txt = driver.find_element(By.XPATH, xpath).text
                    lista.append(filtrar_dados_offline(txt))
                except:
                    lista.append("Erro leitura")
                driver.find_element(By.TAG_NAME, 'body').click()
            except: continue

        if lista:
            msg = f"⚠️ *OFFLINE SEM NET ({qtd})*\n\n" + "\n\n".join(lista)
            enviar_whatsapp(driver, msg, NOME_GRUPO_WHATSAPP)

    except Exception as e: print(f"Erro Offline: {e}")

def tarefa_status_frota(driver):
    print("\n🚗 [FROTA] Contando...")
    try:
        driver.switch_to.window(driver.window_handles[1])
        if driver.current_url != URL_MAPA: driver.get(URL_MAPA)
        else: driver.refresh()
        time.sleep(15)

        livres = len(driver.find_elements(By.CSS_SELECTOR, "img[src*='verde']"))
        ocupados = len(driver.find_elements(By.CSS_SELECTOR, "img[src*='vermelho']")) + \
                   len(driver.find_elements(By.CSS_SELECTOR, "img[src*='ocupado']"))
        offline = len(driver.find_elements(By.CSS_SELECTOR, "img[src*='amarelo']"))
        
        msg = f"🚗 Frota - {time.strftime('%H:%M')}\n🟢 Livres: {livres}\n🔴 Ocupados: {ocupados}\n⚠️ Offline: {offline}"
        enviar_whatsapp(driver, msg, NOME_GRUPO_WHATSAPP)

    except Exception as e: print(f"Erro Frota: {e}")

def tarefa_corridas(driver):
    print("\n📊 [DASHBOARD] Calculando...")
    try:
        driver.switch_to.window(driver.window_handles[0])
        if driver.current_url != URL_DASHBOARD: driver.get(URL_DASHBOARD)
        else: driver.refresh()
        time.sleep(15)

        sim = ler_texto(driver, '/html/body/div/app/div/div/div[2]/div[1]/div/div[1]/h3')
        sol = ler_texto(driver, '/html/body/div/app/div/div/div[2]/div[2]/div/div[1]/h3')
        con = ler_texto(driver, '/html/body/div/app/div/div/div[2]/div[3]/div/div[1]/h3')
        por = ler_texto(driver, '/html/body/div/app/div/div/div[2]/div[4]/div/div[1]/h3')

        try:
            perdidas = int(sol.replace('.','')) - int(con.replace('.',''))
        except: perdidas = "?"

        msg = f"*📊 Relatório - {time.strftime('%H:%M')}*\n🔢 Simul: {sim}\n📩 Solic: {sol}\n✅ Conc: {con}\n❌ Canc/Perd: {perdidas}\n📈 Conv: {por}"
        
        for dest in LISTA_CORRIDAS:
            enviar_whatsapp(driver, msg, dest)

    except Exception as e: print(f"Erro Dash: {e}")

# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == "__main__":
    
    # Se rodar como .exe, verifica update
    if getattr(sys, 'frozen', False):
        verificar_atualizacao()

    if not os.path.exists(CAMINHO_PERFIL):
        os.makedirs(CAMINHO_PERFIL)
        
    os.system("taskkill /F /IM chrome.exe /T >nul 2>&1")
    
    driver = iniciar_driver()
    
    # Abre abas
    driver.get(URL_DASHBOARD)
    for i in range(3): 
        driver.execute_script("window.open('');")
    
    abas = driver.window_handles
    driver.switch_to.window(abas[1]); driver.get(URL_MAPA)
    driver.switch_to.window(abas[2]); driver.get(URL_MAPA)
    driver.switch_to.window(abas[3]); driver.get(URL_WHATSAPP)
    
    print("\n⏳ 60s para LOGIN...")
    time.sleep(60)
    print("🤖 ROBÔ RODANDO!")

    t_off = t_frota = t_corr = 0
    
    while True:
        agora = time.time()
        
        if agora >= t_off:
            tarefa_offline_inteligente(driver)
            t_off = time.time() + (TEMPO_OFFLINE * 60)
            
        if agora >= t_frota:
            tarefa_status_frota(driver)
            t_frota = time.time() + (TEMPO_FROTA * 60)
            
        if agora >= t_corr:
            tarefa_corridas(driver)
            t_corr = time.time() + (TEMPO_CORRIDAS * 60)
            
        time.sleep(10)