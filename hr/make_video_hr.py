import subprocess, os, math, wave, sys
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, "_vid_hr"); os.makedirs(TMP, exist_ok=True)
W, H, FPS, S = 1280, 720, 24, 2
BG, FG, CY, BL, AM, GR = (5,28,44), (255,255,255), (0,169,244), (70,110,255), (224,161,0), (60,90,110)

# 장면: 내레이션, 화면 텍스트(줄별 단어, 강조는 * 접두), 라인아트 이름
SC = [
 ("AI 교육, 이제는 어느 회사나 합니다.", [["AI","교육,"],["이제는"],["*어느 회사나","합니다"]], "crowd"),
 ("그런데 교육 시간을 늘려도 적용률은 거의 오르지 않습니다. 상관은 영점 일육입니다.", [["교육 시간을","늘려도"],["*적용률은","그대로"],["상관","*0.16"]], "flat"),
 ("업무적용형은 칠십이 퍼센트, 강의형은 사십팔 퍼센트. 팀장 후원은 십오 포인트를 더합니다.", [["*설계가","가른다"],["업무적용형","*72%"],["강의형 48%"],["후원","*+15%p"]], "leader"),
 ("2027년 HR의 다섯 마일스톤. 기준선, 리더, 파일럿, 제도, 내재화.", [["2027"],["*HR의 다섯","마일스톤"],["기준선→리더→파일럿→","제도→내재화"]], "path"),
 ("HR은 교육 운영자에서 변화관리 파트너로. 리더와 제도와 예산을 함께 설계합니다.", [["운영자에서"],["*변화관리","파트너로"],["리더·제도·예산"]], "funnel"),
 ("예산은 인당 정액이 아니라, 적용 과제 단위로 배정하고, 분기 게이트를 통과해야 다음 예산을 풉니다.", [["인당 정액이","*아니라"],["적용 과제","*단위"],["분기","*게이트 통과"]], "price"),
 ("시간이 아니라 적용. 리더가 먼저, 제도가 함께. 이것이 2027년 HR의 AX입니다.", [["시간이 아니라","*적용"],["리더가","*먼저"],["제도가","*함께"]], "door"),
]

def tts(i, text):
    out = os.path.join(TMP, f"s{i}.wav")
    ps = ("Add-Type -AssemblyName System.Speech;$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
          "$s.SelectVoice('Microsoft Heami Desktop');$s.Rate=0;"
          f"$s.SetOutputToWaveFile('{out}');$s.Speak([IO.File]::ReadAllText('{out}.txt',[Text.Encoding]::UTF8));$s.Dispose()")
    open(out + ".txt", "w", encoding="utf-8").write(text)
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    with wave.open(out) as w: return out, w.getnframes() / w.getframerate()

wavs, durs = [], []
for i, (n, _, _) in enumerate(SC):
    p, d = tts(i, n); wavs.append(p); durs.append(d)
total_raw = sum(durs) + 0.5 * len(SC)
print("raw total", total_raw)
GAP = 0.5
# 1분 맞춤: 총 길이가 60초에 가깝게 장면 사이 여유 조정
GAP = max(0.3, (60 - sum(durs)) / len(SC))
GAP = min(GAP, 1.6)
scene_len = [d + GAP for d in durs]
print("durs", durs, "gap", GAP, "total", sum(scene_len))

# 오디오 합본
sr = None; pcm = b""
for i, p in enumerate(wavs):
    with wave.open(p) as w:
        sr = w.getframerate(); ch = w.getnchannels(); sw = w.getsampwidth()
        pcm += w.readframes(w.getnframes()) + b"\x00" * int(sr * ch * sw * GAP)
        # 정렬: 프레임 단위
        pcm = pcm[: len(pcm) - (len(pcm) % (ch * sw))]
with wave.open(os.path.join(TMP, "all.wav"), "wb") as w:
    w.setnchannels(ch); w.setsampwidth(sw); w.setframerate(sr); w.writeframes(pcm)

