import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from pcare_automation_test_one import FORM_URL, DEFAULT_RESP_RATE, DEFAULT_HEART_RATE, split_value

# ── Pastel Girly Theme ──────────────────────────────────────────────────────
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

BG         = "#FFF0F5"   # lavender blush background
CARD       = "#FFFFFF"   # white card
ACCENT     = "#FF85A1"   # rose pink accent
ACCENT_HOV = "#FF6B8A"   # darker rose on hover
SOFT_PINK  = "#FFD6E0"   # soft pink for frames
TEXT       = "#5C3D4E"   # muted plum text
SUBTEXT    = "#A07080"   # soft subtext
GREEN      = "#B5EAD7"   # mint green success
ORANGE     = "#FFDAC1"   # peach skipped
RED        = "#FFB7B2"   # soft red error
BLUE       = "#C7CEEA"   # periwinkle test
GREEN_TXT  = "#3D7A5E"
ORANGE_TXT = "#7A4E2D"
RED_TXT    = "#7A2E2E"
BLUE_TXT   = "#3D4E7A"

FONT_TITLE = ("Helvetica", 22, "bold")
FONT_LABEL = ("Helvetica", 13)
FONT_SMALL = ("Helvetica", 11)
FONT_BOLD  = ("Helvetica", 13, "bold")

