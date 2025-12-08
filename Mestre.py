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

#teste de commit
# ==============================================================================
# 🔄 SISTEMA DE AUTO-UPDATE
# ==============================================================================
VERSAO_ATUAL = "1.2"
URL_VERSAO = "https://raw.githubusercontent.com/joaoAGS/Mestre-Executavel/refs/heads/main/versao.txt"
URL_EXECUTAVEL = "https://github.com/joaoAGS/Mestre-Executavel/raw/refs/heads/main/Mestre.exe"


# ==============================================================================
# ⚙️ CONFIGURAÇÕES E VERIAVEIS GLOBAIS
# ==============================================================================

VERSAO_ATUAL = "1.2"
URL_VERSAO = "https://raw.githubusercontent.com/joaoAGS/Mestre-Executavel/refs/heads/main/versao.txt"
URL_EXECUTAVEL = "https://github.com/joaoAGS/Mestre-Executavel/raw/refs/heads/main/Mestre.exe"


URL_DASHBOARD = "https://paineladmin3.azurewebsites.net/mobfy/dashboard"
URL_MAPA = "https://paineladmin3.azurewebsites.net/mobfy/vermapa"
URL_WHATSAPP = "https://web.whatsapp.com"

# --- NOMES DO WHATSAPP (Edite aqui) ---
NOME_GRUPO_WHATSAPP = "MOBFY Avisos CAÇADOR"    # Para alertas de Offline e Frota

# --- LISTA DE QUEM RECEBE O RELATÓRIO DE CORRIDAS ---
# Adicione ou remova nomes entre aspas, separados por vírgula
LISTA_CORRIDAS = ["Matheus Wichmann", "Mobfy Canal"]

# --- INTERVALOS (Minutos) ---
TEMPO_OFFLINE = 3      # Verifica offline (Aba 2)
TEMPO_FROTA = 15        # Relatório geral de cores (Aba 1)
TEMPO_CORRIDAS = 30    # Relatório dashboard (Aba 0)

# Se estiver rodando como .exe, usa o caminho do executável. Se for script, usa o local do arquivo.
if getattr(sys, 'frozen', False):
    diretorio_base = os.path.dirname(sys.executable)
else:
    diretorio_base = os.path.dirname(os.path.abspath(__file__))

CAMINHO_PERFIL = os.path.join(diretorio_base, "perfil_chrome")

# ==============================================================================
# 🛠️ FUNÇÕES DE SUPORTE
# ==============================================================================
def verificar_atualizacao():
    print(f"🔍 Verificando atualizações... (Versão {VERSAO_ATUAL})")
    try:
        # 1. Pega a versão online
        resposta = requests.get(URL_VERSAO)
        versao_online = resposta.text.strip()
        
        # 2. Compara (Se a online for maior ou diferente)
        if versao_online != VERSAO_ATUAL:
            print(f"🚀 Nova versão encontrada: {versao_online}! Baixando...")
            
            # 3. Baixa o novo executável
            resposta_exe = requests.get(URL_EXECUTAVEL)
            
            # Nome do arquivo atual e do novo
            nome_atual = sys.argv[0]
            nome_novo = "Mestre_Novo.exe"
            
            # 4. Salva o novo .exe
            with open(nome_novo, 'wb') as f:
                f.write(resposta_exe.content)
            
            print("✅ Download concluído! Instalando...")
            
            # 5. TRUQUE DE MESTRE: Script .bat para trocar os arquivos
            # O Windows não deixa deletar o .exe enquanto ele roda.
            # Então criamos um script que espera o robô fechar, troca os arquivos e reabre.
            
            bat_script = f"""
            @echo off
            timeout /t 2 >nul
            del "{nome_atual}"
            ren "{nome_novo}" "{os.path.basename(nome_atual)}"
            start "" "{nome_atual}"
            del "%~f0"
            """
            
            with open("atualizador.bat", "w") as bat:
                bat.write(bat_script)
                
            # Executa o .bat e fecha o robô atual
            subprocess.Popen("atualizador.bat", shell=True)
            sys.exit()
            
        else:
            print("✅ Seu robô está atualizado.")
            
    except Exception as e:
        print(f"⚠️ Erro ao verificar atualização: {e}")
        # Continua o robô normalmente se der erro na internet
        
