// ゲーム進行を制御するメインスクリプト
import { BLACK, WHITE, newBoard, opponent, validMoves, applyMove, countStone, label } from "./rules.js";
import { renderBoard, setScore, setStatus } from "./ui.js";
import init, { choose_move } from "./pkg/web_app.js";

const boardEl = document.getElementById("board");
const statusEl = document.getElementById("status");
const scoreEl = document.getElementById("score");
const restartBtn = document.getElementById("restart");
let board = newBoard(), turn = BLACK, done = false;

const flatBoard = () => Uint8Array.from(board.flat());

function redraw() {
  const hints = new Set(validMoves(board, turn).map(([r, c]) => `${r},${c}`));
  renderBoard(boardEl, board, hints, onCellClick);
  setScore(scoreEl, countStone(board, BLACK), countStone(board, WHITE));
}

function finish() {
  const b = countStone(board, BLACK), w = countStone(board, WHITE);
  done = true; redraw();
  const result = b > w ? "黒の勝ち" : w > b ? "白の勝ち" : "引き分け";
  setStatus(statusEl, result);
}

function step() {
  const m1 = validMoves(board, turn), m2 = validMoves(board, opponent(turn));
  if (!m1.length && !m2.length) return finish();
  if (!m1.length) { setStatus(statusEl, "パス"); turn = opponent(turn); redraw(); return step(); }
  if (turn === BLACK) { setStatus(statusEl, `あなたの手番: ${m1.map(([r,c]) => label(r,c)).join(", ")}`); return redraw(); }
  setStatus(statusEl, "AIが思考中..."); redraw();
  setTimeout(() => {
    const idx = choose_move(flatBoard(), WHITE); if (idx < 0) return;
    applyMove(board, Math.floor(idx / 8), idx % 8, WHITE);
    turn = BLACK; step();
  }, 200);
}

function onCellClick(r, c) {
  if (done || turn !== BLACK) return;
  if (!applyMove(board, r, c, BLACK)) return;
  turn = WHITE; step();
}

restartBtn.addEventListener("click", () => { board = newBoard(); turn = BLACK; done = false; step(); });
init().then(step);
