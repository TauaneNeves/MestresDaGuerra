# app.py (VERSÃO COM FLUXO DE ESPERA CORRETO)

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import random
import string
import logging

# --- Configuração (sem mudanças) ---
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app = Flask(__name__)
socketio = SocketIO(app)
games = {}
player_to_game = {}
# Importando a classe Tabuleiro do outro arquivo
from jogo_logica import Tabuleiro

def generate_game_id():
    return "game_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))

# --- Funções de Lógica de Jogo (sem mudanças) ---
def get_board_state_for_player(game_state, jogador_id):
    # (Esta função permanece idêntica à versão anterior)
    tabuleiro = game_state['tabuleiro']
    vez = game_state['vez']
    jogadores = game_state['jogadores']
    grid_para_enviar = []
    for y, linha in enumerate(tabuleiro.grid):
        linha_para_enviar = []
        for x, peca in enumerate(linha):
            if peca is None:
                linha_para_enviar.append(None)
            elif peca == "LAGO":
                linha_para_enviar.append({"type": "lago"})
            else:
                info_peca = {"type": "peca", "jogador": peca.jogador, "nome": peca.nome}
                if peca.jogador != jogador_id:
                    info_peca["nome"] = "???"
                else:
                    info_peca["rank"] = peca.rank
                linha_para_enviar.append(info_peca)
        grid_para_enviar.append(linha_para_enviar)
    return {
        "grid": grid_para_enviar, "vez": vez, "num_jogadores": len(jogadores),
        "cor_turno_atual": "Vermelho" if vez == 1 else "Azul",
        "sua_cor": "Vermelho" if jogador_id == 1 else "Azul"
    }

# --- Rota Principal (sem mudanças) ---
@app.route('/')
def index():
    return render_template('index.html')

# --- Eventos do Socket.IO (COM MUDANÇAS IMPORTANTES) ---
@socketio.on('create_game')
def handle_create_game():
    sid = request.sid
    game_id = generate_game_id()
    games[game_id] = {
        'tabuleiro': Tabuleiro(), 'jogadores': {}, 'vez': 1
    }
    print(f"Jogo '{game_id}' criado por {sid}.")
    
    join_room(game_id)
    games[game_id]['jogadores'][sid] = 1
    player_to_game[sid] = game_id
    
    # MUDANÇA: Apenas confirma a criação para o criador. Não envia o tabuleiro ainda.
    emit('game_created', {'game_id': game_id, 'player_id': 1})

@socketio.on('join_game')
def handle_join_game(data):
    sid = request.sid
    game_id = data.get('game_id')
    game = games.get(game_id)

    if not game:
        emit('error_message', {'message': f"Jogo '{game_id}' não encontrado."})
        return
    if len(game['jogadores']) >= 2:
        emit('error_message', {'message': f"O jogo '{game_id}' já está cheio."})
        return

    join_room(game_id)
    game['jogadores'][sid] = 2
    player_to_game[sid] = game_id
    print(f"Jogador {sid} entrou no jogo '{game_id}'. O jogo vai começar.")
    
    # MUDANÇA: Agora que o segundo jogador entrou, envia o estado para AMBOS e inicia o jogo.
    # Usaremos um novo evento 'start_game' para ser mais claro.
    for player_sid, player_id in game['jogadores'].items():
        board_state = get_board_state_for_player(game, player_id)
        socketio.emit('start_game', {
            'game_id': game_id,
            'player_id': player_id,
            'initial_state': board_state
        }, to=player_sid)

# As funções handle_move_piece e handle_disconnect da versão anterior podem ser mantidas,
# mas precisam chamar a função correta para atualizar o estado.
def broadcast_game_state(game_id):
    game = games.get(game_id)
    if not game: return
    for sid, pid in game['jogadores'].items():
        board_state = get_board_state_for_player(game, pid)
        socketio.emit('update_board', board_state, to=sid)

@socketio.on('move_piece')
def handle_move_piece(data):
    # (Esta função pode ser mantida como na versão anterior, mas chamando broadcast_game_state no final)
    sid = request.sid
    game_id = player_to_game.get(sid)
    if not game_id: return
    game = games[game_id]
    player_id = game['jogadores'].get(sid)
    if player_id is None or player_id != game['vez'] or len(game['jogadores']) < 2: return
    
    de_coord_str, para_coord_str = data['de'], data['para']
    de_yx = (int(de_coord_str[1]), ord(de_coord_str[0]) - ord('A'))
    para_yx = (int(para_coord_str[1]), ord(para_coord_str[0]) - ord('A'))
    
    resultado = game['tabuleiro'].mover_peca(de_yx, para_yx, player_id)
    if "sucesso" in resultado or "Combate" in resultado or "FIM_DE_JOGO" in resultado:
        game['vez'] = 2 if game['vez'] == 1 else 1
    
    broadcast_game_state(game_id)
    
    if "FIM_DE_JOGO" in resultado:
        socketio.emit('game_over', {'message': f"Jogador {player_id} venceu!"}, to=game_id)

@socketio.on('disconnect')
def handle_disconnect():
    # (Esta função pode ser mantida como na versão anterior)
    sid = request.sid
    game_id = player_to_game.get(sid)
    if not game_id: return
    game = games.get(game_id)
    if not game: return
    
    player_id = game['jogadores'].pop(sid, None)
    if sid in player_to_game: del player_to_game[sid]
    
    print(f"Jogador {player_id} desconectou do jogo '{game_id}'.")
    
    if not game['jogadores']:
        games.pop(game_id, None)
    else:
        socketio.emit('opponent_left', {'message': 'Seu oponente desconectou.'}, to=game_id)
        broadcast_game_state(game_id)

if __name__ == '__main__':
    print("Servidor de jogos iniciado. Abra http://127.0.0.1:5000.")
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)