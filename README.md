# Godot 3.5 PS Vita export template – with network

A ready-to-use **PS Vita export template for Godot 3.5** (`vita_release.zip`) with the **network code enabled**,
so your Vita homebrew can talk to servers: `HTTPRequest`, `HTTPClient`, `StreamPeerTCP`, `PacketPeerUDP`,
`WebSocketClient` (ws://) and other socket-based features.

**Why?** The prebuilt template from the [godot-vita](https://github.com/SonicMastr/godot-vita) releases
(`3.5-rc5-vita1`) was compiled with `-DUNIX_SOCKET_UNAVAILABLE`, so no connection can be opened from a game.
This template is compiled from the godot-vita source with sockets turned on.

Used by [FlickLine](https://github.com/Swisha33/FlickLine) (internet radio) and BallRoller (online leaderboards).

## Download

- **[vita_release.zip](../../releases/download/latest/vita_release.zip)** from the [latest release](../../releases/tag/latest)
  (also in the root of this repo), plus `SHA256SUMS.txt`.

Contents (same layout as the official template):
```
eboot.bin                         Godot 3.5 Vita runtime (with sockets)
module/libGLESv2.suprx ...        PVR_PSP2 GPU driver modules
sce_sys/livearea/contents/template.xml
```

## What works / what doesn't

| | |
|---|---|
| ✅ HTTP (`http://`) | `HTTPRequest`, `HTTPClient` – REST APIs, game servers (e.g. Nakama on port 7350), MP3 radio streams |
| ✅ TCP / UDP | `StreamPeerTCP`, `TCP_Server`, `PacketPeerUDP`, `UDPServer` |
| ✅ WebSocket (`ws://`) | `WebSocketClient` without TLS |
| ❌ HTTPS / TLS (`https://`, `wss://`) | not available on the Vita build – use plain http, or put an http endpoint / proxy in front of your server |

Everything else is the normal godot-vita runtime (GLES2 renderer, ~Godot 3.5 feature set).

> Status: the template exports and runs the same as the official one. The network features were enabled from
> source but are still being verified on real hardware – please open an issue with what works for you.

## Requirements

- **Godot 3.5.x** to export your project (3.5.3 works; the Vita runtime is based on 3.5, so stay on 3.5).
- On the Vita: HENkaku / Ensō, VitaShell, and **`ur0:data/libshacccg.suprx`** (the shader compiler;
  extract it with [ShaRKF00D](https://github.com/OsirizX/ShaRKF00D) if your game closes right at start).
- Wi-Fi connected on the Vita for network features.
- Your project must use the **GLES2** renderer.

## How to use it

### Option A – godot-vita editor (Vita export preset)
If you use the godot-vita editor build (it has a "PS Vita" export platform):
1. *Project → Export → PS Vita* preset.
2. **Custom Template → Release**: pick this `vita_release.zip`.
3. Export the VPK as usual.

### Option B – stock Godot 3.5 + `tools/make_vpk.py` (no special editor, works in CI)
The VPK is just this template + your game's `game.pck` + `param.sfo` + LiveArea images.
`tools/make_vpk.py` does what the godot-vita exporter does, with plain Python 3:

1. In your project add an export preset (e.g. "VitaPack") with platform **Linux/X11**, custom feature **`vita`**,
   texture format **ETC** (no S3TC/BPTC), and export it as a pack:
   ```sh
   godot --path . --export-pack "VitaPack" build/game.pck
   ```
2. Build the VPK:
   ```sh
   python3 tools/make_vpk.py --template vita_release.zip --pck build/game.pck \
       --out build/MyGame.vpk --title "My Game" --title-id MYGM00001 --version 01.00 --art vita
   ```
   - `--title-id`: 9 characters, unique for your game (4 letters + 5 digits).
   - `--art`: folder with `icon0.png` (128×128), `pic0.png` (960×544), `bg.png` (840×500), `startup.png` (280×158).
     **They must be 8-bit indexed (palette) PNGs** (e.g. `convert in.png -colors 256 PNG8:out.png`), or the install
     fails. Provide all four: the template's LiveArea layout uses `bg.png` and `startup.png`.
3. Copy the VPK to the Vita and install it with VitaShell.

### Option C – GitHub Actions
```yaml
      - name: Vita template with network
        run: curl -sSL -o vita_release.zip https://github.com/Swisha33/Vita-Template-with-network-/releases/download/latest/vita_release.zip

      - name: Export VPK
        run: |
          godot --path . --export-pack "VitaPack" build/game.pck
          python3 tools/make_vpk.py --template vita_release.zip --pck build/game.pck \
            --out build/MyGame.vpk --title "My Game" --title-id MYGM00001 --version 01.00 --art vita
```
(Copy `tools/make_vpk.py` into your repo, or download it the same way. For a headless Godot 3.5.3 in CI see
[FlickLine's workflow](https://github.com/Swisha33/FlickLine/blob/main/.github/workflows/build.yml).)

### Detecting the Vita in your game
```gdscript
var on_vita = "vita" in OS.get_name().to_lower()   # or OS.has_feature("vita") with the custom feature above
```

### Tips for networking on the Vita
- Use `http://` URLs only. For a server you control, keep an HTTP port open for the Vita.
- Keep requests small and async (`HTTPRequest` node or `HTTPClient` polled in `_process`); the Vita's CPU is slow.
- Follow redirects yourself with `HTTPClient` (check the `Location` header on 301/302).
- For audio streaming, Godot 3 has no network stream player: read the stream with `HTTPClient`, cut it at MP3
  frame boundaries and feed `AudioStreamMP3` chunks to two players (see FlickLine's `scripts/Radio.gd`).

## Rebuilding the template yourself

`.github/workflows/build-template.yml` builds `vita_release.zip` from source on GitHub Actions
(Actions → *Build Vita template (with network) from source* → *Run workflow*, 1–2 hours):
1. Checks out [SonicMastr/godot-vita](https://github.com/SonicMastr/godot-vita) at a pinned commit (`GODOT_VITA_REF`).
2. Installs [VitaSDK](https://vitasdk.org) with vdpm, plus `vita-rss-libdl` and `pvr_psp2` from
   [vita-packages-extra](https://github.com/isage/vita-packages-extra).
3. Compiles with `scons p=vita target=release tools=no` (sockets enabled in this source).
4. Publishes `bin/vita_release.zip` as the release `template-from-source`.

To make a new build the main download, commit that zip to the repo root; `release.yml` republishes it as `latest`.

## Credits and licenses

- [Godot Engine](https://godotengine.org) – MIT license.
- [godot-vita](https://github.com/SonicMastr/godot-vita) by SonicMastr and contributors – MIT license.
- PVR_PSP2 GPU driver modules by GrapheneCt ([vita-packages-extra](https://github.com/isage/vita-packages-extra)).
- `tools/make_vpk.py` – written for BallRoller / FlickLine, free to use.

This repository only repackages a build of these open source projects for convenience.
