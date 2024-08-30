import pygame
import math

from pygame import Vector2

# Inicializando o pygame
pygame.init()

# Definindo a largura e altura da tela
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Jogo de Carro Top-Down')

ACCEL = 0.1  # Aceleração do carro

BROWN = (165, 42, 42)
CIRCUIT_SCALE = 1.4
CAR_RADIUS = 20

# Carregando a imagem do carro
car_image = pygame.image.load('carro.png')
car_image = pygame.transform.scale(car_image, (25, 50))  # Redimensionar o carro

def triangle_area(p1, p2, p3):
    return abs((p1.x * (p2.y - p3.y) + p2.x * (p3.y - p1.y) + p3.x * (p1.y - p2.y)) / 2)
    # return abs((p3 - p2).cross(p1 - p2) / 2)

def line_circle_collision(p1, p2, circle_center, circle_radius):
    # se o angulo entre o segmento p1-p2 e o segmento p1-circle_center for maior que 90 graus, então o ponto mais próximo é p1
    if (circle_center - p1).dot(p2 - p1) < 0:
        return (circle_center - p1).length() < circle_radius
    # se o angulo entre o segmento p2-p1 e o segmento p2-circle_center for maior que 90 graus, então o ponto mais próximo é p2
    if (circle_center - p2).dot(p1 - p2) < 0:
        return (circle_center - p2).length() < circle_radius
    # caso contrário, o ponto mais próximo é perpendicular ao segmento
    return 2 * triangle_area(p1, p2, circle_center) / (p2 - p1).length() < circle_radius

def project_along_wall(wall, movement):
    # Pega o vetor da parede
    wall_vector = wall[1] - wall[0]
    wall_vector = wall_vector.normalize()

    # Projeta o movimento ao longo da parede
    projection = wall_vector * movement.dot(wall_vector)
    return projection

# Definindo a classe do carro
class Car:
    def __init__(self, circuito):
        self.image = car_image
        self.rect = self.image.get_rect(center=(circuito.get('partida').x, circuito.get('partida').y))
        self.angle = 0  # Ângulo de rotação do carro
        self.speed = 0  # Velocidade inicial do carro
        self.circuito = circuito
        self.circle_center = Vector2(self.rect.center)

    def draw(self, screen):
        rotated_image = pygame.transform.rotate(self.image, self.angle)
        new_rect = rotated_image.get_rect(center=self.rect.center)
        screen.blit(rotated_image, new_rect.topleft)
        pygame.draw.circle(screen, (0, 0, 50, 50), self.circle_center, CAR_RADIUS, 2)

    def update(self, keys_pressed):
        if keys_pressed[pygame.K_SPACE]:
            self.rect.center = (self.circuito.get('partida').x, self.circuito.get('partida').y)
            self.circle_center = Vector2(self.rect.center)
            self.angle = 0
            self.speed = 0
        # Movimentos de rotação
        if keys_pressed[pygame.K_LEFT]:
            self.angle += 5  # Girar para a esquerda
        if keys_pressed[pygame.K_RIGHT]:
            self.angle -= 5  # Girar para a direita

        # Movimentos para frente e para trás
        if keys_pressed[pygame.K_UP]:
            self.speed -= ACCEL  # Aumenta a velocidade
        elif keys_pressed[pygame.K_DOWN]:
            self.speed += ACCEL  # Reverter a direção
        self.speed = min(0, self.speed)

        # Convertendo o ângulo para coordenadas de movimento
        radian_angle = math.radians(self.angle)
        movement_vector = Vector2(self.speed * math.sin(radian_angle), self.speed * math.cos(radian_angle))
        next_center = self.circle_center + movement_vector

        collided = False
        collision_wall = None
        for wall in self.circuito.get('walls'):
            if line_circle_collision(wall[0], wall[1], next_center, CAR_RADIUS):
                collided = True
                collision_wall = wall
                # Projetar o vetor de movimento ao longo da parede
                # movement_vector = project_along_wall(wall, movement_vector)
                break
        print(collided)
        # Atualizar a posição do carro com ou sem colisão
        if not collided:
            self.rect.center += movement_vector
            self.circle_center = Vector2(self.rect.center)
        else:
            # Ajustar o movimento projetado ao longo da parede
            self.rect.center += project_along_wall(collision_wall, movement_vector)
            self.circle_center = Vector2(self.rect.center)

def load_walls(filename):
    circuit = {'partida': Vector2(0, 0), 'walls': []}
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            if line.startswith('partida:'):
                circuit.get('partida').x, circuit.get('partida').y = map(int, line.strip().split(':')[1].split(','))
                circuit.get('partida').x *= CIRCUIT_SCALE
                circuit.get('partida').y *= CIRCUIT_SCALE
                continue
            x1, y1, x2, y2 = map(int, line.strip().split(','))
            circuit.get('walls').append((Vector2(x1 * CIRCUIT_SCALE, y1 * CIRCUIT_SCALE), Vector2(x2 * CIRCUIT_SCALE, y2 * CIRCUIT_SCALE)))
    return circuit

def draw_circuit(screen, circuit):
    for wall in circuit.get('walls'):
        pygame.draw.line(screen, BROWN, wall[0], wall[1], 5)

circuito = load_walls('circuito2.txt')

# Inicializando o carro
car = Car(circuito)

# Configurando o relógio do jogo
clock = pygame.time.Clock()

# Loop principal do jogo
running = True

while running:
    # Verificar eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Verificar teclas pressionadas
    keys_pressed = pygame.key.get_pressed()

    # Atualizar o carro
    car.update(keys_pressed)

    # Preencher a tela com cor (fundo)
    screen.fill((30, 30, 30))  # Cor de fundo (cinza escuro)

    # Desenhar o carro
    car.draw(screen)
    draw_circuit(screen, circuito)

    # Atualizar a tela
    pygame.display.flip()

    # Controlar a taxa de quadros
    clock.tick(30)

# Finalizar o pygame
pygame.quit()
