import json
import os
import sys
import urllib.error
import urllib.request
ENV_URL = os.environ.get("MAKEFUN_ENV_URL") or sys.exit("MAKEFUN_ENV_URL is not set")
VAL = (0, 100, 320, 330, 500, 900, 0)
PST = (
    "aaaaaaaakkkkkkkkcceggeccbbcffcbbaaaeeaaab98aa89bbcc66ccbaaaaaaaa",
    "0244442026aaaa624acddca44bdeedb44adeeda44bcddcb426abba6202444420",
    "688888868aaaaaa88abccba88bbccbb88acccca88cccccc88baaaab868888886",
    "aaaaaaaabccccccb9aaaaaa99aaaaaa99aaaaaa99aaaaaa99aaaaaa9aaabbaaa",
    "688998868aaaaaa88abbbba89abbbba9aabbbba98bbbbba88abaaaa868899886",
    "422002244220022442200224422002246442244686666668eeaaaaeeegcaacge",
)
TW = []
TB = []
for _c in range(7):
    _w = [0] * 128
    _b = [0] * 128
    for _s in range(128):
        if not _s & 0x88:
            _f = _s & 7
            _r = _s >> 4
            _w[_s] = VAL[_c] + 5 * (int(PST[_c - 1][_f + 8 * (7 - _r)], 36) - 10) if _c else 0
            _b[_s] = -(VAL[_c] + 5 * (int(PST[_c - 1][_f + 8 * _r], 36) - 10)) if _c else 0
    TW.append(_w)
    TB.append(_b)
