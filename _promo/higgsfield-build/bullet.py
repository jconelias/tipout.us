# Higgsfield "bullet time" reel: Kling 3.0 clip + real TipOut graphics (engine.py from content-2wk/_build).
# Usage: python3 bullet.py <clip.mp4> <name>   Pieces copied from ai-reels/_build/reels.py so it runs without opencv.
import sys, os, subprocess
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, '../../content-2wk/_build'))
from engine import *

END = 2.4

class Clip:
    """Streams frames of an AI clip (scaled to 1080x1920 @30fps) starting at `start` seconds."""
    def __init__(self, path, start, dur):
        self.path, self.start, self.dur = path, start, dur
        self.proc = None; self.i = -1; self.buf = None
    def _open(self):
        self.proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', str(self.start), '-t', str(self.dur + 0.3), '-i', self.path,
                                      '-vf', f'scale={W}:{H}:flags=lanczos,fps={FPS}', '-pix_fmt', 'bgra', '-f', 'rawvideo', '-'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.i = -1
    def frame(self, lt):
        idx = int(round(lt * FPS))
        if self.proc is None or idx < self.i: self._open()
        while self.i < idx:
            b = self.proc.stdout.read(W * H * 4)
            if len(b) < W * H * 4: break
            self.buf = bytearray(b); self.i += 1
        return self.buf

def scrim(c, h=760, a=0.6):
    g = cairo.LinearGradient(0, 0, 0, h); g.add_color_stop_rgba(0, 0, 0, 0, a); g.add_color_stop_rgba(1, 0, 0, 0, 0)
    c.rectangle(0, 0, W, h); c.set_source(g); c.fill()

def ai_tag(c):
    s = 'AI-GENERATED SCENE'; w = tw(c, s, 8, 22, 2) + 2*22*0.85
    label(c, s, 56 + w/2, 120, 22, wa(INK, 0.55), WHITE, 1, 2, 8)

def vseg(path, start, dur, caps=(), punch=False):
    """caps: list of (t0, lines, size)."""
    clip = Clip(path, start, dur)
    def fn(c, t, d):
        buf = clip.frame(t)
        s = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, W, H)
        c.set_source_surface(s, 0, 0); c.paint()
        scrim(c); ai_tag(c)
        cur = [cp for cp in caps if t >= cp[0]]
        if cur:
            t0, lines, sz = cur[-1]
            pop_lines(c, lines, W/2, 360, sz, t, t0)
    seg = Seg(dur, fn, punch=punch); seg.clip = clip
    return seg

def g_logged(c, t, d):
    bg(c, 'dark', t); dots_grid(c, t, WHITE, 0.04)
    pop_lines(c, ['Your whole shift,', '*logged.*'], W/2, 260, 84, t)
    phone(c, W/2, 1150, 1.38, shift_screen(reveal=eo(prog(t, 0.1, 0.9))), t)
    if t > 0.9: check(c, W/2 + 300, 600, 62, G, INK, eo(prog(t, 0.9, 1.25)))

def g_week(c, t, d):
    bg(c, 'dark', t)
    pop_lines(c, ['Your money for the week,', '*right there.*'], W/2, 270, 76, t)
    rp = eo(prog(t, 0.1, 1.6))
    phone(c, W/2, 1180, 1.32, home_screen(amount=1592.75 + 389*rp, ring_p=0.8 + 0.2*rp, hourly=f'${35.23*(0.97 + 0.03*rp):.2f}/hr'), t)
    if 0.1 < t < 1.4:
        lt = t - 0.1; label(c, '+$389 Saturday', W/2 + 270, 1220 - 160*eo(lt/1.3), 34, YEL, INK, 1 - lt/1.3, 0)

def end_coming(c, t, d):
    bg(c, 'deep', t); dots_grid(c, t, WHITE, 0.05)
    pig(c, W/2, 430, 260*back(prog(t, 0.05, 0.5)) + 0.01, WHITE)
    s = back(prog(t, 0, 0.45))
    c.save(); c.translate(W/2, 800); c.scale(s, s); text(c, 'COMING', 0, 40, 110, 9, WHITE); c.restore()
    s = back(prog(t, 0.1, 0.55))
    c.save(); c.translate(W/2, 960); c.scale(max(s, .01), max(s, .01)); text(c, 'MONDAY', 0, 70, 200, 9, G); c.restore()
    a = prog(t, 0.35, 0.7)
    text(c, 'TipOut hits the App Store', W/2, 1180, 46, 8, wa(MINT, a))
    label(c, 'MON · OCT 26', W/2, 1240, 40, WHITE, INK, a)
    text(c, '@tipout_us', W/2, 1440, 38, 8, wa(WHITE, a*0.8))

TAGS = {'coming-monday': end_coming, 'app-store': end_now()}

CAPS = [(0.0, ['When the tray goes down', 'but the *tips don’t*'], 78),
        (2.6, ['Every.', '*Single.*', 'Dollar.'], 120),
        (7.6, ['Tracked in *TipOut.*'], 96)]

def reel(path):
    return [vseg(path, 0.0, 10.0, CAPS), Seg(2.0, g_logged), Seg(2.6, g_week)]

def audio(segs, video, out):
    """The AI clip's own sound under its segment, a short tail fade, silence under the graphics."""
    clip = segs[0].clip
    fc = (f'[1:a]atrim=0:{clip.dur},asetpts=PTS-STARTPTS,afade=t=out:st={clip.dur - 0.4}:d=0.4,apad,'
          f'atrim=0:{sum(s.dur for s in segs)}[aout]')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-i', clip.path, '-filter_complex', fc, '-map', '0:v', '-map', '[aout]',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out], check=True)

if __name__ == '__main__':
    path, name = sys.argv[1], sys.argv[2]
    out_dir = os.environ.get('OUT', os.path.join(BASE, '..'))
    for tag, end in TAGS.items():
        segs = reel(path) + [Seg(END, end)]
        tmp = f'{os.environ.get("TMPDIR", "/tmp")}/_{name}_{tag}.mp4'; fn = f'{out_dir}/TipOut-{name}_{tag}.mp4'
        tot = render(segs, tmp); audio(segs, tmp, fn); os.remove(tmp)
        print(fn, round(tot, 1), 's')
