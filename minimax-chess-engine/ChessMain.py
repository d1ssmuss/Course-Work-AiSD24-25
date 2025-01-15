import sys
import pygame as p
import ChessEngine
import Minimax
import math
import tkinter.messagebox
from cryptography.fernet import Fernet
import tkinter as tk
from tkinter import ttk

# Исправленная версия !!! 27.12.24 + исправил бота
WIDTH = 1050
HEIGHT = 850
MOVE_LOG_PANEL_WIDTH = 290
MOVE_LOG_PANEL_HEIGHT = HEIGHT
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 240
IMAGES = {}

# Функция для загрузки или генерации ключа шифрования
def load_or_generate_key():
    try:
        with open('key.key', 'rb') as key_file:
            key = key_file.read()
    except FileNotFoundError:
        key = Fernet.generate_key()
        with open('key.key', 'wb') as key_file:
            key_file.write(key)
    return key

key = load_or_generate_key()
cipher_suite = Fernet(key)

def load_images():
    pieces = ["wp", "wR", "wN", "wB", "wQ", "wK", "bp", "bR", "bN", "bB", "bQ", "bK"]
    for piece in pieces:
        IMAGES[piece] = p.transform.smoothscale(p.image.load("images/" + piece + ".png").convert_alpha(), (SQ_SIZE, SQ_SIZE))

def save_users(users):
    with open('users.txt', 'w', encoding='utf-8') as f:
        for username, encrypted_password in users.items():
            f.write(f"{username},{encrypted_password}\n")

def load_users():
    users = {}
    try:
        with open('users.txt', 'r', encoding='utf-8') as f:
            for line in f:
                username, encrypted_password = line.strip().split(',')
                users[username] = encrypted_password
    except FileNotFoundError:
        pass
    return users

def encrypt_password(password):
    return cipher_suite.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password):
    return cipher_suite.decrypt(encrypted_password.encode()).decode()