KEGIATAN_OPTIONS = {"🏃 Senam (037)": "037", "📚 Edukasi (036)": "036"}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.configure(fg_color=BG)
        self.title("PCare Prolanis ✨")
        self.geometry("720x720")
        self.minsize(620, 640)

        self.csv_path     = ctk.StringVar()
        self.kegiatan_var = ctk.StringVar(value="🏃 Senam (037)")
        self.mode_var     = ctk.StringVar(value="test")
        self.counts       = {"success": 0, "skipped": 0, "error": 0, "test": 0}

        self._build_ui()

    def _card(self, parent, **kwargs):
        return ctk.CTkFrame(parent, fg_color=CARD, corner_radius=16,
                            border_width=1, border_color=SOFT_PINK, **kwargs)

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=ACCENT, corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="💊 Automation Buat Istriku 🌸",
                     font=FONT_TITLE, text_color="white").pack(expand=True)

        # ── CSV picker ──────────────────────────────────────────
        card1 = self._card(self)
        card1.pack(fill="x", padx=24, pady=(18, 6))
        ctk.CTkLabel(card1, text="📂  File CSV", font=FONT_BOLD,
                     text_color=TEXT).pack(anchor="w", padx=16, pady=(12, 4))
        row = ctk.CTkFrame(card1, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkEntry(row, textvariable=self.csv_path, state="readonly",
                     fg_color=SOFT_PINK, border_color=ACCENT, text_color=TEXT,
                     font=FONT_SMALL, height=36, corner_radius=10
                     ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(row, text="Browse 🗂️", width=100, height=36,
                      fg_color=ACCENT, hover_color=ACCENT_HOV,
                      text_color="white", corner_radius=10, font=FONT_SMALL,
                      command=self._browse_csv).pack(side="right")

        # ── Settings card ───────────────────────────────────────
        card2 = self._card(self)
        card2.pack(fill="x", padx=24, pady=6)
        ctk.CTkLabel(card2, text="⚙️  Pengaturan", font=FONT_BOLD,
                     text_color=TEXT).pack(anchor="w", padx=16, pady=(12, 4))
        settings_row = ctk.CTkFrame(card2, fg_color="transparent")
        settings_row.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkLabel(settings_row, text="Kegiatan:", font=FONT_LABEL,
                     text_color=SUBTEXT).pack(side="left", padx=(0, 6))
        ctk.CTkOptionMenu(settings_row, values=list(KEGIATAN_OPTIONS.keys()),
                          variable=self.kegiatan_var,
                          fg_color=SOFT_PINK, button_color=ACCENT,
                          button_hover_color=ACCENT_HOV, text_color=TEXT,
                          dropdown_fg_color=CARD, dropdown_text_color=TEXT,
                          font=FONT_SMALL, corner_radius=10, width=180,
                          ).pack(side="left")
        ctk.CTkLabel(settings_row, text="Mode:", font=FONT_LABEL,
                     text_color=SUBTEXT).pack(side="left", padx=(24, 8))
        for label, value in [("🔍 Test", "test"), ("✅ Submit", "submit")]:
            ctk.CTkRadioButton(settings_row, text=label, variable=self.mode_var,
                               value=value, font=FONT_SMALL, text_color=TEXT,
                               fg_color=ACCENT, hover_color=ACCENT_HOV,
                               border_color=ACCENT).pack(side="left", padx=6)

        # ── Start button ────────────────────────────────────────
        self.start_btn = ctk.CTkButton(
            self, text="▶  Mulai Automation", state="disabled",
            fg_color=ACCENT, hover_color=ACCENT_HOV, text_color="white",
            font=("Helvetica", 14, "bold"), height=44, corner_radius=12,
            command=self._start)
        self.start_btn.pack(padx=24, pady=10, fill="x")

        # ── Log area ────────────────────────────────────────────
        card3 = self._card(self)
        card3.pack(fill="both", expand=True, padx=24, pady=6)
        ctk.CTkLabel(card3, text="📋  Log", font=FONT_BOLD,
                     text_color=TEXT).pack(anchor="w", padx=16, pady=(10, 4))
        self.log_box = ctk.CTkTextbox(card3, state="disabled", wrap="word",
                                      fg_color=SOFT_PINK, text_color=TEXT,
                                      font=("Courier", 11), corner_radius=10,
                                      border_width=0)
        self.log_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # ── Summary bar ─────────────────────────────────────────
        summary = ctk.CTkFrame(self, fg_color="transparent")
        summary.pack(fill="x", padx=24, pady=(0, 16))
        specs = [
            ("success", "✅ SUCCESS", GREEN,  GREEN_TXT),
            ("skipped", "⏭ SKIPPED", ORANGE, ORANGE_TXT),
            ("error",   "❌ ERROR",   RED,    RED_TXT),
            ("test",    "🔍 TEST",    BLUE,   BLUE_TXT),
        ]
        self.summary_labels = {}
        for key, label, bg, fg in specs:
            box = ctk.CTkFrame(summary, fg_color=bg, corner_radius=10)
            box.pack(side="left", expand=True, fill="x", padx=4)
            lbl = ctk.CTkLabel(box, text=f"{label}: 0", font=FONT_BOLD, text_color=fg)
            lbl.pack(pady=12)
            self.summary_labels[key] = lbl

    # ── Actions ─────────────────────────────────────────────────────────────

    def _browse_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            self.csv_path.set(path)
            self.start_btn.configure(state="normal")

    def _log(self, msg):
        self.after(0, self._append_log, msg)

    def _append_log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _update_summary(self):
        labels = {"success": "✅ SUCCESS", "skipped": "⏭ SKIPPED",
                  "error": "❌ ERROR", "test": "🔍 TEST"}
        for key, lbl in self.summary_labels.items():
            lbl.configure(text=f"{labels[key]}: {self.counts[key]}")

    def _start(self):
        self.start_btn.configure(state="disabled", text="⏳ Berjalan...")
        self.counts = {"success": 0, "skipped": 0, "error": 0, "test": 0}
        self.after(0, self._update_summary)
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        threading.Thread(target=self._run_automation, daemon=True).start()

    # ── Automation thread ────────────────────────────────────────────────────

    def _run_automation(self):
        csv_path    = self.csv_path.get()
        kegiatan    = KEGIATAN_OPTIONS[self.kegiatan_var.get()]
        submit_form = self.mode_var.get() == "submit"

        try:
            df = pd.read_csv(csv_path, dtype=str).fillna("")
        except Exception as e:
            self._log(f"ERROR membaca CSV: {e}")
            self.after(0, lambda: self.start_btn.configure(state="normal", text="▶  Mulai Automation"))
            return

        self._log(f"✨ Loaded {len(df)} data dari CSV")
        self._log(f"Kegiatan : {self.kegiatan_var.get()}")
        self._log(f"Mode     : {'SUBMIT 🚀' if submit_form else 'TEST 🔍'}")
        self._log("─" * 50)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir="browser_session", headless=False)
                page = browser.pages[0]
                page.goto(FORM_URL)

                self._login_event = threading.Event()
                self.after(0, self._show_login_dialog)
                self._login_event.wait()

                self._log("🌸 Automation dimulai...")

                for index, row in df.iterrows():
                    no_bpjs = str(row["NO_BPJS"]).strip()
                    self._log(f"[{index + 1}/{len(df)}] {no_bpjs}")
                    try:
                        result, msg = self._fill_one_row(page, row, index, submit_form, kegiatan)
                        self.counts[result] += 1
                        icons = {"success": "✅", "skipped": "⏭", "error": "❌", "test": "🔍"}
                        self._log(f"  {icons[result]} {result.upper()}{': ' + msg if msg else ''}")
                    except Exception as e:
                        self.counts["error"] += 1
                        self._log(f"  ❌ ERROR: {e}")
                        self.after(0, self._update_summary)
                        try:
                            page.goto(FORM_URL, wait_until="networkidle")
                        except Exception:
                            self._log("  ⚠️ Browser tertutup, automation dihentikan.")
                            break

                    self.after(0, self._update_summary)
                    page.wait_for_timeout(3000)

                self._log("─" * 50)
                self._log(f"🎀 Selesai! SUCCESS:{self.counts['success']} SKIPPED:{self.counts['skipped']} ERROR:{self.counts['error']} TEST:{self.counts['test']}")

                self._review_event = threading.Event()
                self.after(0, self._show_review_dialog)
                self._review_event.wait()

                browser.close()

        except Exception as e:
            self._log(f"❌ Automation berhenti: {e}")
        finally:
            self.after(0, lambda: self.start_btn.configure(state="normal", text="▶  Mulai Automation"))

    def _show_login_dialog(self):
        messagebox.showinfo("Login Required 🌸",
                            "Login dulu dan atur tanggal,\nlalu klik OK untuk mulai ✨")
        self._login_event.set()

    def _show_review_dialog(self):
        messagebox.showinfo("Selesai 🎀",
                            "Automation selesai!\nCek hasil di browser, lalu klik OK untuk menutup 💖")
        self._review_event.set()

    def _fill_one_row(self, page, row, index, submit_form, kegiatan):
        no_bpjs = str(row["NO_BPJS"]).strip()
        tinggi_badan, berat_badan = split_value(row["TB_BB"])
        lingkar_perut = str(row["LP"]).strip()
        sistole, diastole = split_value(row["TD"])

        page.locator("#txtnokartu").fill(no_bpjs)
        page.locator("#btnCariPeserta").click()
        page.locator("#lblnmpst:not(:empty), .alert-danger, .alert-warning, .bootbox-body").first.wait_for(state="visible", timeout=15000)

        alert = page.locator(".alert-danger, .alert-warning, .bootbox-body").first
        if alert.is_visible():
            msg = alert.inner_text()
            dismiss = page.locator(".bootbox .btn-primary, .alert .close").first
            if dismiss.is_visible():
                dismiss.click()
                page.wait_for_timeout(500)
            page.goto(FORM_URL, wait_until="networkidle")
            return "skipped", msg

        page.locator('input[name="kunjSakitF"][value="false"]').check(force=True)
        page.locator('input[name="tkp"][value="10"]').check(force=True)
        page.locator("#poli").select_option(kegiatan)
        page.locator("#tinggiBadan").fill(tinggi_badan)
        page.locator("#beratBadan").fill(berat_badan)
        page.locator("#lingkarPerut").fill(lingkar_perut)
        page.locator("#sistole").fill(sistole)
        page.locator("#diastole").fill(diastole)
        page.locator("#respRate").fill(DEFAULT_RESP_RATE)
        page.locator("#heartRate").fill(DEFAULT_HEART_RATE)

        if submit_form:
            page.wait_for_timeout(1000)
            if page.locator("#btnSimpanPendaftaran").is_disabled():
                page.goto(FORM_URL, wait_until="networkidle")
                return "skipped", "button disabled"
            page.locator("#btnSimpanPendaftaran").click()
            try:
                page.locator(".alert-success, .gritter-item-wrapper").first.wait_for(state="visible", timeout=10000)
                dismiss = page.locator(".gritter-close").first
                if dismiss.is_visible():
                    dismiss.click()
                return "success", ""
            except PlaywrightTimeoutError:
                return "success", "no banner"
        else:
            return "test", ""


if __name__ == "__main__":
    app = App()
    app.mainloop()
