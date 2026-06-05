import socket
import json
import matplotlib.pyplot as plt

# Configuração do Socket do Observer
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('127.0.0.1', 5000))
sock.settimeout(0.1) 

print("Observador de Lamport Iniciado na porta 5000...")
print("Aguardando eventos da rede...")

# Dicionários para guardar os dados
eventos_send = {}    
eventos_receive = {} 
eventos_interno = {} # <--- NOVO: Guarda os eventos internos

# Configuração do Gráfico
plt.ion()
fig, ax = plt.subplots(figsize=(10, 5))
fig.canvas.manager.set_window_title('Diagrama de Espaço-Tempo (Lamport)')

def desenhar_grafico():
    ax.clear()
    
    # Desenha as linhas horizontais
    ax.axhline(3, color='green', linestyle='-', alpha=0.3)
    ax.text(0, 3.1, 'Processo 3', color='green', fontweight='bold')
    
    ax.axhline(2, color='red', linestyle='-', alpha=0.3)
    ax.text(0, 2.1, 'Processo 2', color='red', fontweight='bold')
    
    ax.axhline(1, color='blue', linestyle='-', alpha=0.3)
    ax.text(0, 1.1, 'Processo 1', color='blue', fontweight='bold')

    # 1. Plota os eventos internos (Bolinha Azul)
    for msg_id, int_data in eventos_interno.items():
        x_int, y_int = int_data['tempo'], int_data['p_origem']
        ax.plot(x_int, y_int, 'bo') # 'bo' = bolinha azul
        ax.text(x_int, y_int - 0.25, str(x_int), ha='center', color='blue', fontweight='bold')

    # 2. Plota os envios e recebimentos (Bolinha Preta com Seta)
    for msg_id, send_data in eventos_send.items():
        x_send, y_send = send_data['tempo'], send_data['p_origem']
        
        ax.plot(x_send, y_send, 'ko') 
        ax.text(x_send, y_send - 0.25, str(x_send), ha='center') 
        
        if msg_id in eventos_receive:
            recv_data = eventos_receive[msg_id]
            x_recv, y_recv = recv_data['tempo'], recv_data['p_destino']
            tempo_anterior = recv_data.get('tempo_anterior') 
            
            ax.plot(x_recv, y_recv, 'ko')
            
            if tempo_anterior is not None and tempo_anterior != x_recv:
                texto_tempo = f"{tempo_anterior} ➔ {x_recv}"
                ax.text(x_recv, y_recv - 0.25, texto_tempo, ha='center', color='purple', fontweight='bold')
            else:
                ax.text(x_recv, y_recv - 0.25, str(x_recv), ha='center')
            
            ax.annotate('', xy=(x_recv, y_recv), xytext=(x_send, y_send),
                        arrowprops=dict(arrowstyle="->", color='black', lw=1.5))

    ax.set_yticks([1, 2, 3])
    ax.set_yticklabels(['P1', 'P2', 'P3'])
    ax.set_xlabel('Tempo Lógico de Lamport')
    
    # Ajusta o tamanho da tela baseado no maior tempo
    todos_tempos = (
        [e['tempo'] for e in eventos_send.values()] + 
        [e['tempo'] for e in eventos_receive.values()] +
        [e['tempo'] for e in eventos_interno.values()]
    )
    max_tempo = max(todos_tempos) + 5 if todos_tempos else 10
        
    ax.set_xlim(0, max_tempo)
    ax.set_ylim(0.5, 3.5)
    plt.draw()

# Loop principal do Observer
while True:
    try:
        data, _ = sock.recvfrom(1024)
        log = json.loads(data.decode('utf-8'))
        
        # Filtra o tipo de evento que chegou
        if log['tipo'] == 'SEND':
            eventos_send[log['msg_id']] = log
        elif log['tipo'] == 'RECEIVE':
            eventos_receive[log['msg_id']] = log
        elif log['tipo'] == 'INTERNAL':
            eventos_interno[log['msg_id']] = log # Registra o evento interno!
            
        desenhar_grafico()
        
    except socket.timeout:
        plt.pause(0.01)