def main():
    p.init()
    p.display.set_caption("Эндшпиль: Король и Ладья против Короля и Двух Коней")
    screen = p.display.set_mode((WIDTH + MOVE_LOG_PANEL_WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("black"))
    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False
    animate = False
    gameOver = False
    playerOne = True
    playerTwo = False
    load_images()
    sqSelected = ()
    playerClicks = []
    scroll_offset = 0
    scroll_bar_dragging = False
    scroll_bar_rect = p.Rect(WIDTH + MOVE_LOG_PANEL_WIDTH - 20, 0, 20, MOVE_LOG_PANEL_HEIGHT)
    scroll_bar_handle_rect = p.Rect(WIDTH + MOVE_LOG_PANEL_WIDTH - 20, 0, 20, 50)

    running = True
    while running:
        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            elif e.type == p.MOUSEBUTTONDOWN:
                if not gameOver and humanTurn:
                    location = p.mouse.get_pos()
                    col = location[0] // SQ_SIZE
                    row = location[1] // SQ_SIZE
                    if sqSelected == (row, col) or col >= 8:
                        sqSelected = ()
                        playerClicks = []
                    else:
                        sqSelected = (row, col)
                        playerClicks.append(sqSelected)
                    if len(playerClicks) == 2:
                        move = ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                        if move in validMoves:
                            move = validMoves[validMoves.index(move)]
                            gs.makeMove(move)
                            moveMade = True
                            animate = True
                            sqSelected = ()
                            playerClicks = []
                            print(move.getChessNotation())
                        else:
                            playerClicks = [sqSelected]
                if scroll_bar_rect.collidepoint(e.pos):
                    scroll_bar_dragging = True
                    mouse_x, mouse_y = e.pos
                    scroll_offset = (mouse_y - scroll_bar_handle_rect.y) / (MOVE_LOG_PANEL_HEIGHT - scroll_bar_handle_rect.height) * len(gs.moveLog)
            elif e.type == p.MOUSEBUTTONUP:
                scroll_bar_dragging = False
            elif e.type == p.MOUSEMOTION:
                if scroll_bar_dragging:
                    mouse_x, mouse_y = e.pos
                    scroll_offset = (mouse_y - scroll_bar_handle_rect.y) / (MOVE_LOG_PANEL_HEIGHT - scroll_bar_handle_rect.height) * len(gs.moveLog)
                    scroll_offset = max(0, min(scroll_offset, len(gs.moveLog) - 1))
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    gs.undoMove()
                    moveMade = True
                    animate = False
                    gameOver = False
                    playerOne = True
                    playerTwo = True
                elif e.key == p.K_r:
                    gs = ChessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    moveMade = False
                    animate = False
                    gameOver = False
                    playerOne = True
                    playerTwo = True
                    sqSelected = ()
                    playerClicks = []
                elif e.key == p.K_q:
                    playerOne = False
                    playerTwo = True
                elif e.key == p.K_e:
                    playerOne = True
                    playerTwo = False
                elif e.key == p.K_UP:
                    scroll_offset = max(0, scroll_offset - 1)
                elif e.key == p.K_DOWN:
                    scroll_offset = min(len(gs.moveLog) - 1, scroll_offset + 1)

        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False

        ''' AI move finder '''
        if not gameOver and not humanTurn:
            AIMove = Minimax.findBestMoveMinimax(gs, validMoves)
            if AIMove is None:   #when begin the game
                AIMove = Minimax.findRandomMove(validMoves)
            gs.makeMove(AIMove)
            moveMade = True
            animate = True
            print(AIMove.getChessNotation())

        drawGameState(screen, gs, validMoves, sqSelected)

        if gs.checkMate or gs.staleMate:
            gameOver = True
            if gs.staleMate:
                gameOver = True
                drawEndGameText(screen, "DRAW")
            else:
                if gs.whiteToMove:
                    drawEndGameText(screen, "BLACK WIN")
                else:
                    drawEndGameText(screen, "WHITE WIN")

        drawMoveLog(screen, gs, scroll_offset)
        drawScrollBar(screen, scroll_offset, len(gs.moveLog))

        clock.tick(MAX_FPS)
        p.display.flip()

def highlightMove(screen, gs, validMoves, sqSelected):
    sq = p.Surface((SQ_SIZE, SQ_SIZE))
    sq.set_alpha(100)
    if sqSelected != ():
        r, c = sqSelected
        if gs.board[r][c][0] == ('w' if gs.whiteToMove else 'b'): #sqSelected is a piece that can be moved
            #highlight selected square
            sq.fill(p.Color("blue"))
            screen.blit(sq, (c * SQ_SIZE, r * SQ_SIZE))
            #highlight validmoves
            sq.fill(p.Color("cyan"))
            for move in validMoves:
                if move.startRow == r and move.startCol == c:
                    screen.blit(sq, (move.endCol * SQ_SIZE, move.endRow * SQ_SIZE))

    if gs.inCheck:
        if gs.whiteToMove:
            sq.fill(p.Color("red"))
            screen.blit(sq, (gs.whiteKingLocate[1] * SQ_SIZE, gs.whiteKingLocate[0] * SQ_SIZE))
        else:
            sq.fill(p.Color("red"))
            screen.blit(sq, (gs.blackKingLocate[1] * SQ_SIZE, gs.blackKingLocate[0] * SQ_SIZE))

    if len(gs.moveLog) != 0:
        sq.fill(p.Color("yellow"))
        screen.blit(sq, (gs.moveLog[-1].startCol * SQ_SIZE, gs.moveLog[-1].startRow * SQ_SIZE))
        screen.blit(sq, (gs.moveLog[-1].endCol * SQ_SIZE, gs.moveLog[-1].endRow * SQ_SIZE))

def animateMove(move, screen, board, clock):
    colors = [p.Color("white"), p.Color("grey")]
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    sqDistance = math.sqrt(abs(move.endRow - move.startRow)*abs(move.endRow - move.startRow) +
                           abs(move.endCol - move.startCol)*abs(move.endCol - move.startCol))
    sqDistance = int(sqDistance)
    framesPerSquare = 12 // sqDistance
    frameCount = (abs(dR) + abs(dC)) * framesPerSquare
    for frame in range(frameCount + 1):
        r, c = (move.startRow + dR*frame/frameCount, move.startCol + dC*frame/frameCount)
        drawBoard(screen)
        drawPieces(screen, board)
        color = colors[(move.endRow + move.endCol) % 2]
        endSquare = p.Rect(move.endCol*SQ_SIZE, move.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)
        if move.pieceCaptured != "--":
            if move.isEnpassantMove:
                enPassantRow = (move.endRow + 1) if move.pieceCaptured[0] == 'b' else (move.endRow - 1)
                endSquare = p.Rect(move.endCol*SQ_SIZE, enPassantRow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
            screen.blit(IMAGES[move.pieceCaptured], endSquare)
        if move.pieceMoved != "--":
            screen.blit(IMAGES[move.pieceMoved], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(144)

def drawGameState(screen, gs, validMoves, sqSelected):
    drawBoard(screen)
    highlightMove(screen, gs, validMoves, sqSelected)
    drawPieces(screen, gs.board)

def drawBoard(screen):
    colors = [p.Color("white"), p.Color("grey")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r + c) % 2)]
            p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def drawPieces(screen, board):
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            piece = board[row][col]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def drawEndGameText(screen, text):
    font = p.font.SysFont("Times New Roman", 32, True, False)
    textObject = font.render(text, False, p.Color("black"))
    textLocation = p.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH/2 - textObject.get_width()/2, HEIGHT/2 - textObject.get_height()/2)
    screen.blit(textObject, textLocation)
    textObject = font.render(text, False, p.Color("red"))
    screen.blit(textObject, textLocation.move(2, 2))

