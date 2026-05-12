# JARVIS — Step-by-Step Setup

Follow these steps in order. Don't skip ahead. **Total time: about 15 minutes.**

---

## Before you start, you need three things

1. A Windows 10 PC (or Windows 11)
2. A working internet connection
3. About 15 minutes

You do **NOT** need:
- Python (we don't use it anymore)
- Outlook
- A Fish Audio account
- An OpenAI account

---

## STEP 1 — Install Node.js

**1.1.** Go to: <https://nodejs.org/>

**1.2.** You'll see two big green buttons. Click the **LTS** one (left button — recommended for most users).

**1.3.** A `.msi` installer will download (about 30 MB). Open it.

**1.4.** Click **Next**, accept the license, click **Next**, **Next**, **Next**, **Install**. (Just accept all the defaults — they're correct.)

**1.5.** When it finishes, click **Finish**.

**1.6.** ✅ **Verify it worked.** Open a new **Command Prompt** window (press Windows key, type `cmd`, hit Enter). Type:

```
node --version
```

You should see something like `v20.10.0` or `v22.0.0`. If you see `'node' is not recognized`, close the Command Prompt, open a new one, and try again. If it still fails, restart your PC and try once more.

---

## STEP 2 — Get an Anthropic API key

JARVIS uses Claude (made by Anthropic) for its brain. You need a key.

**2.1.** Go to: <https://console.anthropic.com/>

**2.2.** Sign up with email (or log in if you already have an account).

**2.3.** Once logged in, click **Get API keys** (or go to Settings → API Keys).

**2.4.** Click **Create Key**. Give it a name like "JARVIS".

**2.5.** **Copy the key.** It starts with `sk-ant-`. **You will not be able to see it again** after closing the page, so copy it somewhere safe (a note in Notepad is fine).

**2.6.** Cost note: Anthropic charges per use, but it's tiny. Casual personal use is usually well under $1/day. New accounts get free starter credits.

---

## STEP 3 — Download JARVIS

**3.1.** Go to your GitHub repo and click **Code** → **Download ZIP** (or `git clone` if you know how).

**3.2.** Extract the ZIP somewhere easy to find, like `C:\JARVIS` or your Desktop.

**3.3.** Open the extracted folder. You should see files including:
- `INSTALL.bat`
- `start_jarvis.bat`
- `server.js`
- `package.json`
- a `frontend` folder

---

## STEP 4 — Run the installer

**4.1.** **Double-click `INSTALL.bat`**.

A blue terminal window opens.

**4.2.** Press any key to continue past the welcome screen.

**4.3.** It checks that Node.js is installed. If you did Step 1 correctly, it should say `[OK]`.

**4.4.** It asks for your Anthropic API key. **Paste it here** (right-click in the terminal pastes on Windows 10+). Press Enter.

**4.5.** It asks what JARVIS should call you. Type your name (or "Tony" for full Iron Man mode). Press Enter.

**4.6.** Now it installs everything. **This takes 5-10 minutes.** Don't close the window. You'll see lots of text scrolling — that's normal.

**4.7.** When done, you'll see a green **INSTALL COMPLETE!** message. It asks if you want to launch JARVIS now. Type `Y` and press Enter.

---

## STEP 5 — First launch

JARVIS starts and prints a banner like this:

```
==================================================================
  J.A.R.V.I.S — ready
==================================================================
  Desktop (this PC):  https://localhost:8000
  Phone / LAN:        https://192.168.1.42:8000

  iPhone note: Safari will warn about the self-signed cert.
              Tap 'Show Details' → 'Visit Website' to continue.

  Scan this QR code with your phone (same WiFi):

   [a QR code is drawn here in ASCII]

==================================================================
```

**5.1.** Open **Google Chrome** (or Microsoft Edge). Type `https://localhost:8000` into the address bar.

**5.2.** ⚠️ Chrome will show a scary red **"Your connection is not private"** page. **This is normal** — JARVIS uses a self-signed certificate for your own PC.

- Click **Advanced** (at the bottom)
- Click **Proceed to localhost (unsafe)**

**5.3.** You'll see the JARVIS interface — a glowing blue particle orb. It says **"Tap to activate JARVIS"**.

**5.4.** Click anywhere on the page.

**5.5.** Chrome asks for **microphone permission**. Click **Allow**.

**5.6.** JARVIS says **"Good [morning/afternoon/evening], [your name]. JARVIS online."** in a British voice. 🎉

**5.7.** Try saying:
- "What time is it?"
- "Open Notepad"
- "Remember that I prefer dark mode"
- "Search for the weather in London"

---

## STEP 6 — Use it on your iPhone

**6.1.** Your iPhone needs to be on the **same WiFi** as your PC.

**6.2.** Look at the JARVIS console window on your PC. There's a QR code printed in it.

**6.3.** On your iPhone, open the **Camera app**. Point it at the QR code. A yellow banner appears at the top — tap it. Safari opens.

**6.4.** Safari shows a warning: **"This Connection Is Not Private"**. Tap **Show Details**, then **Visit Website**, then **Continue**.

**6.5.** The JARVIS page loads. Tap to activate.

**6.6.** iOS asks for microphone permission. Tap **Allow**.

**6.7.** **Hold** the big mic button on screen to talk. **Release** to send. JARVIS responds.

**6.8.** Optional: tap the Share button in Safari, then **Add to Home Screen**. JARVIS now appears as an app on your iPhone home screen.

---

## If something goes wrong

### Run the doctor

Double-click `doctor.bat`. It checks 8 common things and tells you what's wrong.

### Specific problems

**"node is not recognized"**
- Node.js isn't installed, or the installer wasn't given a fresh Command Prompt. Reinstall Node.js, then **restart your PC**.

**"npm install failed"** with `better-sqlite3` errors
- Your machine needs C++ build tools (rare on modern Windows).
- Easy fix: Install **Visual Studio Build Tools** from <https://visualstudio.microsoft.com/downloads/>
  - Scroll to **Tools for Visual Studio** → **Build Tools for Visual Studio**
  - During install, check **"Desktop development with C++"**
  - Wait for it to finish (~5 GB download), then run `INSTALL.bat` again.

**Browser shows "site can't be reached"**
- JARVIS isn't running. Make sure `start_jarvis.bat` window is open.
- Check the URL matches what the console printed.

**Phone can't connect**
- Same WiFi as PC? Check.
- Windows Firewall: a popup may have asked you on first run. If you clicked "Cancel", you need to allow it manually. Search Windows for **Windows Defender Firewall** → **Allow an app** → find Node.js → tick **Private**.

**iPhone says "Microphone permission denied"**
- Settings → Safari → scroll to **Microphone** → **Ask** (not Deny).
- Reload the JARVIS page.

**No voice — only text**
- First TTS request takes a couple of seconds (Microsoft Edge TTS connects).
- If it consistently fails: your network or antivirus might be blocking the MS Edge TTS endpoint. JARVIS will fall back to your browser's built-in voice.

**JARVIS misunderstands me**
- On PC, you're using Chrome's Web Speech API. Speak clearly, normal pace.
- On iPhone, you're holding the mic button. Hold it down through the whole sentence, then release.

---

## Daily use

After the first setup, all you do is:

1. Double-click `start_jarvis.bat`
2. Open the URL in Chrome
3. Click → speak

That's it.

---

## What can JARVIS actually do?

Try these phrases:

| Say... | What happens |
|--------|-------------|
| "What time is it?" | Tells you the time and date |
| "Open Notepad" | Launches Notepad |
| "Open Spotify" | Launches Spotify |
| "Search for tonight's NBA scores" | Opens Google search in your browser |
| "Go to youtube.com" | Opens YouTube |
| "Remember that my dog's name is Charlie" | Saved forever, across sessions |
| "What do you remember?" | Recalls what you've told it |
| "Add a task to call mom tomorrow at 5pm" | Tracked with a due time |
| "What's on my to-do list?" | Reads pending tasks |
| "Build me a snake game in JavaScript" | Spawns Claude Code to build it in `~/Documents/JARVIS Projects/` (requires Claude Code CLI installed separately) |
| "Save a note: ideas for my book" | Creates a `.txt` in `~/Documents/JARVIS Notes/` |

---

## Files JARVIS creates on your PC

- `~/Documents/JARVIS/memory.db` — what JARVIS remembers about you
- `~/Documents/JARVIS Notes/` — saved notes (`.txt` files)
- `~/Documents/JARVIS Projects/` — software JARVIS builds for you
- `cert.pem`, `key.pem` in the JARVIS folder — SSL certificate (auto-generated)

To wipe and start over: delete those files and run `INSTALL.bat` again.
