// Load pieces data
// Note: In a real browser environment, we'd use a module or a separate script tag.
// Since we are writing these as separate files, we'll ensure they are loaded in HTML.

class ChessGame {
    constructor() {
        this.game = new Chess();
        this.boardElement = document.getElementById('board');
        this.statusElement = document.getElementById('status');
        this.historyElement = document.getElementById('history');
        this.newGameBtn = document.getElementById('new-game-btn');
        
        this.selectedSquare = null;
        this.lastMove = null;

        this.init();
    }

    init() {
        this.renderBoard();
        this.updateStatus();
        
        this.newGameBtn.addEventListener('click', () => {
            this.game.reset();
            this.lastMove = null;
            this.renderBoard();
            this.updateStatus();
            this.updateHistory();
        });

        // Drag and drop are complex in pure JS, so we'll implement a 
        // "Click-to-Select, Click-to-Move" system for maximum reliability
        // and cleaner code.
    }

    renderBoard() {
        this.boardElement.innerHTML = '';
        const boardState = this.game.board();

        for (let r = 0; r < 8; r++) {
            for (let c = 0; c < 8; c++) {
                const square = document.createElement('div');
                const squareName = String.fromCharCode(97 + c) + (8 - r);
                
                square.classList.add('square');
                square.classList.add((r + c) % 2 === 0 ? 'light' : 'dark');
                square.dataset.square = squareName;

                const piece = boardState[r][c];
                if (piece) {
                    const pieceElement = document.createElement('div');
                    pieceElement.classList.add('piece');
                    pieceElement.innerHTML = PIECE_SVGS[piece.color + piece.type];
                    square.appendChild(pieceElement);
                }

                if (this.lastMove && (this.lastMove.from === squareName || this.lastMove.to === squareName)) {
                    square.classList.add('highlight-last-move');
                }

                square.addEventListener('click', () => this.handleSquareClick(squareName));
                this.boardElement.appendChild(square);
            }
        }
    }

    handleSquareClick(squareName) {
        if (this.selectedSquare === null) {
            // First click: select a piece
            const piece = this.game.get(squareName);
            if (piece && piece.color === this.game.turn()) {
                this.selectedSquare = squareName;
                this.highlightLegalMoves(squareName);
            }
        } else {
            // Second click: attempt to move
            const move = this.game.move({
                from: this.selectedSquare,
                to: squareName,
                promotion: 'q' // always promote to queen for simplicity
            });

            if (move) {
                this.lastMove = { from: this.selectedSquare, to: squareName };
                this.renderBoard();
                this.updateStatus();
                this.updateHistory();
            }

            this.selectedSquare = null;
            this.clearHighlights();
        }
    }

    highlightLegalMoves(squareName) {
        this.clearHighlights();
        const moves = this.game.moves({ square: squareName, verbose: true });
        
        moves.forEach(move => {
            const square = this.boardElement.querySelector(`[data-square="${move.to}"]`);
            const dot = document.createElement('div');
            dot.classList.add('legal-dot');
            square.appendChild(dot);
        });
    }

    clearHighlights() {
        const dots = this.boardElement.querySelectorAll('.legal-dot');
        dots.forEach(dot => dot.remove());
    }

    updateStatus() {
        let status = '';
        const turn = this.game.turn() === 'w' ? 'White' : 'Black';

        if (this.game.in_checkmate()) {
            status = `Game Over! ${turn === 'White' ? 'Black' : 'White'} wins by Checkmate!`;
        } else if (this.game.in_draw()) {
            status = 'Game Over! Draw';
        } else {
            status = `${turn}'s Turn`;
            if (this.game.in_check()) {
                status += ' (CHECK!)';
            }
        }

        this.statusElement.innerText = status;
    }

    updateHistory() {
        this.historyElement.innerHTML = '';
        const history = this.game.history();
        
        for (let i = 0; i < history.length; i += 2) {
            const moveDiv = document.createElement('div');
            moveDiv.classList.add('history-move');
            
            const moveNum = document.createElement('div');
            moveNum.innerText = `${Math.floor(i/2) + 1}.`;
            
            const whiteMove = document.createElement('div');
            whiteMove.innerText = history[i];
            
            const blackMove = document.createElement('div');
            blackMove.innerText = history[i+1] || '';
            
            moveDiv.appendChild(moveNum);
            moveDiv.appendChild(whiteMove);
            moveDiv.appendChild(blackMove);
            this.historyElement.appendChild(moveDiv);
        }
        this.historyElement.scrollTop = this.historyElement.scrollHeight;
    }
}

// Initialize the game when the window loads
window.onload = () => {
    // To make this work as a standalone HTML file for the user, 
    // we'll assume pieces.js is loaded first.
    new ChessGame();
};
