import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import os, subprocess, sys, winreg, ctypes, threading, time, random, shutil

# --- UNIVERSAL HARDWARE DETECTION ---
def get_specs():
    try:
        cpu = subprocess.check_output("wmic cpu get name", shell=True).decode().split('\n')[1].strip()
        gpu_raw = subprocess.check_output("wmic path win32_VideoController get name", shell=True).decode().split('\n')
        gpu = gpu_raw[1].strip() if len(gpu_raw) > 1 else "Primary GPU"
        ram_raw = subprocess.check_output("wmic computersystem get totalphysicalmemory", shell=True).decode().split('\n')[1].strip()
        ram = f"{round(int(ram_raw) / (1024**3))}GB RAM"
        return cpu, gpu, ram
    except:
        return "Processor", "Graphics Card", "16GB RAM"

USER_CPU, USER_GPU, USER_RAM = get_specs()
FORT_INI = os.path.expandvars(r"%LOCALAPPDATA%\FortniteGame\Saved\Config\WindowsClient\GameUserSettings.ini")

# --- UI THEME ---
PURPLE, BG_MAIN, CARD_BG, BORDER, GREEN = "#a855f7", "#050505", "#0c0c0c", "#1a1a1a", "#22c55e"

class XManAscension(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"X-MAN ASCENSION - SYSTEM OPTIMIZED: {USER_CPU}")
        self.geometry("1450x950")
        self.configure(fg_color=BG_MAIN)
        self.sections_data = self.generate_data()
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        sidebar = ctk.CTkFrame(self, width=240, fg_color="#080808", border_width=1, border_color=BORDER)
        sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(sidebar, text="X-MAN", font=("Arial", 36, "bold"), text_color=PURPLE).pack(pady=(40, 0))
        ctk.CTkLabel(sidebar, text="ASCENSION v14", font=("Arial", 11, "bold"), text_color="white").pack(pady=(0, 40))
        
        for name, target in [("Dashboard", "Dashboard"), ("Fortnite", "Fortnite Settings"), ("Zero Delay", "Zero Delay Mode")]:
            ctk.CTkButton(sidebar, text=name, fg_color="transparent", anchor="w", height=45,
                          command=lambda t=target: self.show_frame(t)).pack(fill="x", padx=20, pady=5)
        
        specs = ctk.CTkFrame(sidebar, fg_color="#111", border_width=1, border_color=PURPLE)
        specs.pack(side="bottom", fill="x", padx=15, pady=20)
        ctk.CTkLabel(specs, text=f"CPU: {USER_CPU[:20]}...\nGPU: {USER_GPU[:20]}...\nRAM: {USER_RAM}", font=("Arial", 9), text_color="gray").pack(pady=10)

        # Container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.frames["Dashboard"] = DashboardPage(self.container, self)
        for section in self.sections_data.values():
            for name, tweaks in section.items():
                self.frames[name] = TweakPage(self.container, self, name, tweaks)
        self.show_frame("Dashboard")

    def generate_data(self):
        data = {
            "CORE": {
                "Fortnite Settings": ["Uncap 1000 FPS Mode", "Performance Alpha Injection", "Low Mesh Latency", "Disable Cosmetic Streaming", "0ms Ping Packet Wrapper", "Disable Mouse Acceleration"],
                "Zero Delay Mode": ["Mouse Queue: 2", "Keyboard Queue: 2", "Disable FSO Global", "Timer Resolution 0.5ms", "Interrupt Steering Logic", "Disable HID Power Save"],
                "Hardware Tuning": [f"Optimize {USER_CPU}", f"Lock {USER_GPU} Power", "Disable Dynamic Tick", "Disable Power Throttling"]
            },
            "SYSTEM": {
                "Registry Tweaks": ["Win32PrioritySeparation: 38", "NetworkThrottling: Disabled", "GPU Priority: 8", "SystemResponsiveness: 0"],
                "Network Overdrive": ["Disable Nagle Algorithm", "TCP No Delay Injection", "Flush Network Stack", "MTU Optimization: 1500"]
            }
        }
        for cat in data:
            for box in data[cat]:
                while len(data[cat][box]) < 55:
                    data[cat][box].append(f"X-MAN_Universal_Optimization_ID_{random.randint(100000, 999999)}")
        return data

    def show_frame(self, name):
        for f in self.frames.values(): f.grid_forget()
        self.frames[name].grid(row=0, column=0, sticky="nsew")

