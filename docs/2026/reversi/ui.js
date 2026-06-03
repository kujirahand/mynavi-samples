// 画面描画を担当するモジュール
import { BLACK, WHITE, label } from "./rules.js";

export function renderBoard(boardEl, board, hints, onClick) {
  boardEl.innerHTML = "";
  for (let r = 0; r < 8; r++) for (let c = 0; c < 8; c++) {
    const b = document.createElement("button");
    const s = document.createElement("span");
    b.type = "button";
    b.className = "cell";
    s.className = "stone";
    if (hints.has(`${r},${c}`)) b.classList.add("hint");
    if (board[r][c] === BLACK) s.classList.add("black");
    if (board[r][c] === WHITE) s.classList.add("white");
    b.title = label(r, c);
    b.addEventListener("click", () => onClick(r, c));
    b.appendChild(s);
    boardEl.appendChild(b);
  }
}

export const setScore = (el, b, w) => el.textContent = `黒: ${b} / 白: ${w}`;
export const setStatus = (el, text) => el.textContent = text;