KNIGHT_D = (31, 33, 14, 18, -31, -33, -14, -18)
KING_D = (1, 15, 16, 17, -1, -15, -16, -17)
ROOK_D = (1, 16, -1, -16)
BISHOP_D = (15, 17, -15, -17)
PROMO = "  nbrq"
def post(path, body):
    req = urllib.request.Request(
        ENV_URL + path,
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        sys.exit(f"{path}: HTTP {e.code} {e.read().decode(errors='replace')}")
def sq_name(s):
    return "abcdefgh"[s & 7] + str((s >> 4) + 1)
def sq_num(name):
    return "abcdefgh".index(name[0]) + (int(name[1]) - 1) * 16
b = [0] * 128
stm = 1
castling = 0
ep = -1
score = 0
wk = 4
bk = 116
stack = []
def piece_val(p, s):
    return TW[p][s] if p > 0 else TB[-p][s]
def setup(fen):
    global stm, castling, ep, score, wk, bk
    del stack[:]
    parts = fen.split()
    for i in range(128):
        b[i] = 0
    score = 0
    rank = 7
    file = 0
    for c in parts[0]:
        if c == "/":
            rank -= 1
            file = 0
        elif c.isdigit():
            file += int(c)
        else:
            p = "PNBRQK".index(c.upper()) + 1
            if c.islower():
                p = -p
            s = file + rank * 16
            b[s] = p
            score += piece_val(p, s)
            if p == 6:
                wk = s
            elif p == -6:
                bk = s
            file += 1
    stm = 1 if parts[1] == "w" else -1
    castling = 0
    if len(parts) > 2:
        for c in parts[2]:
            castling |= {"K": 1, "Q": 2, "k": 4, "q": 8}.get(c, 0)
    ep = sq_num(parts[3]) if len(parts) > 3 and parts[3] != "-" else -1
def attacked(s, by):
    d = -16 if by > 0 else 16
    for t in (s + d - 1, s + d + 1):
        if not t & 0x88 and b[t] == by:
            return True
    for o in KNIGHT_D:
        t = s + o
        if not t & 0x88 and b[t] == 2 * by:
            return True
    for o in KING_D:
        t = s + o
        if not t & 0x88 and b[t] == 6 * by:
            return True
    for o in ROOK_D:
        t = s + o
        while not t & 0x88:
            p = b[t]
            if p:
                if p == 4 * by or p == 5 * by:
                    return True
                break
            t += o
    for o in BISHOP_D:
        t = s + o
        while not t & 0x88:
            p = b[t]
            if p:
                if p == 3 * by or p == 5 * by:
                    return True
                break
            t += o
    return False
def king_sq(side):
    return wk if side > 0 else bk
def gen_moves(captures_only=False):
    moves = []
    for f in range(128):
        p = b[f]
        if not p or (p > 0) != (stm > 0):
            continue
        ap = abs(p)
        if ap == 1:
            step = 16 if p > 0 else -16
            start_rank = 1 if p > 0 else 6
            last_rank = 7 if p > 0 else 0
            t = f + step
            if not t & 0x88 and not b[t] and not captures_only:
                if (t >> 4) == last_rank:
                    for promo in (5, 2):
                        moves.append(f | t << 7 | promo << 14)
                else:
                    moves.append(f | t << 7)
                    if (f >> 4) == start_rank:
                        t2 = f + step * 2
                        if not b[t2]:
                            moves.append(f | t2 << 7)
            for o in (step - 1, step + 1):
                t = f + o
                if t & 0x88:
                    continue
                q = b[t]
                if q and (q > 0) != (p > 0):
                    if (t >> 4) == last_rank:
                        for promo in (5, 2):
                            moves.append(f | t << 7 | promo << 14)
                    else:
                        moves.append(f | t << 7)
                elif t == ep and ep >= 0:
                    moves.append(f | t << 7)
        elif ap == 2 or ap == 6:
            for o in KNIGHT_D if ap == 2 else KING_D:
                t = f + o
                if t & 0x88:
                    continue
                q = b[t]
                if not q:
                    if not captures_only:
                        moves.append(f | t << 7)
                elif (q > 0) != (p > 0):
                    moves.append(f | t << 7)
        else:
            for o in (ROOK_D if ap == 4 else BISHOP_D if ap == 3 else ROOK_D + BISHOP_D):
                t = f + o
                while not t & 0x88:
                    q = b[t]
                    if not q:
                        if not captures_only:
                            moves.append(f | t << 7)
                    else:
                        if (q > 0) != (p > 0):
                            moves.append(f | t << 7)
                        break
                    t += o
    if not captures_only:
        if stm > 0:
            if castling & 1 and not b[5] and not b[6] and b[4] == 6 and b[7] == 4 \
                    and not attacked(4, -1) and not attacked(5, -1) and not attacked(6, -1):
                moves.append(4 | 6 << 7)
            if castling & 2 and not b[3] and not b[2] and not b[1] and b[4] == 6 and b[0] == 4 \
                    and not attacked(4, -1) and not attacked(3, -1) and not attacked(2, -1):
                moves.append(4 | 2 << 7)
        else:
            if castling & 4 and not b[117] and not b[118] and b[116] == -6 and b[119] == -4 \
                    and not attacked(116, 1) and not attacked(117, 1) and not attacked(118, 1):
                moves.append(116 | 118 << 7)
            if castling & 8 and not b[115] and not b[114] and not b[113] and b[116] == -6 and b[112] == -4 \
                    and not attacked(116, 1) and not attacked(115, 1) and not attacked(114, 1):
                moves.append(116 | 114 << 7)
    return moves
def make(m):
    global castling, ep, score, stm, wk, bk
    f = m & 127
    t = (m >> 7) & 127
    promo = (m >> 14) & 7
    p = b[f]
    cap = b[t]
    cap_sq = t
    if abs(p) == 1 and t == ep and not cap:
        cap_sq = t - 16 if p > 0 else t + 16
        cap = b[cap_sq]
    stack.append((m, cap, cap_sq, castling, ep))
    score -= piece_val(p, f)
    if cap:
        score -= piece_val(cap, cap_sq)
        b[cap_sq] = 0
    b[f] = 0
    if abs(p) == 6 and abs(t - f) == 2:
        rf = 7 if t > f else 0
        rt = 5 if t > f else 3
        if p < 0:
            rf += 112
            rt += 112
        r = b[rf]
        score -= piece_val(r, rf)
        b[rf] = 0
        b[rt] = r
        score += piece_val(r, rt)
    np = (promo if p > 0 else -promo) if promo else p
    b[t] = np
    score += piece_val(np, t)
    if abs(p) == 6:
        if p > 0:
            wk = t
        else:
            bk = t
    if abs(p) == 6:
        castling &= ~(3 if p > 0 else 12)
    for s, bit in ((0, 2), (7, 1), (112, 8), (119, 4)):
        if f == s or t == s:
            castling &= ~bit
    ep = (f + t) // 2 if abs(p) == 1 and abs(t - f) == 32 else -1
    stm = -stm
    return cap
def unmake():
    global castling, ep, score, stm, wk, bk
    m, cap, cap_sq, old_castling, old_ep = stack.pop()
    f = m & 127
    t = (m >> 7) & 127
    promo = (m >> 14) & 7
    p = b[t]
    if abs(p) == 6:
        if p > 0:
            wk = f
        else:
            bk = f
    score -= piece_val(p, t)
    b[t] = 0
    if abs(p) == 6 and abs(t - f) == 2:
        rf = 7 if t > f else 0
        rt = 5 if t > f else 3
        if p < 0:
            rf += 112
            rt += 112
        r = b[rt]
        score -= piece_val(r, rt)
        b[rt] = 0
        b[rf] = r
        score += piece_val(r, rf)
    orig = promo and (1 if p > 0 else -1) or p
    b[f] = orig
    score += piece_val(orig, f)
    if cap:
        b[cap_sq] = cap
        score += piece_val(cap, cap_sq)
    castling = old_castling
    ep = old_ep
    stm = -stm
NODES = 0
BUDGET = 250000
MATE = 100000
class Abort(Exception):
    pass
def legal_moves(captures_only=False):
    out = []
    for m in gen_moves(captures_only):
        make(m)
        safe = not attacked(king_sq(-stm), stm)
        unmake()
        if safe:
            out.append(m)
    return out
def order(moves):
    def key(m):
        f = m & 127
        t = (m >> 7) & 127
        cap = b[t]
        if not cap and abs(b[f]) == 1 and t == ep:
            cap = 1 if b[f] > 0 else -1
        s = 0
        if cap:
            s = 10 * VAL[abs(cap)] - VAL[abs(b[f])] // 10
        if ply < 128 and m in killer[ply]:
            s += 5000
        return -s
    return sorted(moves, key=key)
killer = [[0, 0] for _ in range(128)]
ply = 0
def quiesce(a, beta):
    global NODES
    NODES += 1
    if NODES > BUDGET:
        raise Abort
    stand = score if stm > 0 else -score
    if stand >= beta:
        return beta
    if stand > a:
        a = stand
    for m in order(gen_moves(captures_only=True)):
        cap = make(m)
        if cap and abs(cap) == 6:
            unmake()
            return MATE
        s = -quiesce(-beta, -a)
        unmake()
        if s >= beta:
            return beta
        if s > a:
            a = s
    return a
def search(d, a, beta):
    global NODES, ply
    NODES += 1
    if NODES > BUDGET:
        raise Abort
    if d <= 0:
        return quiesce(a, beta)
    moves = order(gen_moves())
    if not moves:
        return -MATE + ply if attacked(king_sq(stm), -stm) else 0
    best = -MATE
    for m in moves:
        t = (m >> 7) & 127
        cap0 = b[t] or (1 if abs(b[m & 127]) == 1 and t == ep else 0)
        cap = make(m)
        if cap and abs(cap) == 6:
            unmake()
            return MATE - ply
        ply += 1
        s = -search(d - 1, -beta, -a)
        ply -= 1
        unmake()
        if s > best:
            best = s
        if s > a:
            a = s
            if a >= beta:
                if not cap0 and m != killer[ply][0]:
                    killer[ply][1] = killer[ply][0]
                    killer[ply][0] = m
                break
    return best
def uci(m):
    s = sq_name(m & 127) + sq_name((m >> 7) & 127)
    promo = (m >> 14) & 7
    return s + (PROMO[promo] if promo else "")
def choose(fen, legal_uci):
    global NODES, stm, ply, killer
    setup(fen)
    ply = 0
    killer = [[0, 0] for _ in range(128)]
    root = legal_moves()
    by_uci = {uci(m): m for m in root}
    legal = [by_uci[u] for u in legal_uci if u in by_uci]
    if not legal:
        return legal_uci[0] if legal_uci else None
    if len(legal) == 1:
        return uci(legal[0])
    best = legal[0]
    depth = 1
    while depth <= 64:
        NODES = 0
        try:
            scored = []
            a = -MATE
            for m in order(legal):
                make(m)
                s = -search(depth - 1, -MATE, -a)
                unmake()
                scored.append((s, m))
                if s > a:
                    a = s
                    best = m
            scored.sort(key=lambda x: -x[0])
            best = scored[0][1]
            legal = [m for _, m in scored]
            depth += 1
        except Abort:
            break
    return uci(best)
if __name__ == "__main__":
    while True:
        g = post("/game", {})
        if g["status"] == "done":
            break
        while g["status"] == "your_move":
            move = choose(g["fen"], g["legal_moves"])
            g = post("/move", {"game": g["game"], "move": move})
        print(f"game {g['game']}: {g['outcome']} by {g['reason']}", file=sys.stderr)
    print(f"done: {g.get('wins')} won, {g.get('draws')} drawn, {g.get('losses')} lost", file=sys.stderr)
