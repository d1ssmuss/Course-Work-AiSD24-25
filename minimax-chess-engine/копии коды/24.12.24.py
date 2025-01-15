import sys
import pygame as p
import ChessEngine
import ChienKoNgu
import math

WIDTH = 850
HEIGHT = 850
MOVE_LOG_PANEL_WIDTH = 290
MOVE_LOG_PANEL_HEIGHT = HEIGHT
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 240
IMAGES = {}

def load_images():
    pieces = ["wp", "wR", "wN", "wB", "wQ", "wK", "bp", "bR", "bN", "bB", "bQ", "bK"]
    for piece in pieces:
        IMAGES[piece] = p.transform.smoothscale(p.image.load("images/" + piece + ".png").convert_alpha(), (SQ_SIZE, SQ_SIZE))

def main():
    p.init()
    screen = p.display.set_mode((WIDTH + MOVE_LOG_PANEL_WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
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
                    scroll_offset += 1

        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False

        ''' AI move finder '''
        if not gameOver and not humanTurn:
            AIMove = ChienKoNgu.findBestMoveMinimax(gs, validMoves)
            #AIMove = ChienKoNgu.findRandomMove(validMoves)
            if AIMove is None:   #when begin the game
                AIMove = ChienKoNgu.findRandomMove(validMoves)
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
    moveLogRect = p.Rect(WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
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

def show_login_window():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    font = p.font.SysFont("Times New Roman", 24)
    input_box_username = p.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 32)
    input_box_password = p.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 20, 200, 32)
    color_inactive = p.Color('lightskyblue3')
    color_active = p.Color('dodgerblue2')
    color_username = color_inactive
    color_password = color_inactive
    active_username = False
    active_password = False
    username = ''
    password = ''
    login_successful = False
    error_message = ''

    while not login_successful:
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                return False
            if event.type == p.MOUSEBUTTONDOWN:
                if input_box_username.collidepoint(event.pos):
                    active_username = not active_username
                    active_password = False
                    color_username = color_active if active_username else color_inactive
                    color_password = color_inactive
                elif input_box_password.collidepoint(event.pos):
                    active_password = not active_password
                    active_username = False
                    color_password = color_active if active_password else color_inactive
                    color_username = color_inactive
                else:
                    active_username = False
                    active_password = False
                    color_username = color_inactive
                    color_password = color_inactive
            if event.type == p.KEYDOWN:
                if active_username:
                    if event.key == p.K_RETURN:
                        active_username = False
                        active_password = True
                        color_username = color_inactive
                        color_password = color_active
                    elif event.key == p.K_BACKSPACE:
                        username = username[:-1]
                    else:
                        username += event.unicode
                elif active_password:
                    if event.key == p.K_RETURN:
                        if username and password:
                            if username == "admin" and password == "admin":
                                login_successful = True
                            else:
                                error_message = "Неверное имя пользователя или пароль"
                        else:
                            error_message = "Оба поля обязательны для заполнения"
                    elif event.key == p.K_BACKSPACE:
                        password = password[:-1]
                    else:
                        password += event.unicode

        screen.fill((30, 30, 30))
        txt_surface_username = font.render(username, True, color_username)
        txt_surface_password = font.render('*' * len(password), True, color_password)
        input_box_username.w = max(200, txt_surface_username.get_width()+10)
        input_box_password.w = max(200, txt_surface_password.get_width()+10)
        screen.blit(txt_surface_username, (input_box_username.x+5, input_box_username.y))
        screen.blit(txt_surface_password, (input_box_password.x+5, input_box_password.y))
        p.draw.rect(screen, color_username, input_box_username, 2)
        p.draw.rect(screen, color_password, input_box_password, 2)

        if error_message:
            error_font = p.font.SysFont("Times New Roman", 20)
            error_text = error_font.render(error_message, True, p.Color("red"))
            screen.blit(error_text, (WIDTH // 2 - error_text.get_width() // 2, HEIGHT // 2 + 100))

        p.display.flip()
        clock.tick(30)

    return True

if __name__ == "__main__":
    if show_login_window():
        main()
