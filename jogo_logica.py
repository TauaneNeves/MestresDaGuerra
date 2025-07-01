# jogo_logica.py (CÓDIGO COMPLETO E CORRETO)
import random

PECAS_INFO = {
    'marechal': {'rank': 10, 'qty': 1}, 'general': {'rank': 9, 'qty': 1},
    'coronel': {'rank': 8, 'qty': 2}, 'major': {'rank': 7, 'qty': 3},
    'capitao': {'rank': 6, 'qty': 4}, 'tenente': {'rank': 5, 'qty': 4},
    'sargento': {'rank': 4, 'qty': 4}, 'cabo': {'rank': 3, 'qty': 5},
    'soldado': {'rank': 2, 'qty': 8}, 'espiao': {'rank': 1, 'qty': 1},
    'bomba': {'rank': 11, 'qty': 6},
    'bandeira': {'rank': 0, 'qty': 1}
}

class Peca:
    """Representa uma única peça no jogo."""
    def __init__(self, nome, rank, jogador):
        self.nome = nome
        self.rank = rank
        self.jogador = jogador

# A classe Tabuleiro PRECISA estar definida aqui para que o app.py a encontre.
class Tabuleiro:
    """Representa o tabuleiro e a lógica principal do jogo."""
    def __init__(self):
        self.grid = [[None for _ in range(10)] for _ in range(10)]
        self._configurar_zonas_proibidas()
        self._preparar_tabuleiro_inicial()

    def _configurar_zonas_proibidas(self):
        for y in [4, 5]:
            for x in [2, 3, 6, 7]:
                self.grid[y][x] = "LAGO"

    def _preparar_tabuleiro_inicial(self):
        # Jogador 1 (Vermelho)
        pecas_p1 = self._criar_conjunto_de_pecas(1)
        posicoes_p1 = [(y, x) for y in range(4) for x in range(10)]
        random.shuffle(posicoes_p1)
        for peca in pecas_p1:
            if not posicoes_p1: break
            y, x = posicoes_p1.pop()
            self.grid[y][x] = peca

        # Jogador 2 (Azul)
        pecas_p2 = self._criar_conjunto_de_pecas(2)
        posicoes_p2 = [(y, x) for y in range(6, 10) for x in range(10)]
        random.shuffle(posicoes_p2)
        for peca in pecas_p2:
            if not posicoes_p2: break
            y, x = posicoes_p2.pop()
            self.grid[y][x] = peca

    def _criar_conjunto_de_pecas(self, jogador_id):
        """Cria uma lista de objetos Peca para um jogador."""
        conjunto_pecas = []
        for nome, info in PECAS_INFO.items():
            for _ in range(info['qty']):
                conjunto_pecas.append(Peca(nome, info['rank'], jogador_id))
        return conjunto_pecas

    def mover_peca(self, de_yx, para_yx, jogador_id):
        # Lógica de movimento... (esta parte provavelmente já estava correta)
        de_y, de_x = de_yx
        para_y, para_x = para_yx

        if not (0 <= de_y < 10 and 0 <= de_x < 10 and 0 <= para_y < 10 and 0 <= para_x < 10):
            return "Movimento fora do tabuleiro."

        peca_movida = self.grid[de_y][de_x]
        if peca_movida is None: return "Não há peça na posição inicial."
        if peca_movida.jogador != jogador_id: return "Você não pode mover a peça do oponente."
        
        if abs(de_y - para_y) + abs(de_x - para_x) != 1:
             return "Movimento inválido. Mova apenas uma casa."

        if peca_movida.nome in ["bomba", "bandeira"]: return "Bandeiras e Bombas não podem se mover."

        peca_alvo = self.grid[para_y][para_x]
        if peca_alvo == "LAGO": return "Não é possível mover para o lago."

        if peca_alvo is None:
            self.grid[para_y][para_x] = peca_movida
            self.grid[de_y][de_x] = None
            return "Movimento realizado com sucesso."

        if peca_alvo.jogador == jogador_id: return "Você não pode atacar suas próprias peças."

        atacante = peca_movida
        defensor = peca_alvo

        if defensor.nome == 'bomba':
            self.grid[de_y][de_x] = None
            return f"Combate! Seu {atacante.nome} foi destruído!"
        
        if defensor.nome == 'bandeira':
            self.grid[para_y][para_x] = atacante
            self.grid[de_y][de_x] = None
            return f"FIM_DE_JOGO:VITORIA_JOGADOR_{jogador_id}"

        if atacante.nome == 'espiao' and defensor.nome == 'marechal':
            resultado = "Combate! Seu Espião capturou o Marechal!"
            self.grid[para_y][para_x] = atacante
            self.grid[de_y][de_x] = None
            return resultado

        if atacante.rank > defensor.rank:
            resultado = f"Combate! Seu {atacante.nome} venceu o {defensor.nome}."
            self.grid[para_y][para_x] = atacante
            self.grid[de_y][de_x] = None
        elif atacante.rank < defensor.rank:
            resultado = f"Combate! Seu {atacante.nome} perdeu para o {defensor.nome}."
            self.grid[de_y][de_x] = None
        else:
            resultado = f"Combate! Empate. Ambos foram removidos."
            self.grid[para_y][para_x] = None
            self.grid[de_y][de_x] = None
        return resultado