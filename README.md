# Mirra Call's Second Opinion (Open Reference Implementation)

**Mirra Call is a local-first, computer-vision coaching mirror for upper-extremity rehab and self-care.** Small on-device models guide older adults through everyday hand and arm tasks, like washing the face, with live movement feedback and plain-language coaching tips. It is built for older adults in continuing care and community programs, for the aides and recreation staff who supervise sessions, and for the occupational therapists who write the tasks and keep clinical oversight.

**Status:** working prototype, piloted with older adults and clinicians. This repository is the **Open Reference Implementation** of Mirra Call: the software layer, demonstrated here with a laptop webcam and designed to run on a local device behind a two-way mirror (see [Intended deployment](#intended-deployment)). It is not a medical device, it does not diagnose, and clinicians make all clinical decisions.

**Website:** https://mirracall.github.io/mirracallwebsite-main/

---

## What this demo does

A webcam demo that guides a participant through washing their face with a face towel, with live movement feedback and coaching tips.

- **Participant routes:** `/setup` (consent, camera checks, arm and face calibration) and `/session` (guided exercise with live coaching).
- **Reviewer routes:** `/metrics`, `/review`, and `/validation`.

## Privacy and data flow

- **Runs locally by default.** Pose tracking, struggle detection, and the overlay all run in the browser. The default coaching model is Qwen3-VL 2B served locally through Ollama.
- **Video never leaves the browser.** No video or images are sent anywhere.
- **Only an aggregate movement summary reaches the model**, and only with the participant's consent.
- **A hosted endpoint is optional and intended for development.** Any OpenAI-compatible endpoint can be selected through `.env` (see below).
- **Fallback is labeled.** When model coaching is disabled or a request fails, the app shows the tip as a *Local tip*.

## How it works

Mirra Call uses two layers, so a language model is only involved when simple rules aren't enough.

1. **System 1 (browser):** MediaPipe pose estimation, frame gates, and struggle detection with a cooldown. It drives the live overlay and basic cues instantly, with no language model.
2. **System 2 (local model):** when System 1 detects a struggle, or the participant presses **Get a tip**, the app sends an aggregate movement summary to a small vision-language model (Qwen3-VL 2B) and returns a short coaching tip.

## Intended deployment

This repository is the Open Reference Implementation of Mirra Call. It is meant to be read, run, and adapted by other builders and clinicians.

- **In this repo:** a laptop and webcam demo, so anyone can run the full software loop without special hardware.
- **Intended hardware:** a two-way glass mirror with a camera, driven by a small local computer (an NVIDIA Jetson module) that runs the browser layer and the local model. The mirror shows a simple overlay and gives spoken and visual cues.
- **No depth camera is needed.** A standard RGB camera is enough.
- **Everything stays on the device.** No cloud service or frontier model API is required.

The full hardware build guide is in development and is not in this repository yet. An early concept for it, a modular mirror where assembling it is the first rehabilitation exercise, is published as [PeaceByPiece](https://github.com/Rendyest/SomeAssemblyRequired). It is a concept-stage design exploration, not a tested build guide.

## Stack

- **Web app:** React + TypeScript + Vite.
- **Pose estimation:** MediaPipe Tasks Vision in the browser for live sessions. Python scripts (`system1_loop.py`, `replay.py`, `quality_gate.py`, `struggle_detector.py`, `video_diagnostics.py`) handle the offline loop, replay harness, and diagnostics.
- **Coaching proxy:** a Node proxy (`server/proxy.mjs`) forwards the aggregate movement summary to the configured Qwen3-VL 2B endpoint and returns a tip. The default endpoint is local Ollama.
- **Mock and synthetic data (never results):** `public/mock-stream.json` replays a fixed event stream, and `scripts/make-demo-data.mjs` generates deterministic synthetic clips for the reviewer routes (gitignored output).
- No SAM is used and no external datasets are used. (`third_party/sam/` is vendored but unused. Nothing imports it.)

## Live status

Working: webcam setup checks, calibration, live pose with frame gates, struggle detection with cooldown, local and hosted coaching tips, session controls, and the reviewer routes.

## How to run

Use Node.js 22 or later. From the repository root in Windows PowerShell:

```powershell
npm install
npm run dev        # open the printed localhost URL (webcam needs localhost or HTTPS)
npm test           # vitest suite
```

### Live coaching (local, the default)

Install [Ollama](https://ollama.com) and fetch the model once:

```powershell
ollama pull qwen3-vl:2b
```

Then run the proxy alongside the frontend in separate PowerShell windows from the repository root. The default endpoint is `http://127.0.0.1:11434/v1`.

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
npm run coach-proxy
npm run dev
```

Open the localhost URL Vite prints. In an active webcam session, opt in to sharing movement summaries with the model and press **Get a tip**, or let System 1 detect a struggle. Metrics shows the outcome of completed model attempts.

### Optional: hosted endpoint (development)

To use a hosted OpenAI-compatible endpoint instead of local Ollama, set `MODEL_API_BASE_URL`, `MODEL_NAME`, and (when required) `MODEL_API_KEY` in `.env`. The same rule applies: only the aggregate movement summary is sent, never video.

### Local rehearsal from a production build

Run `npm run build` followed by `npm run preview` with the proxy still running. Both Vite commands forward `/api/coach` to the loopback proxy on port 8787 by default. To use another port, set `COACH_PORT` in the root `.env` and restart both commands.

## Reviewer routes

Generate synthetic demo data (defaults to `scripts/clips/demo/`, which is gitignored and can never be committed):

```powershell
node scripts/make-demo-data.mjs
node scripts/make-results.mjs scripts/clips/demo
```

Then:

- `/metrics` → Replay → Choose a clip file
- `/review` → Choose a review bundle file
- `/validation` reads the generated `results/results.json`

Check the plumbing with `npm test -- tests/demoData.test.ts`, which generates into a temp folder, validates every output, and scores it.

## Recording a real clip and measuring call policies

Synthetic clips and `?source=mock` must never back reported numbers. For real figures, record a clip from the webcam and replay it on `/metrics`:

1. Enable the dev recorder by creating gitignored `src/config/config.local.json` containing `{ "ui": { "dev_controls": true } }`, then restart `npm run dev`.
2. On `/setup`, tick both the recording consent choice and the face-masked clips choice. Without the first, recording will not start. Without the second, download is refused.
3. On `/metrics`, enter an anonymous label (a code like `P1`, never a name), tick the recorder's own consent checkbox, and press **Start recording**. Optionally use **Mark struggle start/end** around the hard part. Those labels power the needed-help coverage rows. Recording caps at 120 seconds and stores landmark numbers only, never video or images.
4. Press **Stop recording**, then **Download clip** (`<label>.clip.json`, `source: "recorded"`). Calibrate beforehand if you want a calibrated replay. An existing video file can be converted instead via the importer below the recorder.
5. In the Replay workspace use **Choose a clip file** with that file (not "Replay synthetic fixture"). Take calls-made per policy (`every_frame`, `fixed_interval` at the 2 s default, `gated_trigger`) and calls-saved against the baselines from the Loop comparison, then **Download results** (JSON) and (CSV).

System 2 latency is not in that export by design (the replay never calls the model). Time real `/session` model calls instead, using DevTools Network on `POST /api/coach` or the proxy log, with the proxy running. Each tip costs one call and the 60 s cooldown spaces them out, so with only a handful of calls report the median and the count rather than a p95.

Keep exported files and screenshots out of `results/` (gitignored build output): save them elsewhere and never overwrite `results/results.json`.

## License

MIT. See [LICENSE](LICENSE). Copyright (c) 2026 Lunate Labs.
