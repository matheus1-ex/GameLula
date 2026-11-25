
import pygame
import random
import sys

# --- CONFIGURAÇÕES GERAIS ---
LARGURA, ALTURA = 900, 600
FPS = 60

# Limites do térreo (onde os personagens podem pisar)
CHAO_TOPO = 320
CHAO_BASE = ALTURA - 20

# Cores (Placeholders antes de colocar sprites)
COR_CEU = (88, 252, 254)
COR_PAREDE = (90, 90, 110)
COR_CHAO = (65, 65, 75)
COR_SOMBRA = (35, 35, 40)
COR_JOGADOR = (50, 150, 255)
COR_ATAQUE = (255, 220, 50)
COR_INIMIGO = (220, 60, 60)
COR_ITEM_CURA = (60, 220, 100)
COR_ITEM_ARMA = (255, 165, 0)
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)

class Nuvem:
    def __init__(self, imagem, largura_tela):
        self.imagem = imagem
        self.largura_tela = largura_tela
        self.x = random.randint(0, largura_tela)
        self.y = random.randint(15, 130)  # Faixa do céu acima dos morros
        self.velocidade = random.uniform(0.3, 0.8)  # Bem lento para dar profundidade

    def atualizar(self):
        self.x -= self.velocidade
        # Se saiu totalmente pela esquerda, volta pela direita
        if self.x < -self.imagem.get_width():
            self.x = self.largura_tela + random.randint(10, 80)
            self.y = random.randint(15, 130)

    def desenhar(self, tela):
        tela.blit(self.imagem, (int(self.x), self.y))