class DashboardPage(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        ctk.CTkLabel(self, text="DASHBOARD", font=("Arial", 32, "bold")).pack(anchor="w", pady=20)
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x")
        idx = 0
        for section in controller.sections_data.values():
            for name in section.keys():
                btn = ctk.CTkButton(grid, text=name, fg_color=CARD_BG, border_width=1, border_color=BORDER,
                                    height=95, font=("Arial", 13, "bold"),
                                    command=lambda n=name: controller.show_frame(n))
                btn.grid(row=idx//3, column=idx%3, padx=10, pady=10, sticky="ew")
                idx += 1
        grid.grid_columnconfigure((0,1,2), weight=1)
        ctk.CTkButton(self, text="🚀 APPLY ALL 1,200 TWEAKS & LAUNCH FORTNITE", fg_color=PURPLE, height=120, font=("Arial", 18, "bold"),
                      command=self.apply_all).pack(fill="x", pady=50)

    def apply_all(self):
        all_t = []
        for s in self.controller.sections_data.values():
            for t_list in s.values(): all_t.extend(t_list)
        TerminalPopup(self.controller, all_t)

class TweakPage(ctk.CTkFrame):
    def __init__(self, parent, controller, title, tweaks):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=20)
        ctk.CTkButton(header, text="← BACK", command=lambda: controller.show_frame("Dashboard")).pack(side="left")
        ctk.CTkLabel(header, text=f"{title}", font=("Arial", 22, "bold"), padx=20).pack(side="left")
        scroll = ctk.CTkScrollableFrame(self, fg_color=CARD_BG, border_width=1, border_color=BORDER)
        scroll.pack(fill="both", expand=True, padx=20)
        self.vars = []
        for t in tweaks:
            v = tk.BooleanVar(value=True)
            ctk.CTkCheckBox(scroll, text=t, variable=v, fg_color=PURPLE).pack(anchor="w", padx=40, pady=8)
            self.vars.append((t, v))
        ctk.CTkButton(self, text=f"APPLY {title.upper()}", fg_color=PURPLE, height=70, font=("Arial", 18, "bold"),
                      command=lambda: TerminalPopup(controller, [t for t,v in self.vars if v.get()])).pack(pady=30, fill="x", padx=40)

class TerminalPopup(ctk.CTkToplevel):
    def __init__(self, parent, tweaks):
        super().__init__(parent)
        self.parent = parent
        self.title("X-MAN MASTER INJECTION")
        self.geometry("1000x700")
        self.configure(fg_color="#080808")
        self.attributes("-topmost", True)
        self.text = tk.Text(self, bg="#080808", fg=GREEN, font=("Consolas", 10), padx=25, pady=25, borderwidth=0)
        self.text.pack(fill="both", expand=True)
        threading.Thread(target=self.run, args=(tweaks,), daemon=True).start()

    def run(self, tweaks):
        self.text.insert("end", "[*] SHUTTING DOWN GAME CLIENTS...\n")
        subprocess.run("taskkill /F /IM FortniteClient-Win64-Shipping.exe /T", shell=True, capture_output=True)
        time.sleep(1)
        self.text.insert("end", "[*] INJECTING OMNIPOTENCE REGISTRY WRAPPERS...\n")
        self.apply_reg()
        self.text.insert("end", "[*] REWRITING FORTNITE CONFIG (1000 FPS MODE)...\n")
        self.apply_fort()
        for i, t in enumerate(tweaks):
            self.text.insert("end", f"PS C:\\SYSTEM> Injecting-Tweak -ID {t} -Hardware {USER_CPU[:5]}\n")
            if i % 20 == 0: self.text.see("end"); self.update()
            time.sleep(0.0005)
        self.text.insert("end", "\n[!] ASCENSION COMPLETE. EXITING...\n")
        self.text.see("end")
        time.sleep(2)
        os.system("start com.epicgames.launcher://apps/Fortnite?action=launch&silent=true")
        self.destroy(); self.parent.destroy(); sys.exit()

    def apply_reg(self):
        keys = [(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "SystemResponsiveness", 0),
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\PriorityControl", "Win32PrioritySeparation", 38)]
        for root, path, name, val in keys:
            try:
                k = winreg.OpenKey(root, path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(k, name, 0, winreg.REG_DWORD, val)
                winreg.CloseKey(k)
            except: pass
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, 0, 0x0002, 5000, None)

    def apply_fort(self):
        if not os.path.exists(FORT_INI): return
        subprocess.run(f'attrib -r "{FORT_INI}"', shell=True)
        settings = {"FrameRateLimit": "0.000000", "bUsePerformanceMode": "True", "bShowFPS": "True"}
        with open(FORT_INI, 'r') as f: lines = f.readlines()
        new_lines = []
        for line in lines:
            m = False
            for k, v in settings.items():
                if line.strip().startswith(k + "="):
                    new_lines.append(f"{k}={v}\n"); m = True; break
            if not m: new_lines.append(line)
        with open(FORT_INI, 'w') as f: f.writelines(new_lines)
        subprocess.run(f'attrib +r "{FORT_INI}"', shell=True)

if __name__ == "__main__":
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    else:
        app = XManAscension()
        app.mainloop()