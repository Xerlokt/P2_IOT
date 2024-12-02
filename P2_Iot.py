from machine import ADC, Pin, RTC, SoftI2C
from time import sleep, time
import ssd1306
import dht
import network
import ntptime
import urequests as requests

# Configuração de Wi-Fi
SSID = 'Wokwi-GUEST'
PASSWORD = ''
TIMEZONE_OFFSET = -3  # UTC-3 para São Paulo

# Inicialização do RTC
rtc = RTC()

led1 = Pin(13,Pin.OUT) 

led2 = Pin(14,Pin.OUT) 


# Configuração de sensores e atuadores
sensor_dht = dht.DHT22(Pin(32))
ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB)
ldr.width(ADC.WIDTH_10BIT)

# Configuração do display OLED
i2c = SoftI2C(scl=Pin(22), sda=Pin(23))
oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

# Configuração de botões
botaoZap = Pin(35, Pin.IN, Pin.PULL_DOWN)  # Botão para enviar WhatsApp
botao = Pin(12, Pin.IN, Pin.PULL_DOWN)  # Botão para exibir no terminal

# Configuração da API do WhatsApp
PHONE_NUMBER = 'PhoneNumber'  # Número no formato internacional
API_KEY = 'APIKEY'         # Chave de API CallMeBot

# Último envio pelo WhatsApp
ultimo_envio = 0

# Conexão Wi-Fi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print("Conectando ao Wi-Fi...")
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        sleep(1)
    print("Conectado ao Wi-Fi")
    print("IP:", wlan.ifconfig()[0])
    return wlan

# Sincronização do horário
def sincronizar_relogio():
    try:
        ntptime.host = 'pool.ntp.org'
        ntptime.settime()
        print("RTC sincronizado com sucesso")
    except Exception as e:
        print("Falha ao sincronizar o RTC:", e)

# Obter horário local ajustado
def obter_horario_local():
    tm = rtc.datetime()
    hora_local = (tm[4] + TIMEZONE_OFFSET) % 24
    if hora_local < 0:
        hora_local += 24
    data_hora = "{:02d}/{:02d}/{:04d} {:02d}:{:02d}:{:02d}".format(
        tm[2], tm[1], tm[0], hora_local, tm[5], tm[6])
    return data_hora

# Atualização do OLED
def atualizar_oled(temperatura, ldr_valor, data_hora, ip):
    try:
        oled.fill(0)
        oled.text("Sensores:", 0, 0)
        oled.text(f"Temp: {temperatura:.1f} C", 0, 10)
        oled.text(f"Luz: {ldr_valor}", 0, 20)
        oled.text("Horario:", 0, 30)
        oled.text(data_hora, 0, 40)
        oled.text(f"IP: {ip}", 0, 50)
        oled.show()
    except Exception as e:
        print(f"Erro ao atualizar OLED: {e}")

# Função para exibir mensagem temporária no OLED
def exibir_mensagem_oled(mensagem):
    try:
        oled.fill(0)
        oled.text(mensagem, 0, 30)  # Mensagem centralizada na altura
        oled.show()
        sleep(3)  # Exibir mensagem por 3 segundos
    except Exception as e:
        print(f"Erro ao exibir mensagem no OLED: {e}")

# Leitura dos sensores
def ler_sensores():
    sensor_dht.measure()
    temperatura = sensor_dht.temperature()
    luz = ldr.read()
    return temperatura, luz

# Enviar mensagem via WhatsApp e exibir status no OLED
def enviar_mensagem_whatsapp(temperatura, luz):
    global ultimo_envio
    if time() - ultimo_envio < 10:  # Limite de 10 segundos entre envios
        print("Aguarde antes de enviar outra mensagem.")
        exibir_mensagem_oled("Aguarde envio!")
        return
    ultimo_envio = time()

    message = f"Temperatura%3A%20{temperatura:.1f}%20C%0ALuz%3A%20{luz}"
    url = f'https://api.callmebot.com/whatsapp.php?phone={PHONE_NUMBER}&text={message}&apikey={API_KEY}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Mensagem enviada com sucesso!")
            exibir_mensagem_oled("Mensagem enviada!")
        else:
            print(f"Erro ao enviar mensagem: {response.text}")
            exibir_mensagem_oled("Erro ao enviar!")
    except Exception as e:
        print(f"Erro na requisição: {e}")
        exibir_mensagem_oled("Erro de conexão!")

# Programa principal
def main():
    wlan = connect_wifi()
    sincronizar_relogio()

    print("Pressione o botão para exibir os valores no terminal ou enviar via WhatsApp.")

    while True:
        temperatura, ldr_valor = ler_sensores()
        data_hora = obter_horario_local()
        ip = wlan.ifconfig()[0]

        atualizar_oled(temperatura, ldr_valor, data_hora, ip)

        if botao.value() == 1:
            print("\n[Botão Pressionado]")
            print(f"Temperatura: {temperatura:.1f} °C")
            print(f"Luz (LDR): {ldr_valor}")

            if (temperatura < 40):  # Corrigido o nome da variável
                led1.on() 
                sleep(1) 
                led1.off() 

            if (ldr_valor > 250):  # Indentação corrigida
                led2.on() 
                sleep(1) 
                led2.off() 



        if botaoZap.value() == 1:
            print("\n[Botão WhatsApp Pressionado]")
            enviar_mensagem_whatsapp(temperatura, ldr_valor)

        sleep(0.1)  # Reduz o tempo para melhorar resposta ao botão

if __name__ == "__main__":
    main()
