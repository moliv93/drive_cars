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
WHITE = (255, 255, 255)
CIRCUIT_SCALE = 1.4
CAR_RADIUS = 20
RAYS_COUNT = 5
RAYS_ANGLE = 180 / RAYS_COUNT
RAY_LENGTH = 300 * CIRCUIT_SCALE

# Carregando a imagem do carro
car_image = pygame.image.load('carro.png')
car_image = pygame.transform.scale(car_image, (25, 50))  # Redimensionar o carro

class RayCast:
    def __init__(self, ray):
        self.ray: Vector2 = ray
        self.distance = 0
        self.colliding = False

class CarInput:
    def __init__(self, left, right, up, down, reset):
        self.left = left
        self.right = right
        self.up = up
        self.down = down
        self.reset = reset

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

def check_point_line_intersection_during_move(current_pos, next_pos, p1, p2):
    def orientation(a, b, c):
        val = (b.y - a.y) * (c.x - b.x) - (b.x - a.x) * (c.y - b.y)
        if val == 0:
            return 0
        elif val > 0:
            return 1
        else:
            return 2
    def on_segment(a, b, c):
        return min(a.x, b.x) <= c.x <= max(a.x, b.x) and min(a.y, b.y) <= c.y <= max(a.y, b.y)
    def get_intersection_point(a1, a2, b1, b2):
        s1 = a2 - a1
        s2 = b2 - b1
        denom = (-s2.x * s1.y + s1.x * s2.y)
        if denom == 0:
            return None
        s = (-s1.y * (a1.x - b1.x) + s1.x * (a1.y - b1.y)) / denom
        t = (s2.x * (a1.y - b1.y) - s2.y * (a1.x - b1.x)) / denom
        if 0 <= s <= 1 and 0 <= t <= 1:
            # Calcula o ponto de interseção
            intersection_point = a1 + t * s1
            return intersection_point
        return None
    o1 = orientation(current_pos, next_pos, p1)
    o2 = orientation(current_pos, next_pos, p2)
    o3 = orientation(p1, p2, current_pos)
    o4 = orientation(p1, p2, next_pos)
    if o1 != o2 and o3 != o4:
        return get_intersection_point(current_pos, next_pos, p1, p2)
    if o1 == 0 and on_segment(current_pos, next_pos, p1):
        return p1
    if o2 == 0 and on_segment(current_pos, next_pos, p2):
        return p2
    if o3 == 0 and on_segment(p1, p2, current_pos):
        return current_pos
    if o4 == 0 and on_segment(p1, p2, next_pos):
        return next_pos
    return None

def projection_point_on_segment(p1, p2, circle_center):
    # Vetor do segmento
    segment_vector = p2 - p1
    # Vetor do centro do círculo até p1
    to_circle_vector = circle_center - p1
    # Normalizar o vetor do segmento
    segment_unit_vector = segment_vector.normalize()
    # Projeção do vetor to_circle_vector no vetor segment_unit_vector
    projection_length = to_circle_vector.dot(segment_unit_vector)
    # A projeção do ponto no segmento será p1 + projection_length * segment_unit_vector
    projected_point = p1 + segment_unit_vector * projection_length
    # Verificar se o ponto projetado está fora do segmento
    # Para isso, precisamos garantir que a projeção esteja entre p1 e p2
    if projection_length < 0:
        return p1  # O ponto projetado está antes de p1, retorna p1
    elif projection_length > segment_vector.length():
        return p2  # O ponto projetado está além de p2, retorna p2
    return projected_point

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
        self.rays = [RayCast(Vector2(1, 0).rotate(i) * RAY_LENGTH) for i in range(-180, 45, 45)]

    def draw(self, screen):
        rotated_image = pygame.transform.rotate(self.image, self.angle)
        new_rect = rotated_image.get_rect(center=self.rect.center)
        screen.blit(rotated_image, new_rect.topleft)
        pygame.draw.circle(screen, WHITE, self.circle_center, CAR_RADIUS, 2)
        for i, ray in enumerate(self.rays):
            ray_cast = ray.ray.rotate(-self.angle)
            ray_end = self.circle_center + ray_cast
            pygame.draw.line(screen, (0, 255, 0), self.circle_center, ray_end, 2)
            pygame.draw.circle(screen, (255, 0, 0), ray_end, 5)
            font = pygame.font.Font(None, 24)
            text = font.render(str(ray.distance), True, (255, 255, 255))
            screen.blit(text, (10, 10 + i * 20))


    def update(self, car_input):
        if car_input.reset:
            self.rect.center = (self.circuito.get('partida').x, self.circuito.get('partida').y)
            self.circle_center = Vector2(self.rect.center)
            self.angle = 0
            self.speed = 0
        # Movimentos de rotação
        if car_input.left:
            self.angle += 5  # Girar para a esquerda
        if car_input.right:
            self.angle -= 5  # Girar para a direita

        # Movimentos para frente e para trás
        if car_input.up:
            self.speed -= ACCEL  # Aumenta a velocidade
        elif car_input.down:
            self.speed += ACCEL  # Reverter a direção
        self.speed = min(0, self.speed)

        # Convertendo o ângulo para coordenadas de movimento
        radian_angle = math.radians(self.angle)
        movement_vector = Vector2(self.speed * math.sin(radian_angle), self.speed * math.cos(radian_angle))
        next_center = self.circle_center + movement_vector

        for i, ray in enumerate(self.rays):
            ray.distance = RAY_LENGTH
            ray.colliding = False
        for wall in self.circuito.get('walls'):
            for i, ray in enumerate(self.rays):
                ray_cast = ray.ray.rotate(-self.angle)
                ray_end = self.circle_center + ray_cast
                intersection_point = check_point_line_intersection_during_move(self.circle_center, ray_end, wall[0], wall[1])
                if intersection_point and (intersection_point - self.circle_center).length() < ray.distance:
                    distance = (intersection_point - self.circle_center).length()
                    ray.colliding = True
                    ray.distance = distance

        collided = False
        evade = False
        colided_wall = None
        if self.speed == 0:
            for wall in self.circuito.get('walls'):
                if line_circle_collision(wall[0], wall[1], self.circle_center, CAR_RADIUS):
                    evade = True
                    colided_wall = wall
                    break
        else:
            for wall in self.circuito.get('walls'):
                if line_circle_collision(wall[0], wall[1], next_center, CAR_RADIUS):
                    collided = True
                    break
        if evade:
            self.rect.center += (self.circle_center -
             projection_point_on_segment(wall[0], wall[1], self.circle_center)) * 0.04
            self.circle_center = Vector2(self.rect.center)
        # Atualizar a posição do carro com ou sem colisão
        if not collided:
            self.rect.center += movement_vector
            self.circle_center = Vector2(self.rect.center)
        else:
            self.speed = 0

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

circuito = load_walls('circuito.txt')

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

    car_input = CarInput(keys_pressed[pygame.K_LEFT], keys_pressed[pygame.K_RIGHT], keys_pressed[pygame.K_UP], keys_pressed[pygame.K_DOWN], keys_pressed[pygame.K_r])

    # Atualizar o carro
    car.update(car_input)

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
