import socket
import json
from threading import Thread, Lock
from time import sleep


process_id = '1'
clock_speed = 1.0
local_time = 0
OBSERVER_PORT = 5000
msg_counter = 0
time_lock = Lock()  
debug = True
sock = None

PORTS = {
    '1': 5001,
    '2': 5002,
    '3': 5003
}

# realiza o setup inicial perguntando qual o id do processo
def initial_config():
    global process_id, clock_speed, sock
    
    process_id = input('Digite o ID do processo [1, 2, 3]: ')
    while process_id not in PORTS:
        print('Valor inválido!')
        process_id = input('Digite o ID do processo [1, 2, 3]: ')
    
    cs = input('Digite a velocidade do clock em segundos (ex: 1, 1.5, 2): ')
    
    while not cs.replace('.', '', 1).isdigit():
        print('Valor inválido!')
        cs = input('Digite a velocidade do clock em segundos: ')
    clock_speed = float(cs)
    
    # cria o socket do processo
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', PORTS[process_id]))
    print(f'\n[!] Processo {process_id} rodando na porta {PORTS[process_id]}')


# Função para rodar o relógio local
def add_event():
    global local_time, msg_counter
    with time_lock:
        local_time += clock_speed
        msg_counter += 1 # Contador de eventos sempre +1
        
        msg_id = f"{process_id}_int_{msg_counter}" # ID especial para evento interno
        debug_print(f'\r[CLOCK] Processo {process_id} - Evento Interno | Tempo local: {local_time}   ')
        
        # Avisa o observer que rolou um evento interno!
        notificar_observer('INTERNAL', local_time, msg_id, process_id, process_id)

 
# Função para escutar a rede e receber mensagens
# esta roda dentro de uma thread separada para nao travar o relogio local
def listen_network():
    while True:
        data, _ = sock.recvfrom(1024)
        msg_receive = json.loads(data.decode('utf-8'))
        receive_message(msg_receive)


# Função para enviar mensagens para outros processos
def send_message(dest_id, text):
    global local_time, msg_counter
    with time_lock: # usa o lock do tempo, para impedir 2 processos acessarem a mesma variavel ao mesmo tempo
        # incrementa 1 ao tempo local
        local_time += clock_speed
        msg_counter += 1 # counter para o serviço de visualização do relogio funcionando

        msg_id = f"{process_id}_{msg_counter}" # Cria um ID único (ex: '1_1')


        msg_send = {
            'process_id': process_id,
            'local_time': local_time,
            'message': text,
            'msg_id': msg_id # informação para o observer identificar a mensagem e desenhar a seta corretamente
        }

        # envia a mensagem para o processo de destino
        sock.sendto(json.dumps(msg_send).encode('utf-8'), ('127.0.0.1', PORTS[dest_id]))
        print(f'>>> Mensagem enviada para P{dest_id} | Tempo local: {local_time} | Conteúdo: "{text}"')
        
        # Avisa o observer que enviou
        notificar_observer('SEND', local_time, msg_id, process_id, dest_id)

def receive_message(msg_receive):
    global local_time
    with time_lock: # usa o lock do tempo, para impedir 2 processos acessarem a mesma variavel ao mesmo tempo
        tempo_antigo = local_time # salva o tempo local antigo 
        
        print(f"<<< local_time (antes de ajustar): {local_time}, msg_receive['local_time']: {msg_receive['local_time']}")
        # faz a comparação do tempo recebido com o local para verificar qual sera o tempo ajustado
        local_time = max(local_time, msg_receive['local_time']) + clock_speed
        
        print(f'<<< Mensagem recebida de P{msg_receive["process_id"]}: "{msg_receive["message"]}"')
        debug_print(f'<<< Tempo local AJUSTADO para: {local_time}> ')
        
        # envia para o observer as informações do recebimento -> tempos
        notificar_observer('RECEIVE', local_time, msg_receive['msg_id'], msg_receive["process_id"], process_id, tempo_antigo)




def notificar_observer(tipo, local_time, msg_id, remetente, destinatario, tempo_anterior=None):
    log = {
        'tipo': tipo,
        'tempo': local_time,
        'msg_id': msg_id,
        'p_origem': int(remetente),
        'p_destino': int(destinatario),
        'tempo_anterior': tempo_anterior
    }
    sock.sendto(json.dumps(log).encode('utf-8'), ('127.0.0.1', OBSERVER_PORT))


def debug_print(msg):
    if(debug):
        print(f'[DEBUG] {msg}')



def main():
    initial_config()
    
    Thread(target=listen_network, daemon=True).start()
    
    print("\n--- Sistema Pronto ---")
    while True:
        option_choiced = input(f'Digite a opção desejada:\n1. Enviar mensagem\n2. Sair\n3. Realizar um evento interno\nOpção: ')
        if option_choiced == '3':
            add_event()
        else:
            dest = input('\nPara qual processo deseja enviar? [1, 2, 3]: ')
            if dest in PORTS and dest != process_id:
                msg = input('Digite a mensagem: ')
                send_message(dest, msg)
            else:
                print("Destino inválido ou igual ao próprio processo.")

if __name__ == '__main__':
    main()