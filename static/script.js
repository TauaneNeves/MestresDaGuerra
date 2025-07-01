// static/script.js (VERSÃO FINAL COM LÓGICA DE JOGADOR CORRETA)
document.addEventListener('DOMContentLoaded', () => {
    const socket = io();

    // Elementos da UI
    const landingScreen = document.getElementById('landing-screen');
    const gameScreen = document.getElementById('game-screen');
    const welcomeState = document.getElementById('welcome-state');
    const waitingState = document.getElementById('waiting-state');
    const createGameBtn = document.getElementById('create-game-btn');
    const joinGameBtn = document.getElementById('join-game-btn');
    const waitingCopyIcon = document.getElementById('waiting-copy-icon');
    const boardElement = document.getElementById('game-board');
    const gameIdEl = document.getElementById('game-id');
    const waitingGameIdEl = document.getElementById('waiting-game-id');
    const playerColorEl = document.getElementById('player-color');
    const turnColorEl = document.getElementById('turn-color');
    const qgMessageEl = document.getElementById('qg-message');
    
    // Variáveis de estado do cliente
    let myPlayerId = null;
    let selectedCell = null;

    // Funções de UI
    function showWaitingScreen(gameId) {
        welcomeState.classList.add('hidden');
        waitingState.classList.remove('hidden');
        waitingGameIdEl.textContent = gameId;
    }

    function showGameScreen(gameId) {
        landingScreen.classList.add('hidden');
        gameScreen.classList.remove('hidden');
        gameIdEl.textContent = gameId;
    }

    // Ícones para as peças (pode customizar)
    const rankToIcons = {
        10: '<i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i>',
        9: '<i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i>',
        8: '<i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i>',
        7: '<i class="fa-solid fa-star"></i>',
    };
    const nameToIcon = {
        'bomba': '<i class="fa-solid fa-bomb"></i>',
        'bandeira': '<i class="fa-solid fa-flag"></i>',
        'espiao': '<i class="fa-solid fa-user-secret"></i>'
    };
    
    // Função principal para desenhar o tabuleiro
    const createBoard = (boardState) => {
        boardElement.innerHTML = '';
        const grid = boardState.grid;

        // Atualiza o painel de status
        playerColorEl.textContent = boardState.sua_cor;
        playerColorEl.style.color = boardState.sua_cor === 'Vermelho' ? '#d63031' : '#0984e3';
        turnColorEl.textContent = boardState.cor_turno_atual;
        turnColorEl.style.color = boardState.cor_turno_atual === 'Vermelho' ? '#d63031' : '#0984e3';
        
        if (boardState.num_jogadores < 2) {
             qgMessageEl.textContent = 'Oponente desconectou.';
        } else {
            if (boardState.vez === myPlayerId) qgMessageEl.textContent = 'Sua vez de jogar.';
            else qgMessageEl.textContent = 'Aguardando jogada do oponente.';
        }

        // Itera por cada célula do grid recebido do servidor
        grid.forEach((row, y) => {
            row.forEach((peca, x) => {
                const cell = document.createElement('div');
                cell.classList.add('cell');
                cell.dataset.coord = `${String.fromCharCode(65 + x)}${y}`;

                if (peca) { // Se a célula não está vazia
                    if (peca.type === 'lago') {
                        cell.classList.add('lake');
                    } else { // Se for uma peça
                        const pieceEl = document.createElement('div');
                        pieceEl.classList.add('piece');
                        
                        // CORREÇÃO IMPORTANTE: Pinta a peça com a cor do seu dono (peca.jogador)
                        pieceEl.classList.add(`piece-p${peca.jogador}`);
                        
                        // CORREÇÃO IMPORTANTE: Verifica se a peça é minha ou do oponente
                        if (peca.jogador === myPlayerId) {
                            // É minha peça: mostro os detalhes
                            const iconHtml = nameToIcon[peca.nome] || rankToIcons[peca.rank] || peca.rank;
                            pieceEl.innerHTML = `<div class="rank-icons">${iconHtml || ''}</div><div class="piece-name">${peca.nome}</div>`;
                        } else {
                            // É do oponente: mostro escondida
                            pieceEl.classList.add('piece-hidden');
                            pieceEl.innerHTML = '?';
                        }
                        cell.appendChild(pieceEl);
                    }
                }
                cell.addEventListener('click', () => onCellClick(cell));
                boardElement.appendChild(cell);
            });
        });
    };
    
    const onCellClick = (cell) => {
        // Se não for minha vez, não faço nada
        if (boardElement.innerHTML.includes("Aguardando jogada")) return;
        
        if (selectedCell) { // Se já tenho uma peça selecionada (este é o segundo clique)
            const de = selectedCell.dataset.coord;
            const para = cell.dataset.coord;

            // Envia o movimento para o servidor
            if (de !== para) {
                socket.emit('move_piece', { de, para });
            }

            // Limpa a seleção
            selectedCell.classList.remove('selected');
            selectedCell = null;
        } else { // Se não tenho peça selecionada (este é o primeiro clique)
            // CORREÇÃO IMPORTANTE: Verifica se a célula clicada contém uma peça MINHA
            if (cell.querySelector(`.piece-p${myPlayerId}`) && !cell.querySelector('.piece-hidden')) {
                selectedCell = cell;
                cell.classList.add('selected');
            }
        }
    };
    
    // --- Lógica de Conexão e Eventos ---
    createGameBtn.addEventListener('click', () => socket.emit('create_game'));
    joinGameBtn.addEventListener('click', () => {
        const gameId = prompt("Digite o ID do jogo para entrar:");
        if (gameId) socket.emit('join_game', { game_id: gameId });
    });
    waitingCopyIcon.addEventListener('click', () => {
        navigator.clipboard.writeText(waitingGameIdEl.textContent).then(() => alert('ID copiado!'));
    });

    socket.on('game_created', (data) => {
        myPlayerId = data.player_id;
        showWaitingScreen(data.game_id);
    });

    socket.on('start_game', (data) => {
        myPlayerId = data.player_id;
        showGameScreen(data.game_id);
        createBoard(data.initial_state);
    });
    
    socket.on('update_board', createBoard);
    socket.on('error_message', (data) => alert(`Erro: ${data.message}`));
    socket.on('opponent_left', (data) => alert(data.message));
});