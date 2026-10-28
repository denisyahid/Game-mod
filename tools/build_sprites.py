#!/usr/bin/env python3
"""
Bangun sprite strip bersih untuk game Naruto vs Sasuke (HTML).

Sumber sprite (referensi internet):
  - Strip per-aksi gaya Jump Ultimate Stars (JUS) + atlas JSON
    dari repo GitHub Omololu457/multiverse-smash
    (Naruto KCM: naruto_kcm_*.png, Sasuke Taka: sasuke_*.png,
     atlas: tools/atlases/naruto.json & sasuke.json)
  - Background Lembah Akhir (Valley of the End) + shuriken
    dari repo GitHub mission-coding/Naruto-Vs-Sasuke (pics/bg.png, pics/shur.png)
  - Referensi sheet orisinal: Sprite Database (spritedatabase.net)
    "Naruto Shippuden: Naruto vs. Sasuke" (DS) rip oleh Neimad,
    dan The Spriters Resource "Jump Ultimate Stars".

Script ini:
  1. Memotong frame berdasarkan rect atlas (mode A),
     berdasarkan kolom alpha kosong antar-frame (mode C),
     atau grid tetap (mode F).
  2. Men-trim tiap frame ke bounding-box alpha, lalu mengemas ulang
     menjadi strip horizontal seragam (rata bawah, tengah horizontal).
  3. Menulis assets/sprites/manifest.json untuk dipakai game.

Letakkan file mentah di /tmp/multi2 (strip multiverse-smash),
/tmp/naruto_atlas.json, /tmp/sasuke_atlas.json, /tmp/ref1/pics (bg+shuriken),
lalu jalankan:  python3 tools/build_sprites.py
"""
import json, os, shutil
import numpy as np
from PIL import Image

RAW = "/tmp/multi2"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "sprites")
OUT = os.path.abspath(OUT)

naruto_atlas = json.load(open("/tmp/naruto_atlas.json"))
sasuke_atlas = json.load(open("/tmp/sasuke_atlas.json"))


def trim(im):
    bbox = im.getchannel("A").getbbox()
    return im.crop(bbox) if bbox else im


