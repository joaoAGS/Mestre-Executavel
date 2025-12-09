import time
import os
import pyperclip
import requests
import subprocess
import sys
import urllib3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==============================================================================
# ⚙️ CONFIGURAÇÕES
# ==============================================================================

# --- AUTO-UPDATE ---
VERSAO_ATUAL = "1.9.3"  # <--- LEMBRE DE MUDAR ISSO QUANDO GERAR ATUALIZAÇÃO
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

# --- CONFIGURAÇÃO DE PASTA ROBUSTA ---
# Define onde o executável está rodando para não errar o caminho
if getattr(sys, 'frozen', False):
    diretorio_base = os.path.dirname(sys.executable)
    exe_atual = sys.executable
else:
    diretorio_base = os.path.dirname(os.path.abspath(__file__))
    exe_atual = os.path.abspath(__file__)

CAMINHO_PERFIL = os.path.join(diretorio_base, "perfil_chrome")

# ==============================================================================
# 🔄 FUNÇÃO DE ATUALIZAÇÃO (MODO SILENCIOSO E FORÇADO)
# ==============================================================================
def verificar_atualizacao():
    print(f"🔍 Verificando atualizações... (Versão Local: {VERSAO_ATUAL})")
    try:
        # TRUQUE ANTI-CACHE: Adiciona um número aleatório no final do link
        # Isso obriga a internet a baixar o arquivo fresco, sem usar memória antiga
        link_fresco = f"{URL_VERSAO}?v={int(time.time())}"
        
        resposta = requests.get(link_fresco, verify=False)
        versao_online = resposta.text.strip()
        
        # DEBUG: Mostra o que ele achou (para você ver se está lendo certo)
        print(f"🌐 Versão encontrada na internet: '{versao_online}'")
        
        if versao_online != VERSAO_ATUAL and versao_online != "":
            print(f"🚀 ATUALIZAÇÃO DETECTADA: {versao_online}! Baixando...")
            
            # Baixa o executável (também com anti-cache para garantir)
            link_exe_fresco = f"{URL_EXECUTAVEL}?v={int(time.time())}"
            resposta_exe = requests.get(link_exe_fresco, verify=False)
            
            nome_novo_caminho = os.path.join(diretorio_base, "Mestre_Novo.exe")
            
            with open(nome_novo_caminho, 'wb') as f:
                f.write(resposta_exe.content)
            
            print("✅ Download concluído! Reiniciando...")
            
            nome_exe_apenas = os.path.basename(exe_atual)
            
            bat_script = f"""
            @echo off
            @chcp 65001 >nul
            title Atualizando...
            cd /d "{diretorio_base}"
            echo Aguardando fechamento...
            timeout /t 3 /nobreak >nul
            :TENTAR_MOVER
            move /y "Mestre_Novo.exe" "{nome_exe_apenas}"
            if errorlevel 1 (
                timeout /t 1 /nobreak >nul
                goto TENTAR_MOVER
            )
            start "" "{nome_exe_apenas}"
            start /b "" cmd /c del "%~f0"&exit /b
            """
            
            bat_path = os.path.join(diretorio_base, "atualizador.bat")
            with open(bat_path, "w", encoding="utf-8") as bat:
                bat.write(bat_script)
                
            subprocess.Popen(bat_path, shell=True)
            time.sleep(1)
            sys.exit()
            
        else:
            print("✅ Nenhuma atualização necessária.")
            
    except Exception as e:
        print(f"⚠️ Erro ao verificar: {e}")
        time.sleep(2)
# ==============================================================================
# 🛠️ FUNÇÕES DE SUPORTE
# ==============================================================================

def iniciar_driver():
    print("🚀 Iniciando Robô Mestre")
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-data-dir={CAMINHO_PERFIL}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # Busca Chrome em locais padrões
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
        # Se cair a conexão, tenta voltar
        try:
            if "WhatsApp" not in driver.title:
                driver.get(URL_WHATSAPP)
                time.sleep(15)
        except:
            driver.get(URL_WHATSAPP)
            time.sleep(15)

        wait = WebDriverWait(driver, 40)
        
        # Busca Contato
        try:
            box = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')))
            box.click()
            box.send_keys(Keys.CONTROL + "a")
            box.send_keys(Keys.BACKSPACE)
            box.send_keys(destinatario)
            time.sleep(2)
            box.send_keys(Keys.ENTER)
        except:
            print(f"❌ '{destinatario}' não encontrado.")
            return

        # Envia Texto
        chat = wait.until(EC.presence_of_element_located((By.XPATH, '//footer//div[@contenteditable="true"]')))
        chat.click()
        time.sleep(1)
        pyperclip.copy(mensagem)
        chat.send_keys(Keys.CONTROL, 'v')
        time.sleep(1)
        
        # Clica no botão enviar ou Enter
        try:
            btn = driver.find_element(By.XPATH, "//span[@data-icon='send']")
            driver.execute_script("arguments[0].click();", btn)
        except:
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
    
    # 1. VERIFICA ATUALIZAÇÃO (Só se for .exe para evitar bagunça no teste)
    if getattr(sys, 'frozen', False):
        verificar_atualizacao()

    # 2. CONFIGURA PASTA E MATA CHROME ANTIGO
    if not os.path.exists(CAMINHO_PERFIL):
        os.makedirs(CAMINHO_PERFIL)
    os.system("taskkill /F /IM chrome.exe /T >nul 2>&1")
    
    # 3. INICIA TUDO
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

    # Agendamento
    t_off = 0
    t_frota = 0
    t_corr = 0
    
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