FB = os.path.join("C:\\Windows\\Fonts", "malgunbd.ttf")
FR = os.path.join("C:\\Windows\\Fonts", "malgun.ttf")
fbig = ImageFont.truetype(FB, 64 * S); fsm = ImageFont.truetype(FR, 22 * S); ftag = ImageFont.truetype(FB, 20 * S)

def ease(t): t = max(0, min(1, t)); return 1 - (1 - t) ** 3
def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def draw_poly(d, pts, p, col, wd=3):
    """pts 폴리라인을 진행도 p(0~1) 만큼만 그린다 (라인아트 드로잉)."""
    segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    L = [math.dist(a, b) for a, b in segs]; tot = sum(L) or 1; run = p * tot
    for (a, b), l in zip(segs, L):
        if run <= 0: break
        f = min(1, run / l) if l else 1
        e = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        d.line([(a[0] * S, a[1] * S), (e[0] * S, e[1] * S)], fill=col, width=wd * S)
        run -= l

def circ(d, c, r, p, col, wd=3):
    pts = [(c[0] + r * math.cos(2 * math.pi * k / 40), c[1] + r * math.sin(2 * math.pi * k / 40)) for k in range(41)]
    draw_poly(d, pts, p, col, wd)

def art(d, name, t, dur):
    p = lambda a, b: ease((t - a) / (b - a))
    if name == "crowd":
        for i in range(5):
            for j in range(3):
                x, y = 880 + i * 70, 220 + j * 120
                a = p(0.2 + (i + j) * 0.15, 1.0 + (i + j) * 0.15)
                circ(d, (x, y), 16, a, CY if (i, j) != (2, 1) else AM)
                draw_poly(d, [(x - 24, y + 62), (x - 20, y + 34), (x + 20, y + 34), (x + 24, y + 62)], a, CY if (i, j) != (2, 1) else AM, 2)
    elif name == "flat":
        draw_poly(d, [(860, 560), (860, 180)], p(0.1, .6), GR); draw_poly(d, [(860, 560), (1220, 560)], p(0.1, .6), GR)
        draw_poly(d, [(870, 540), (950, 500), (1020, 430), (1100, 340), (1200, 220)], p(0.6, 2.8), BL, 4)  # 지출
        draw_poly(d, [(870, 470), (1200, 458)], p(1.4, 3.2), AM, 4)  # 적용률
        d.text((1000 * S, 210 * S), "", font=fsm)
    elif name == "leader":
        circ(d, (1030, 270), 52, p(0.2, 1.4), CY, 4)
        draw_poly(d, [(930, 520), (940, 380), (1120, 380), (1130, 520)], p(0.8, 2.2), CY, 4)
        draw_poly(d, [(985, 215), (1000, 170), (1030, 205), (1060, 170), (1075, 215), (985, 215)], p(2.0, 3.2), AM, 4)
        for k in range(6):
            a = -math.pi / 2 + (k - 2.5) * 0.35
            draw_poly(d, [(1030 + 140 * math.cos(a), 270 + 140 * math.sin(a)), (1030 + 185 * math.cos(a), 270 + 185 * math.sin(a))], p(2.6, 3.6), AM, 3)
    elif name == "path":
        pts = [(870, 540), (950, 440), (1040, 470), (1110, 340), (1210, 230)]
        draw_poly(d, pts, p(0.3, 4.5), BL, 4)
        for i, c in enumerate(pts):
            circ(d, c, 14, p(0.6 + i * 0.7, 1.4 + i * 0.7), CY if i < 4 else AM, 4)
    elif name == "funnel":
        for i, (x, lab) in enumerate([(880, "리더"), (1010, "제도"), (1140, "예산")]):
            a = p(0.3 + i * 1.0, 1.3 + i * 1.0)
            draw_poly(d, [(x - 50, 250), (x + 50, 250), (x + 50, 400), (x - 50, 400), (x - 50, 250)], a, CY if i < 2 else AM, 4)
            if i < 2: draw_poly(d, [(x + 58, 325), (x + 72, 325)], p(1.2 + i, 1.8 + i), BL, 4)
            if a > 0.95: d.text(((x - 24) * S, 440 * S), lab, font=fsm, fill=FG)
    elif name == "price":
        draw_poly(d, [(880, 230), (1100, 230), (1160, 300), (1100, 370), (880, 370), (880, 230)], p(0.2, 1.6), CY, 4)
        circ(d, (1080, 300), 9, p(1.4, 2), CY, 3)
        draw_poly(d, [(880, 440), (1130, 440)], p(2.0, 3.0), AM, 4); draw_poly(d, [(880, 440), (1130, 440)], 0, AM)
        for i in range(3): draw_poly(d, [(880 + i * 90, 470), (900 + i * 90, 500)], p(3 + i * .3, 3.6 + i * .3), AM, 3)
    elif name == "door":
        draw_poly(d, [(950, 560), (950, 220), (1130, 220), (1130, 560)], p(0.2, 1.8), CY, 4)
        draw_poly(d, [(950, 560), (1130, 560)], p(1.0, 1.8), CY, 4)
        circ(d, (780 + 0, 440), 0, 0, CY)
        circ(d, (1040, 330), 12, p(2.2, 3), AM, 3)
        draw_poly(d, [(860, 560), (1040, 560)], p(1.2, 2.8), BL, 4)

