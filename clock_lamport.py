import socket
import json
from threading import Thread, Lock
from time import sleep


process_id = '1'
clock_speed = 1.0
local_time = 0
time_lock = Lock()  
sock = None

PORTS = {
    '1': 5001,
    '2': 5002,
    '3': 5003
}

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

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', PORTS[process_id]))
    print(f'\n[!] Processo {process_id} rodando na porta {PORTS[process_id]}')

def clock_running():
    
    global local_time
    while True:
        sleep(clock_speed)
        with time_lock:
            local_time += 1
            print(f'\r[CLOCK] Processo {process_id} - Tempo local: {local_time}   ')

def listen_network():
    while True:
        data, _ = sock.recvfrom(1024)
        msg_receive = json.loads(data.decode('utf-8'))
        receive_message(msg_receive)

def send_message(dest_id, text):
    global local_time
    with time_lock:
        local_time += 1
        
        msg_send = {
            'process_id': process_id,
            'local_time': local_time,
            'message': text
        }

        sock.sendto(json.dumps(msg_send).encode('utf-8'), ('127.0.0.1', PORTS[dest_id]))
        print(f'>>> Mensagem enviada para P{dest_id} | Tempo local: {local_time} | Conteúdo: "{text}"')

def receive_message(msg_receive):
    global local_time
    with time_lock:
        print(f"<<< local_time (antes de ajustar): {local_time}, msg_receive['local_time']: {msg_receive['local_time']}")
        local_time = max(local_time, msg_receive['local_time']) + 1
        
        print(f'<<< Mensagem recebida de P{msg_receive["process_id"]}: "{msg_receive["message"]}"')
        print(f'<<< Tempo local AJUSTADO para: {local_time}> ')
        

def main():
    initial_config()
    
    Thread(target=clock_running, daemon=True).start()
    Thread(target=listen_network, daemon=True).start()
    
    print("\n--- Sistema Pronto ---")
    while True:
        dest = input('\nPara qual processo deseja enviar? [1, 2, 3]: ')
        if dest in PORTS and dest != process_id:
            msg = input('Digite a mensagem: ')
            send_message(dest, msg)
        else:
            print("Destino inválido ou igual ao próprio processo.")

if __name__ == '__main__':
    main()