def iniciar_driver():
    print("🚀 Iniciando Robô Mestre (Com Cálculo de Perdas)...")
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-data-dir={CAMINHO_PERFIL}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def enviar_whatsapp(driver, mensagem, destinatario):
    """
    Envia mensagem para um destinatário específico (Grupo ou Pessoa).
    """
    try:
        print(f"💬 Preparando envio para: {destinatario}...")
        driver.switch_to.window(driver.window_handles[3]) # ABA 3
        
        if "WhatsApp" not in driver.title:
            print("⚠️ Recarregando WhatsApp...")
            driver.get(URL_WHATSAPP)
            time.sleep(10)

        wait = WebDriverWait(driver, 40)
        
        # Busca Contato
        try:
            xpath_search = '//div[@contenteditable="true"][@data-tab="3"]'
            search_box = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_search)))
            search_box.click()
            search_box.send_keys(Keys.CONTROL + "a")
            search_box.send_keys(Keys.BACKSPACE)
            search_box.send_keys(destinatario)
            time.sleep(2)
            search_box.send_keys(Keys.ENTER)
        except:
            print(f"❌ Destinatário '{destinatario}' não encontrado.")
            return

        # Envia Mensagem
        xpath_campo = '//footer//div[@contenteditable="true"]'
        campo = wait.until(EC.presence_of_element_located((By.XPATH, xpath_campo)))
        campo.click()
        time.sleep(1)
        
        pyperclip.copy(mensagem)
        campo.send_keys(Keys.CONTROL, 'v')
        time.sleep(1)
        
        try:
            btn = driver.find_element(By.XPATH, "//span[@data-icon='send']")
            driver.execute_script("arguments[0].click();", btn)
        except:
            campo.send_keys(Keys.ENTER)
            
        print(f"✅ Mensagem enviada para {destinatario}!")
        time.sleep(3)
        
    except Exception as e:
        print(f"❌ Erro envio Zap ({destinatario}): {e}")

def ler_texto_painel(driver, xpath):
    try:
        el = driver.find_element(By.XPATH, xpath)
        return el.text if el.text else el.get_attribute("textContent")
    except:
        return "0"

def filtrar_dados_offline(texto):
    if not texto: return "Dados ilegíveis"
    nome, celular = "Não identificado", "Não informado"
    for linha in texto.split('\n'):
        linha = linha.strip()
        if "Nome:" in linha: nome = linha.replace("Nome:", "").strip()
        elif "Motorista:" in linha: nome = linha.replace("Motorista:", "").strip()
        if "Celular:" in linha: celular = linha.replace("Celular:", "").strip()
        elif "Telefone:" in linha: celular = linha.replace("Telefone:", "").strip()
    return f"🚫 Nome: {nome}\nCelular: {celular}"

