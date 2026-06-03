// リバーシの基本ルールと盤面操作
export const SIZE = 8;
export const EMPTY = 0, BLACK = 1, WHITE = 2;
const DIRS = [[-1,-1],[-1,0],[-1,1],[0,-1],[0,1],[1,-1],[1,0],[1,1]];

export const newBoard = () => {
  const b = Array.from({ length: SIZE }, () => Array(SIZE).fill(EMPTY));
  b[3][3] = WHITE; b[3][4] = BLACK; b[4][3] = BLACK; b[4][4] = WHITE;
  return b;
};

export const opponent = (p) => (p === BLACK ? WHITE : BLACK);
export const label = (r, c) => `${String.fromCharCode(65 + c)}${r + 1}`;
const inRange = (r, c) => r >= 0 && r < SIZE && c >= 0 && c < SIZE;

function flipsInDir(board, r, c, dr, dc, p) {
  const out = []; let y = r + dr, x = c + dc;
  while (inRange(y, x)) {
    const v = board[y][x];
    if (v === opponent(p)) out.push([y, x]);
    else if (v === p) return out.length ? out : [];
    else return [];
    y += dr; x += dc;
  }
  return [];
}

export function collectFlips(board, r, c, p) {
  if (board[r][c] !== EMPTY) return [];
  return DIRS.flatMap(([dr, dc]) => flipsInDir(board, r, c, dr, dc, p));
}

export function validMoves(board, p) {
  const out = [];
  for (let r = 0; r < SIZE; r++) for (let c = 0; c < SIZE; c++) {
    if (collectFlips(board, r, c, p).length) out.push([r, c]);
  }
  return out;
}

export function applyMove(board, r, c, p) {
  const flips = collectFlips(board, r, c, p);
  if (!flips.length) return false;
  board[r][c] = p; flips.forEach(([y, x]) => board[y][x] = p);
  return true;
}

export const countStone = (board, s) => board.flat().filter(v => v === s).length;