class Entidade:
    """Classe base para tudo que pisa no chão (permite ordenar por profundidade)."""
    def __init__(self, x, y, largura, altura):
        self.x = x
        self.y = y  # Representa a posição dos PÉS no chão
        self.largura = largura
        self.altura = altura

    def get_rect_corpo(self):
        return pygame.Rect(self.x - self.largura // 2, self.y - self.altura, self.largura, self.altura)

    def desenhar_sombra(self, tela):
        sombra_rect = pygame.Rect(self.x - self.largura // 2, self.y - 8, self.largura, 16)
        pygame.draw.ellipse(tela, COR_SOMBRA, sombra_rect)


class Jogador(Entidade):
    def __init__(self, x, y):
        super().__init__(x, y, 45, 80)
        self.velocidade = 5
        self.direcao = 1  # 1 = direita, -1 = esquerda
        self.vida_max = 100
        self.vida = 100
        self.pontos = 0

        # Combate
        self.atacando = False
        self.timer_ataque = 0
        self.cooldown_ataque = 0
        self.dano_base = 25
        self.tem_arma = False
        self.timer_arma = 0

    def atualizar(self, teclas):
        dx, dy = 0, 0
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            dx = -self.velocidade
            self.direcao = -1
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            dx = self.velocidade
            self.direcao = 1
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            dy = -self.velocidade * 0.8  # Um pouco mais lento na profundidade dá realismo
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            dy = self.velocidade * 0.8

        # Atualiza posição mantendo dentro do térreo
        self.x = max(30, min(LARGURA - 30, self.x + dx))
        self.y = max(CHAO_TOPO, min(CHAO_BASE, self.y + dy))

        # Timers de ataque e arma
        if self.timer_ataque > 0:
            self.timer_ataque -= 1
        else:
            self.atacando = False

        if self.cooldown_ataque > 0:
            self.cooldown_ataque -= 1

        if self.tem_arma:
            self.timer_arma -= 1
            if self.timer_arma <= 0:
                self.tem_arma = False

    def atacar(self):
        if self.cooldown_ataque == 0:
            self.atacando = True
            self.timer_ataque = 10      # Duração visual do soco/golpe
            self.cooldown_ataque = 20   # Tempo até poder bater de novo
            return True
        return False

    def get_hitbox_ataque(self):
        alcance = 75 if self.tem_arma else 50
        if self.direcao == 1:
            return pygame.Rect(self.x, self.y - 60, alcance, 40)
        else:
            return pygame.Rect(self.x - alcance, self.y - 60, alcance, 40)

    def desenhar(self, tela):
        self.desenhar_sombra(tela)
        pygame.draw.rect(tela, COR_JOGADOR, self.get_rect_corpo(), border_radius=6)

        # Olho para indicar direção
        olho_x = self.x + (10 if self.direcao == 1 else -16)
        pygame.draw.rect(tela, BRANCO, (olho_x, self.y - 68, 8, 8))

        # Indicador de arma equipada
        if self.tem_arma:
            arma_x = self.x + (20 if self.direcao == 1 else -35)
            pygame.draw.rect(tela, COR_ITEM_ARMA, (arma_x, self.y - 45, 15, 30))

        # Efeito visual do golpe
        if self.atacando:
            pygame.draw.rect(tela, COR_ATAQUE, self.get_hitbox_ataque(), border_radius=4)


class Inimigo(Entidade):
    def __init__(self):
        # Nasce fora da tela pela esquerda ou direita, ou vindo do fundo/frente
        lado = random.choice(["esquerda", "direita"])
        if lado == "esquerda":
            x, y = -30, random.randint(CHAO_TOPO, CHAO_BASE)
        elif lado == "direita":
            x, y = LARGURA + 30, random.randint(CHAO_TOPO, CHAO_BASE)

        super().__init__(x, y, 42, 75)
        self.velocidade = random.uniform(1.8, 3.0)
        self.vida = 50
        self.cooldown_dano = 0

    def atualizar(self, jogador):
        # Persegue o jogador no térreo
        dx = jogador.x - self.x
        dy = jogador.y - self.y
        distancia = max(1, (dx**2 + dy**2) ** 0.5)

        if distancia > 35:
            self.x += (dx / distancia) * self.velocidade
            self.y += (dy / distancia) * self.velocidade

        # Garante que fique na faixa do chão depois de entrar
        self.y = max(CHAO_TOPO, min(CHAO_BASE, self.y))

        if self.cooldown_dano > 0:
            self.cooldown_dano -= 1

    def desenhar(self, tela):
        self.desenhar_sombra(tela)
        pygame.draw.rect(tela, COR_INIMIGO, self.get_rect_corpo(), border_radius=6)
        # Barrinha de vida em cima da cabeça
        pygame.draw.rect(tela, PRETO, (self.x - 20, self.y - 88, 40, 6))
        pygame.draw.rect(tela, COR_ITEM_CURA, (self.x - 19, self.y - 87, int(38 * (self.vida / 50)), 4))


class ItemCeu(Entidade):
    """Cai do céu até uma posição específica no chão."""
    def __init__(self):
        x = random.randint(60, LARGURA - 60)
        y_chao = random.randint(CHAO_TOPO + 10, CHAO_BASE - 10)
        super().__init__(x, y_chao, 28, 28)
        self.altura_z = random.randint(350, 500)  # Começa alto no céu
        self.vel_queda = 3.5
        self.tipo = random.choice(["cura", "arma"])
        self.tempo_vida_chao = 480  # 8 segundos no chão antes de sumir

    def atualizar(self):
        if self.altura_z > 0:
            self.altura_z = max(0, self.altura_z - self.vel_queda)
        else:
            self.tempo_vida_chao -= 1

    def desenhar(self, tela):
        # Sombra no chão cresce conforme o item chega perto do solo
        escala = max(0.3, 1 - (self.altura_z / 500))
        larg_sombra = int(self.largura * escala)
        pygame.draw.ellipse(tela, COR_SOMBRA, (self.x - larg_sombra // 2, self.y - 6, larg_sombra, 12))

        # Desenha o item deslocado para cima pelo eixo Z
        cor = COR_ITEM_CURA if self.tipo == "cura" else COR_ITEM_ARMA
        pos_visual_y = self.y - self.altura_z - self.altura
        pygame.draw.rect(tela, cor, (self.x - self.largura // 2, pos_visual_y, self.largura, self.altura), border_radius=5)


def desenhar_cenario(tela):
    tela.fill(COR_CEU)
    # Parede de fundo
    pygame.draw.rect(tela, COR_PAREDE, (0, 140, LARGURA, CHAO_TOPO - 140))
    # Térreo (área jogável)
    pygame.draw.rect(tela, COR_CHAO, (0, CHAO_TOPO, LARGURA, ALTURA - CHAO_TOPO))
    # Linha do meio-fio / limite superior do chão
    pygame.draw.line(tela, (120, 120, 130), (0, CHAO_TOPO), (LARGURA, CHAO_TOPO), 4)


def main():
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Lulis contra todes")
    relogio = pygame.time.Clock()
    fonte = pygame.font.SysFont("montserrat", 22, bold=True)

    jogador = Jogador(LARGURA // 2, (CHAO_TOPO + CHAO_BASE) // 2)
    inimigos = []
    itens = []

    timer_spawn_inimigo = 0
    timer_spawn_item = 180
    game_over = False

    while True:
        relogio.tick(FPS)

        # Ajusta a altura para caber na tela mantendo a proporção (ou estica para LARGURA, ALTURA)
        cenario_img = pygame.transform.scale(cenario_img, (LARGURA, ALTURA))

        # Carrega os sprites das nuvens (ex: nuvem1.png, nuvem2.png)
        imgs_nuvens = [
            pygame.image.load("assets/nuvem1.png").convert_alpha(),
            pygame.image.load("assets/nuvem2.png").convert_alpha(),
        ]
        # Cria 5 nuvens espalhadas no céu
        nuvens = [Nuvem(random.choice(imgs_nuvens), LARGURA) for _ in range(5)]

        # --- DENTRO DO LOOP PRINCIPAL ---
        # 1. Atualiza as nuvens
        for nuvem in nuvens:
            nuvem.atualizar()

        # 2. Desenha na ordem certa (de trás para frente)
        tela.fill(COR_CEU)  # Fundo azul do céu
        for nuvem in nuvens:  # Nuvens passando lá atrás
            nuvem.desenhar(tela)
        tela.blit(cenario_img, (0, 0))

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if evento.type == pygame.KEYDOWN:
                if not game_over and evento.key in (pygame.K_SPACE, pygame.K_j, pygame.K_z):
                    if jogador.atacar():
                        hitbox = jogador.get_hitbox_ataque()
                        dano = jogador.dano_base * (2 if jogador.tem_arma else 1)
                        for inimigo in inimigos[:]:
                            # Só acerta se estiver na mesma faixa de profundidade (eixo Y próximo)
                            mesma_profundidade = abs(jogador.y - inimigo.y) < 35
                            if mesma_profundidade and hitbox.colliderect(inimigo.get_rect_corpo()):
                                inimigo.vida -= dano
                                # Empurrão (knockback)
                                inimigo.x += 25 * jogador.direcao
                                if inimigo.vida <= 0:
                                    inimigos.remove(inimigo)
                                    jogador.pontos += 100

                if game_over and evento.key == pygame.K_r:
                    main()  # Reinicia o jogo

        if not game_over:
            teclas = pygame.key.get_pressed()
            jogador.atualizar(teclas)

            # Spawn progressivo de inimigos
            timer_spawn_inimigo -= 1
            if timer_spawn_inimigo <= 0:
                inimigos.append(Inimigo())
                # Dificuldade aumenta conforme a pontuação
                timer_spawn_inimigo = max(45, 130 - (jogador.pontos // 300) * 10)

            # Spawn de itens caindo do céu
            timer_spawn_item -= 1
            if timer_spawn_item <= 0:
                itens.append(ItemCeu())
                timer_spawn_item = random.randint(300, 480)

            # Atualiza inimigos e verifica ataque deles
            for inimigo in inimigos:
                inimigo.atualizar(jogador)
                mesma_profundidade = abs(jogador.y - inimigo.y) < 25
                if mesma_profundidade and jogador.get_rect_corpo().colliderect(inimigo.get_rect_corpo()):
                    if inimigo.cooldown_dano == 0:
                        jogador.vida -= 10
                        inimigo.cooldown_dano = 45
                        if jogador.vida <= 0:
                            jogador.vida = 0
                            game_over = True

            # Atualiza itens do céu e verifica coleta
            for item in itens[:]:
                item.atualizar()
                if item.tempo_vida_chao <= 0:
                    itens.remove(item)
                    continue

                # Só coleta se o item já tocou o chão (altura_z == 0) e estiver perto no Y
                if item.altura_z == 0 and abs(jogador.y - item.y) < 30:
                    if jogador.get_rect_corpo().colliderect(item.get_rect_corpo()):
                        if item.tipo == "cura":
                            jogador.vida = min(jogador.vida_max, jogador.vida + 30)
                        elif item.tipo == "arma":
                            jogador.tem_arma = True
                            jogador.timer_arma = 600  # 10 segundos com arma
                        itens.remove(item)

        # --- RENDERIZAÇÃO ---
        desenhar_cenario(tela)

        # Y-SORTING: ordena todas as entidades pelo Y dos pés para profundidade real
        todas_entidades = [jogador] + inimigos + itens
        todas_entidades.sort(key=lambda e: e.y)

        for entidade in todas_entidades:
            entidade.desenhar(tela)

        # HUD (Interface)
        pygame.draw.rect(tela, PRETO, (20, 20, 204, 24))
        pygame.draw.rect(tela, COR_ITEM_CURA, (22, 22, int(200 * (jogador.vida / jogador.vida_max)), 20))
        texto_hud = fonte.render(f"Pontos: {jogador.pontos}  |  Mover: WASD/Setas  |  Bater: Espaço", True, PRETO)
        tela.blit(texto_hud, (250, 20))

        if jogador.tem_arma:
            texto_arma = fonte.render("ARMA EQUIPADA (2x Dano)!", True, COR_ITEM_ARMA)
            tela.blit(texto_arma, (20, 55))

        if game_over:
            overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            tela.blit(overlay, (0, 0))
            msg = fonte.render(f"FIM DE JOGO! Pontuação final: {jogador.pontos} - Pressione R para reiniciar", True, BRANCO)
            tela.blit(msg, (LARGURA // 2 - msg.get_width() // 2, ALTURA // 2))

        pygame.display.flip()


if __name__ == "__main__":
    main()