def drawMoveLog(screen, gs, scroll_offset):
    moveLogRect = p.Rect(WIDTH - 200, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color("black"), moveLogRect)
    moveLog = gs.moveLog
    moveTexts = []
    for i in range(0, len(moveLog), 2):
        moveString = str(i//2 + 1) + ". " + str(moveLog[i]) + " "
        if i+1 < len(moveLog):
            moveString += str(moveLog[i+1]) + "   "
        moveTexts.append(moveString)

    padding = 5
    movesPerRow = 2
    lineSpacing = 3
    textY = padding
    for i in range(0, len(moveTexts), movesPerRow):
        text = ""
        font = p.font.SysFont("Tahoma", 20, True, False)
        for j in range(movesPerRow):
            if i+j < len(moveTexts):
                text += moveTexts[i+j]
        textObject = font.render(text, True, p.Color("white"))
        textLocation = moveLogRect.move(padding, textY - scroll_offset * (textObject.get_height() + lineSpacing))
        screen.blit(textObject, textLocation)
        textY += textObject.get_height() + lineSpacing

def drawScrollBar(screen, scroll_offset, total_moves):
    scroll_bar_rect = p.Rect(WIDTH + MOVE_LOG_PANEL_WIDTH - 20, 0, 20, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color("grey"), scroll_bar_rect)
    handle_height = max(20, MOVE_LOG_PANEL_HEIGHT / (total_moves + 1) * MOVE_LOG_PANEL_HEIGHT)
    handle_y = scroll_offset / (total_moves + 1) * (MOVE_LOG_PANEL_HEIGHT - handle_height)
    scroll_bar_handle_rect = p.Rect(WIDTH + MOVE_LOG_PANEL_WIDTH - 20, handle_y, 20, handle_height)
    p.draw.rect(screen, p.Color("darkgrey"), scroll_bar_handle_rect)

def show_login_register_window():
    root = tk.Tk()
    root.title("Окно входа(регистрации)")
    root.geometry('%dx%d+%d+%d' % (700, 700, 570, 240))

    tab_control = ttk.Notebook(root)
    tab_login = ttk.Frame(tab_control)
    tab_register = ttk.Frame(tab_control)

    tab_control.add(tab_login, text='Войти')
    tab_control.add(tab_register, text='Регистрация')
    tab_control.pack(expand=1, fill="both")

    # Login Tab
    login_frame = ttk.Frame(tab_login)
    login_frame.pack(pady=20)

    ttk.Label(login_frame, text="Пользователь:").grid(row=0, column=0, padx=10, pady=10)
    ttk.Label(login_frame, text="Пароль:").grid(row=1, column=0, padx=10, pady=10)

    username_entry = ttk.Entry(login_frame)
    password_entry = ttk.Entry(login_frame, show="*")

    username_entry.grid(row=0, column=1, padx=10, pady=10)
    password_entry.grid(row=1, column=1, padx=10, pady=10)

    def login():
        username = username_entry.get()
        password = password_entry.get()
        users = load_users()
        if username in users and decrypt_password(users[username]) == password:
            root.destroy()
            main()
        else:
            tk.messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль")

    login_button = ttk.Button(login_frame, text="Войти", command=login)
    login_button.grid(row=2, column=0, columnspan=2, pady=10)

    # Register Tab
    register_frame = ttk.Frame(tab_register)
    register_frame.pack(pady=20)

    ttk.Label(register_frame, text="Имя пользователя:").grid(row=0, column=0, padx=10, pady=10)
    ttk.Label(register_frame, text="Пароль:").grid(row=1, column=0, padx=10, pady=10)

    register_username_entry = ttk.Entry(register_frame)
    register_password_entry = ttk.Entry(register_frame, show="*")

    register_username_entry.grid(row=0, column=1, padx=10, pady=10)
    register_password_entry.grid(row=1, column=1, padx=10, pady=10)

    def register():
        username = register_username_entry.get()
        password = register_password_entry.get()
        users = load_users()
        if username and password:
            if username not in users:
                users[username] = encrypt_password(password)
                save_users(users)
                tk.messagebox.showinfo("Успешно", "Вы успешно зарегистрировались!")
            else:
                tk.messagebox.showerror("Ошибка", "Имя пользователя уже занято")
        else:
            tk.messagebox.showerror("Ошибка", "Оба поля обязательны для заполнения")

    register_button = ttk.Button(register_frame, text="Зарегистрироваться", command=register)
    register_button.grid(row=2, column=0, columnspan=2, pady=10)

    root.mainloop()

if __name__ == "__main__":
    show_login_register_window()
