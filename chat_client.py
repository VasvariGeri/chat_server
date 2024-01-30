import threading
import socket
import json
import pygame
from pygame.locals import *
import time
import tkinter as tk
from tkinter import simpledialog

# Ablak mérete
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 500

# Színek és stílus
BACKGROUND_COLOR = (48, 48, 48)  # Háttérszín (szürke)
INPUT_BOX_COLOR = (64, 64, 64)  # Beviteli mező színe (sötétszürke)
BUTTON_COLOR = (112, 112, 112)  # Gombok színe (világosszürke)
SEND_BUTTON_COLOR = (30, 144, 255)  # "Send" gomb színe (dodgerblue)
CLOSE_BUTTON_COLOR = (255, 69, 0)  # "Close" gomb színe (orangered)
HOVERED_SEND_BUTTON_COLOR = (70, 170, 255)  # Rámutatott "Send" gomb színe
HOVERED_CLOSE_BUTTON_COLOR = (255, 89, 0)  # Rámutatott "Close" gomb színe
MESSAGE_BOX_COLOR = (255, 255, 255)  # Üzenetek háttere (fehér)
TEXT_COLOR = (0, 0, 0)  # Szövegszín (fekete)
CURSOR_COLOR = (255, 255, 255)  # Kurzor színe (fehér)
FONT_SIZE = 20  # Betűméret

# Szövegbeviteli mező mérete és helye
INPUT_BOX_WIDTH = 600
INPUT_BOX_HEIGHT = 30
INPUT_BOX_X = 10
INPUT_BOX_Y = WINDOW_HEIGHT - INPUT_BOX_HEIGHT - 10

# Gombok mérete és helye
SEND_BUTTON_WIDTH = 80
SEND_BUTTON_HEIGHT = 30
SEND_BUTTON_X = INPUT_BOX_X + INPUT_BOX_WIDTH + 10
SEND_BUTTON_Y = INPUT_BOX_Y

CLOSE_BUTTON_WIDTH = 80
CLOSE_BUTTON_HEIGHT = 30
CLOSE_BUTTON_X = SEND_BUTTON_X + SEND_BUTTON_WIDTH + 10
CLOSE_BUTTON_Y = INPUT_BOX_Y

# Üzenetek megjelenítéséhez kapcsolódó változók
MESSAGE_BOX_X = 10
MESSAGE_BOX_Y = 10
MESSAGE_BOX_WIDTH = WINDOW_WIDTH - 20
MESSAGE_BOX_HEIGHT = WINDOW_HEIGHT - INPUT_BOX_HEIGHT - 30

# Pygame színek
WHITE = (255, 255, 255)