# ==============================================================================
# 1️⃣ TAREFA: OFFLINE INTELIGENTE (1 a 15 = Lista / 16+ = Alerta Geral)
# ==============================================================================
def tarefa_offline_inteligente(driver):
    print("\n🔍 [OFFLINE] Buscando pinos amarelos...")
    try:
        driver.switch_to.window(driver.window_handles[2]) # ABA 2
        if driver.current_url != URL_MAPA:
            driver.get(URL_MAPA)
        else:
            driver.refresh()
        
        time.sleep(15)

        amarelos = driver.find_elements(By.CSS_SELECTOR, "img[src*='pin-amarelo.png']")
        qtd_offline = len(amarelos)
        
        # CASO 0: Ninguém offline
        if qtd_offline == 0:
            print("✅ [OFFLINE] Tudo normal.")
            return

        # CASO CRÍTICO: 16 ou mais offline (Provável queda de rede)
        if qtd_offline >= 16:
            print(f"⚠️ [CRÍTICO] {qtd_offline} offlines! Enviando alerta de rede...")
            mensagem = (
                f"🚨 *ALERTA CRÍTICO: INSTABILIDADE NA REDE* 🚨\n\n"
                f"⚠️ Foram detectados *{qtd_offline} motoristas offline* simultaneamente.\n\n"
                f"📢 *AÇÃO IMEDIATA:*\n"
                f"Por favor, solicitem que *TODOS* os motoristas reiniciem seus aparelhos celulares e verifiquem a conexão de dados."
            )
            enviar_whatsapp(driver, mensagem, NOME_GRUPO_WHATSAPP)
            return

        # CASO PADRÃO: Entre 1 e 15 (Lista individual)
        print(f"⚠️ [OFFLINE] {qtd_offline} detectados. Listando até 15...")
        lista_final = []

        # Loop vai até 15
        for i, pino in enumerate(amarelos[:15]):
            try:
                driver.execute_script("arguments[0].click();", pino)
                time.sleep(1.5)
                
                xpath_info = '//*[@id="map"]/div/div[3]/div[1]/div[2]/div/div[4]'
                try:
                    elem = driver.find_element(By.XPATH, xpath_info)
                    texto = elem.text if elem.text else elem.get_attribute("textContent")
                    lista_final.append(filtrar_dados_offline(texto))
                except:
                    # Tenta pegar pelo título se falhar
                    try:
                        tit = driver.find_element(By.CLASS_NAME, "infowindow-title").text
                        lista_final.append(f"🚫 {tit} (Sem telefone)")
                    except:
                        lista_final.append("Erro na leitura")
                
                driver.find_element(By.TAG_NAME, 'body').click()
                time.sleep(0.5)
            except:
                continue

        if lista_final:
            texto_zap = "\n\n".join(lista_final)
            mensagem = (
                f"⚠️ *ALERTA: MOTORISTAS ONLINE SEM INTERNET - {time.strftime('%H:%M')}*\n\n"
                f"Total Detectado: {qtd_offline}\n\n"
                f"{texto_zap}"
            )
            enviar_whatsapp(driver, mensagem, NOME_GRUPO_WHATSAPP)

    except Exception as e:
        print(f"❌ Erro Offline: {e}")

# ==============================================================================
# 2️⃣ TAREFA: STATUS DA FROTA (5 min) - ABA 1
# ==============================================================================
def tarefa_status_frota(driver):
    print("\n🚗 [FROTA] Contando geral...")
    try:
        driver.switch_to.window(driver.window_handles[1]) # ABA 1
        if driver.current_url != URL_MAPA:
            driver.get(URL_MAPA)
        else:
            driver.refresh()
        
        time.sleep(15)

        livres = len(driver.find_elements(By.CSS_SELECTOR, "img[src*='verde']"))
        em_corrida = len(driver.find_elements(By.CSS_SELECTOR, "img[src*='vermelho']")) + \
                     len(driver.find_elements(By.CSS_SELECTOR, "img[src*='ocupado']"))
        offline = len(driver.find_elements(By.CSS_SELECTOR, "img[src*='amarelo']"))
        
        total = livres + em_corrida + offline

        msg = (
            f"🚗 Status da Frota - {time.strftime('%H:%M')}\n"
            f"🟢 Livres: {livres}\n"
            f"🔴 Em Corrida: {em_corrida}\n"
            f"⚠️ Online sem internet: {offline}\n"
            f"📊 Total: {total}"
        )
        enviar_whatsapp(driver, msg, NOME_GRUPO_WHATSAPP)

    except Exception as e:
        print(f"❌ Erro Frota: {e}")