def atlas_frames(atlas, action):
    spec = atlas["actions"][action]
    sheet = Image.open(os.path.join(RAW, os.path.basename(spec["sheet"]))).convert("RGBA")
    return [sheet.crop((r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"])) for r in spec["rects"]]


def column_groups(path, y0=0, gap=6):
    im = Image.open(path).convert("RGBA")
    if y0:
        im = im.crop((0, y0, im.width, im.height))
    a = np.array(im)[:, :, 3] > 8
    col = a.any(axis=0)
    res, s, empty, last = [], None, 0, 0
    for x, v in enumerate(col):
        if v:
            if s is None:
                s = x
            empty, last = 0, x
        elif s is not None:
            empty += 1
            if empty >= gap:
                res.append((s, last)); s = None; empty = 0
    if s is not None:
        res.append((s, last))
    frames = []
    for x0, x1 in res:
        frames.append(im.crop((x0, 0, x1 + 1, im.height)))
    return frames


def fixed_frames(path, fw, fh, n, y0=0):
    im = Image.open(path).convert("RGBA")
    return [im.crop((i * fw, y0, i * fw + fw, y0 + fh)) for i in range(n)]


def repack(frames, out_path):
    frames = [trim(f) for f in frames]
    frames = [f for f in frames if f.width >= 4 and f.height >= 4]
    fw = max(f.width for f in frames)
    fh = max(f.height for f in frames)
    strip = Image.new("RGBA", (fw * len(frames), fh), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.alpha_composite(f, (i * fw + (fw - f.width) // 2, fh - f.height))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    strip.save(out_path)
    return {"file": os.path.relpath(out_path, OUT).replace("\\", "/"),
            "frames": len(frames), "fw": fw, "fh": fh}


manifest = {"naruto": {}, "sasuke": {}, "fx": {}}

def A(char, atlas, action, name=None, extra_action=None, clear_top=0):
    frames = atlas_frames(atlas, action)
    if extra_action:  # gabung dua aksi atlas (mis. jump + fall)
        frames += atlas_frames(atlas, extra_action)
    if clear_top:  # hapus artefak teks di baris teratas sheet asli
        cleaned = []
        for f in frames:
            arr = np.array(f); arr[:clear_top, :, 3] = 0
            cleaned.append(Image.fromarray(arr))
        frames = cleaned
    manifest[char][name or action] = repack(frames, f"{OUT}/{char}/{name or action}.png")

def C(char, filename, name, y0=0, gap=6, select=None, min_h=0):
    frames = column_groups(os.path.join(RAW, filename), y0=y0, gap=gap)
    frames = [f for f in frames if trim(f).height >= min_h] if min_h else frames
    if select is not None:
        frames = [frames[i] for i in select]
    manifest[char][name] = repack(frames, f"{OUT}/{char}/{name}.png")

def F(char, filename, name, fw, fh, n, y0=0):
    manifest[char][name] = repack(fixed_frames(os.path.join(RAW, filename), fw, fh, n, y0),
                                  f"{OUT}/{char}/{name}.png")


# ---------------- NARUTO (Mode Chakra Kurama / KCM) ----------------
A("naruto", naruto_atlas, "idle")
A("naruto", naruto_atlas, "run")
A("naruto", naruto_atlas, "jump", extra_action="fall")      # 8 frame: naik + turun
A("naruto", naruto_atlas, "guard")
A("naruto", naruto_atlas, "hurt")
A("naruto", naruto_atlas, "knockdown")
A("naruto", naruto_atlas, "win")
A("naruto", naruto_atlas, "light")                          # pukulan
A("naruto", naruto_atlas, "heavy")                          # hantaman ke tanah
A("naruto", naruto_atlas, "up")                             # uppercut berputar (juga serangan udara)
# catatan: aksi atlas "air" (y_up_attack) hanya berisi potongan lengan chakra raksasa
# tanpa badan, jadi tidak dipakai.
A("naruto", naruto_atlas, "down_air", name="down")
A("naruto", naruto_atlas, "rasengan_cast")                  # rentetan lengan chakra (4-koma)
A("naruto", naruto_atlas, "rasenshuriken_cast")             # putaran dash (6-koma)
A("naruto", naruto_atlas, "komaRasengan", name="clone_cast")  # bunshin + rasengan (3-koma)
A("naruto", naruto_atlas, "uzumakiRendan3", name="forward")   # tinju chakra memanjang

# ---------------- SASUKE (Taka) ----------------
A("sasuke", sasuke_atlas, "idle")
A("sasuke", sasuke_atlas, "run")
A("sasuke", sasuke_atlas, "jump", extra_action="fall")
A("sasuke", sasuke_atlas, "dash")
A("sasuke", sasuke_atlas, "hurt")
A("sasuke", sasuke_atlas, "light")                          # tendangan combo
A("sasuke", sasuke_atlas, "heavy")                          # tebasan pedang 2
A("sasuke", sasuke_atlas, "up")
A("sasuke", sasuke_atlas, "air", clear_top=5)               # ada artefak teks di atas frame 1
A("sasuke", sasuke_atlas, "down_air", name="down")
A("sasuke", sasuke_atlas, "shurikenThrow", name="throw")
A("sasuke", sasuke_atlas, "chidoriKoiten", name="chidori_cast")
C("sasuke", "sasuke_intro.png", "intro")                    # melepas jubah
C("sasuke", "sasuke_foword_sword_attack_1.png", "sword1")
C("sasuke", "sasuke_dash_attack.png", "dash_attack")
C("sasuke", "sasuke_fire_ball_justu.png", "fireball_cast")
C("sasuke", "sasuke_chidori_attack.png", "chidori_lunge")
F("sasuke", "sasuke_chidori_attack_3.png", "eisou", 50, 63, 4)   # Chidori Eisou
C("sasuke", "sasuke_GOD_OF_THUNDER_KIRIN.png", "kirin_cast", select=[0, 1, 2, 3, 4, 5, 6])
C("sasuke", "sasuke_super_chidori.png", "chidori_run")
C("sasuke", "sasuke_regular_sword_attack.png", "slash")
C("sasuke", "sasuke_lose.png", "win")                       # berbalik & berjalan pergi
C("sasuke", "sasuke_knocked_down.png", "knockdown", select=[4, 5, 6])
C("sasuke", "sasuke_knocked_down.png", "dead", select=[6])

# ---------------- FX ----------------
C("fx", "naruto_kcm_fx_rasengan_sphere.png", "rasengan", select=[1, 2])
C("fx", "naruto_kcm_fx_rasenshuriken.png", "rasenshuriken", y0=14)
C("fx", "sasuke_fireball_justu_effect_2.png", "fireball")
C("fx", "sasuke_fireball_justu_effect_1.png", "explosion", select=[2, 3, 4, 5, 7])
C("fx", "sasuke_Lightning_dragon_Jitsu.png", "kirin_dragon", select=[0, 1, 2])
C("fx", "sasuke_chidori_effect.png", "chidori_spark")
C("fx", "sasuke_CHIDORI_KOITEN_effects.png", "koiten", y0=10, min_h=40)
C("fx", "sasuke_substitusion_justu.png", "smoke", select=[0, 1, 2])
C("fx", "sasuke_amaterasu_attack_2.png", "amaterasu", min_h=50)

# File tunggal: susanoo, portrait, shuriken, background
os.makedirs(f"{OUT}/fx", exist_ok=True)
shutil.copy(f"{RAW}/sasuke_susano_ribcage.png", f"{OUT}/fx/susanoo.png")
shutil.copy("/tmp/ref1/pics/shur.png", f"{OUT}/fx/shuriken.png")
shutil.copy(f"{RAW}/naruto_kcm_portrait.png", f"{OUT}/naruto_portrait.png")
shutil.copy(f"{RAW}/sasuke_pfp.png", f"{OUT}/sasuke_portrait.png")

assets_dir = os.path.dirname(OUT)
bg = Image.open("/tmp/ref1/pics/bg.png").convert("RGB")
bg.save(os.path.join(assets_dir, "valley.jpg"), quality=90)

manifest["meta"] = {
    "naruto_scale": 2.7, "sasuke_scale": 3.0,
    "sources": [
        "github.com/Omololu457/multiverse-smash (strip JUS + atlas JSON)",
        "github.com/mission-coding/Naruto-Vs-Sasuke (background Lembah Akhir, shuriken)",
        "spritedatabase.net/file/1397 - Sasuke DS rip oleh Neimad (referensi)",
        "spriters-resource.com/ds_dsi/jus - Jump Ultimate Stars (referensi)",
    ],
}
with open(f"{OUT}/manifest.json", "w") as f:
    json.dump(manifest, f, indent=1)

for char in ("naruto", "sasuke", "fx"):
    print(f"== {char} ==")
    for k, v in manifest[char].items():
        print(f"  {k:20s} frames={v['frames']:2d} cell={v['fw']}x{v['fh']}")
print("OK ->", OUT)