class UserClient:
    def __init__(self, name, connect_ip, connect_port):
        self.name = name
        self.connect_ip = connect_ip
        self.connect_port = connect_port
        self.server = None
        self.message_queue = []
        self.input_text = ""
        self.cursor_visible = True
        self.cursor_timer = 0

    def connect_to_server(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((self.connect_ip, self.connect_port))
        self.server.send(json.dumps({"type": "REQUEST", "msg": [self.name]}).encode())

    def send_message(self, message):
        if self.server is not None:
            try:
                self.server.send(json.dumps({"type": "NEWMSG", "msg": [self.name, message]}).encode())
            except BrokenPipeError:
                exit(1)

    def receive_messages(self):
        while True:
            if self.server is not None:
                try:
                    data = self.server.recv(1024)
                except OSError:
                    exit(1)
                if data:
                    try:
                        msg = json.loads(data.decode())
                    except json.decoder.JSONDecodeError:
                        self.message_queue.append("Message not readable.")
                        print(data)
                    else:
                        if msg["type"] == "NEWMSG":
                            self.message_queue.append(f"{msg['msg'][0]}: {msg['msg'][1]}")
                            if len(self.message_queue) > 14:
                                self.message_queue.pop(0)
                        elif msg["type"] == "NEWCON":
                            self.message_queue.append(f"{msg['msg']} connected to the chat")
                            if len(self.message_queue) > 14:
                                self.message_queue.pop(0)
                        elif msg["type"] == "CLOSED":
                            self.message_queue.append(f"{msg['msg']} left the chat")
                            if len(self.message_queue) > 14:
                                self.message_queue.pop(0)

    def close_connection(self):
        if self.server is not None:
            #self.server.send(json.dumps({"type": "NEWMSG", "msg": [self.name, 'left the chat']}).encode())
            self.server.send(json.dumps({"type": "CLOSED", "msg": [self.name]}).encode())
            time.sleep(0.1)
            self.server.close()

    def start(self):
        pygame.init()
        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Chat ablak Pygame-ben')
        clock = pygame.time.Clock()

        font = pygame.font.Font(None, FONT_SIZE)

        input_box = pygame.Rect(INPUT_BOX_X, INPUT_BOX_Y, INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT)
        send_button = pygame.Rect(SEND_BUTTON_X, SEND_BUTTON_Y, SEND_BUTTON_WIDTH, SEND_BUTTON_HEIGHT)
        close_button = pygame.Rect(CLOSE_BUTTON_X, CLOSE_BUTTON_Y, CLOSE_BUTTON_WIDTH, CLOSE_BUTTON_HEIGHT)

        self.connect_to_server()
        threading.Thread(target=self.receive_messages).start()

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN:
                    if event.key == K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    elif event.key == K_RETURN:
                        self.send_message(self.input_text)
                        self.input_text = ""
                    else:
                        self.input_text += event.unicode
                elif event.type == MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if send_button.collidepoint(mouse_pos):
                        self.send_message(self.input_text)
                        self.input_text = ""
                    elif close_button.collidepoint(mouse_pos):
                        self.close_connection()
                        running = False

            screen.fill(BACKGROUND_COLOR)

            pygame.draw.rect(screen, INPUT_BOX_COLOR, input_box)
            pygame.draw.rect(screen, SEND_BUTTON_COLOR, send_button)
            pygame.draw.rect(screen, CLOSE_BUTTON_COLOR, close_button)

            # Gombok színe a rámutatás szerint
            if send_button.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(screen, HOVERED_SEND_BUTTON_COLOR, send_button)
            if close_button.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(screen, HOVERED_CLOSE_BUTTON_COLOR, close_button)

            screen.blit(font.render(self.input_text, True, WHITE), (input_box.x + 5, input_box.y + 5))

            message_box = pygame.Rect(MESSAGE_BOX_X, MESSAGE_BOX_Y, MESSAGE_BOX_WIDTH, MESSAGE_BOX_HEIGHT)
            pygame.draw.rect(screen, MESSAGE_BOX_COLOR, message_box)

            visible_messages = self.message_queue[-14:]
            message_y = message_box.y + 10
            for message in visible_messages:
                message_render = font.render(message, True, TEXT_COLOR)
                screen.blit(message_render, (message_box.x + 10, message_y))
                message_y += 30

            # Villogó kurzor
            if pygame.time.get_ticks() - self.cursor_timer > 500:
                self.cursor_timer = pygame.time.get_ticks()
                self.cursor_visible = not self.cursor_visible

            if self.cursor_visible:
                cursor_pos = font.size(self.input_text)[0] + input_box.x + 5
                pygame.draw.line(screen, CURSOR_COLOR, (cursor_pos, input_box.y + 5),
                                 (cursor_pos, input_box.y + input_box.height - 5), 2)

            # Feher szoveg a "Send" gombon
            screen.blit(font.render("Send", True, WHITE), (send_button.x + 5, send_button.y + 5))
            
            # Feher szoveg a "Close" gombon
            screen.blit(font.render("Close", True, WHITE), (close_button.x + 5, close_button.y + 5))

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
    
class Popup:
    def __init__(self) -> None:
        self.name = None
        self.ip = None
        self.root = tk.Tk()
        self.root.withdraw()

    def get_name(self):
        self.name = simpledialog.askstring("Input", "Enter your name:")

    def get_ip(self):
        self.ip = simpledialog.askstring("Input", "Enter host ip:")

    def display_gui(self):
        self.get_name()
        self.get_ip()
        self.root.destroy()


if __name__ == "__main__":
    popup = Popup()
    popup.display_gui()
    client = UserClient(popup.name, popup.ip, 10000)
    client.start()