fr_total = int(sum(scene_len) * FPS)
cmd = [FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
       "-i", os.path.join(TMP, "all.wav"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
       "-c:a", "aac", "-b:a", "160k", "-shortest", os.path.join(HERE, "ax2027_hr_summary.mp4")]
pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
bounds = [sum(scene_len[:i]) for i in range(len(SC))]
for f in range(fr_total):
    T = f / FPS
    si = max(i for i in range(len(SC)) if bounds[i] <= T)
    t = T - bounds[si]; dur = durs[si]
    im = Image.new("RGB", (W * S, H * S), BG); d = ImageDraw.Draw(im)
    # 배경 그리드 라인아트
    for k in range(0, W + 1, 80): d.line([(k * S, 0), (k * S, H * S)], fill=(10, 36, 54), width=S)
    # 진행바 + 태그
    d.rectangle([0, (H - 6) * S, int(W * S * T / sum(scene_len)), H * S], fill=BL)
    d.text((70 * S, 44 * S), f"AX 2027 · HR  |  {si + 1:02d}/{len(SC):02d}", font=ftag, fill=CY)
    # 키네틱 타이포
    words = [(li, w) for li, line in enumerate(SC[si][1]) for w in line]
    n = len(words); y0 = 150
    xcur = {}
    for idx, (li, w) in enumerate(words):
        acc = w.startswith("*"); w = w.lstrip("*")
        ts = 0.25 + (dur * 0.75) * idx / max(n, 1)
        a = ease((t - ts) / 0.55)
        if a <= 0: xcur.setdefault(li, 70); xcur[li] += d.textlength(w + " ", font=fbig) / S; continue
        x = xcur.setdefault(li, 70)
        y = y0 + li * 100 + (1 - a) * 46
        scale_pop = 1 + (0.08 * (1 - a) if acc else 0)
        col = lerp(BG, CY if acc else FG, a)
        d.text((x * S, y * S), w, font=fbig, fill=col)
        if acc and a > .9:
            wlen = d.textlength(w, font=fbig) / S
            e = ease((t - ts - 0.5) / 0.5)
            d.line([(x * S, (y + 78) * S), ((x + wlen * e) * S, (y + 78) * S)], fill=AM, width=3 * S)
        xcur[li] = x + d.textlength(w + " ", font=fbig) / S
    art(d, SC[si][2], t, dur)
    # 장면 전환 페이드
    fade = min(1, t / 0.3, (scene_len[si] - t) / 0.3)
    im = im.resize((W, H), Image.LANCZOS)
    if fade < 1: im = Image.blend(Image.new("RGB", (W, H), BG), im, max(0, fade))
    pr.stdin.write(im.tobytes())
pr.stdin.close(); pr.wait()
print("done")