# ==============================================================================
# 3️⃣ TAREFA: CORRIDAS (30 min) - ABA 0 - DIRETO PARA LISTA VIP
# ==============================================================================
def tarefa_corridas(driver):
    print("\n📊 [DASHBOARD] Coletando estatísticas e calculando perdas...")
    try:
        driver.switch_to.window(driver.window_handles[0]) # ABA 0
        if driver.current_url != URL_DASHBOARD:
            driver.get(URL_DASHBOARD)
        else:
            driver.refresh()
        
        time.sleep(15)

        xp_sim = '/html/body/div/app/div/div/div[2]/div[1]/div/div[1]/h3'
        xp_sol = '/html/body/div/app/div/div/div[2]/div[2]/div/div[1]/h3'
        xp_con = '/html/body/div/app/div/div/div[2]/div[3]/div/div[1]/h3'
        xp_por = '/html/body/div/app/div/div/div[2]/div[4]/div/div[1]/h3'

        # LEITURA DOS DADOS (Texto puro)
        txt_sim = ler_texto_painel(driver, xp_sim)
        txt_sol = ler_texto_painel(driver, xp_sol)
        txt_con = ler_texto_painel(driver, xp_con)
        txt_por = ler_texto_painel(driver, xp_por)

        # CÁLCULO DE CORRIDAS PERDIDAS (Solicitações - Concluídas)
        try:
            # Removemos pontos caso o número seja milhar (ex: 1.500 vira 1500)
            num_sol = int(txt_sol.replace('.', ''))
            num_con = int(txt_con.replace('.', ''))
            
            calculo_perdidas = num_sol - num_con
        except:
            calculo_perdidas = "?" # Retorna ? se houver erro na conversão

        msg = (
            f"*📊 Relatório de Corridas - {time.strftime('%H:%M')}*\n"
            f"📅 _Atualização a cada 30min_\n\n"
            f"🔢 *Simulações:* {txt_sim}\n"
            f"📩 *Solicitações:* {txt_sol}\n"
            f"✅ *Concluídas:* {txt_con}\n"
            f"❌ *Perdidas/Canc:* {calculo_perdidas}\n"
            f"📈 *Conversão:* {txt_por}"
        )
        
        # LOOP PARA ENVIAR PARA TODOS DA LISTA
        print(f"📤 Enviando relatório para {len(LISTA_CORRIDAS)} destinatários...")
        for destinatario in LISTA_CORRIDAS:
            enviar_whatsapp(driver, msg, destinatario)
            time.sleep(2) # Pequena pausa entre envios

    except Exception as e:
        print(f"❌ Erro Corridas: {e}")

# ==============================================================================
# 🔄 LOOP PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    
    verificar_atualizacao()
    
    if not os.path.exists(CAMINHO_PERFIL):
        os.makedirs(CAMINHO_PERFIL)
        
    os.system("taskkill /F /IM chrome.exe /T >nul 2>&1")
    
    driver = iniciar_driver()
    
    print("\n🛠️  ABRINDO AS 4 ABAS...")
    driver.get(URL_DASHBOARD)
    
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get(URL_MAPA)
    
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[2])
    driver.get(URL_MAPA)
    
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[3])
    driver.get(URL_WHATSAPP)
    
    print("\n" + "="*60)
    print("⏳ 60 SEGUNDOS PARA LOGIN!")
    print("="*60 + "\n")
    
    time.sleep(60)
    
    print("🤖 MONITORAMENTO INTELIGENTE INICIADO.")

    proximo_offline = 0
    proximo_frota = 0
    proximo_corridas = 0
    
    while True:
        agora = time.time()
        
        # --- OFFLINE (3 min) ---
        if agora >= proximo_offline:
            tarefa_offline_inteligente(driver)
            proximo_offline = time.time() + (TEMPO_OFFLINE * 60)
            
        # --- FROTA (5 min) ---
        agora = time.time()
        if agora >= proximo_frota:
            tarefa_status_frota(driver)
            proximo_frota = time.time() + (TEMPO_FROTA * 60)
            
        # --- CORRIDAS (30 min) ---
        agora = time.time()
        if agora >= proximo_corridas:
            tarefa_corridas(driver)
            proximo_corridas = time.time() + (TEMPO_CORRIDAS * 60)
            
        time.sleep(10)