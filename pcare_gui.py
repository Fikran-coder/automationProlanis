import os
import threading
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import Stealth

from pcare_automation_test_one import FORM_URL, DEFAULT_RESP_RATE, DEFAULT_HEART_RATE, split_value
from pcare_pendaftaran_peserta import (
    FORM_URL as PESERTA_FORM_URL,
    fill_peserta_row,
)
from komdat_automation import (
    KOMDAT_LOGIN_URL,
    navigate_to_table,
    run_komdat,
    parse_month,
)
from epuskesmas_automation import (
    EPUSKESMAS_LOGIN_URL,
    EPUSKESMAS_PASIEN_URL,
    run_update_alamat,
)

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
AUTOMATION_OPTIONS = ["📋 Pendaftaran Kegiatan Prolanis", "👥 Pendaftaran Peserta Prolanis", "🏥 Komdat Posyandu", "📍 Update Alamat CSV"]


def _dismiss_load_modals(page, after_reload=True):
    """Dismiss warning banners and bootbox modals that appear on page load/reload.
    Only dismisses SYSTEM modals (Belum Entri, HFIS), not patient-specific alerts.
    Also handles rate-limit page by waiting for auto-reload.
    
    after_reload=True: called after page.goto — waits for modals to render.
    after_reload=False: quick check for overlays blocking interaction.
    """
    # Handle rate-limit page ("Permintaan Terlalu Cepat")
    if after_reload:
        try:
            if page.locator(".rate-card").is_visible(timeout=2000):
                # Page will auto-reload after countdown (max 16s), wait for it
                page.wait_for_selector("#txtnokartu", timeout=25000)
                page.wait_for_timeout(2000)  # extra buffer for modals to appear after reload
        except Exception:
            pass
        # Wait a moment for modals to render after page load
        page.wait_for_timeout(2000)
    # Dismiss yellow warning banner (Pakta Integritas HFIS)
    # This overlay intercepts clicks on the form, so must be dismissed first
    for _ in range(3):
        try:
            warning_close = page.locator('.WarningBoxKuningHitam [data-notify="dismiss"]')
            if warning_close.is_visible(timeout=1000):
                warning_close.click()
                page.wait_for_timeout(500)
            else:
                break
        except Exception:
            break
    # Dismiss bootbox modal ONLY if it's a system modal (Belum Entri Pelayanan)
    try:
        bootbox_body = page.locator(".bootbox-body")
        if bootbox_body.is_visible(timeout=1000 if not after_reload else 2000):
            text = bootbox_body.inner_text()
            if "Belum Entri Pelayanan" in text:
                page.locator(".bootbox-accept").click()
                page.wait_for_timeout(500)
    except Exception:
        pass
    # Check if warning banner appeared again after bootbox dismiss
    try:
        warning_close = page.locator('.WarningBoxKuningHitam [data-notify="dismiss"]')
        if warning_close.is_visible(timeout=1000):
            warning_close.click()
            page.wait_for_timeout(300)
    except Exception:
        pass
    # Clear any leftover text in search field (prevent stale data)
    if after_reload:
        try:
            txt = page.locator("#txtnokartu")
            if txt.is_visible(timeout=1000):
                txt.fill("")
        except Exception:
            pass


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.configure(fg_color=BG)
        self.title("PCare Prolanis ✨")
        self.geometry("720x720")
        self.minsize(620, 640)

        self.csv_path          = ctk.StringVar()
        self.automation_var    = ctk.StringVar(value=AUTOMATION_OPTIONS[0])
        self.kegiatan_var      = ctk.StringVar(value="🏃 Senam (037)")
        self.mode_var          = ctk.StringVar(value="test")
        self.month_var         = ctk.StringVar(value="Januari")
        self.counts            = {"success": 0, "skipped": 0, "error": 0, "test": 0}
        self._stop_flag        = False

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
        self.csv_card = card1
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
        self.settings_card = card2
        ctk.CTkLabel(card2, text="⚙️  Pengaturan", font=FONT_BOLD,
                     text_color=TEXT).pack(anchor="w", padx=16, pady=(12, 4))

        # Automation type row
        type_row = ctk.CTkFrame(card2, fg_color="transparent")
        type_row.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(type_row, text="Automation:", font=FONT_LABEL,
                     text_color=SUBTEXT).pack(side="left", padx=(0, 6))
        ctk.CTkOptionMenu(type_row, values=AUTOMATION_OPTIONS,
                          variable=self.automation_var,
                          fg_color=SOFT_PINK, button_color=ACCENT,
                          button_hover_color=ACCENT_HOV, text_color=TEXT,
                          dropdown_fg_color=CARD, dropdown_text_color=TEXT,
                          font=FONT_SMALL, corner_radius=10, width=280,
                          command=self._on_automation_change,
                          ).pack(side="left")

        # Kegiatan row (only for Pendaftaran Kegiatan)
        self.kegiatan_row = ctk.CTkFrame(card2, fg_color="transparent")
        self.kegiatan_row.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(self.kegiatan_row, text="Kegiatan:", font=FONT_LABEL,
                     text_color=SUBTEXT).pack(side="left", padx=(0, 6))
        ctk.CTkOptionMenu(self.kegiatan_row, values=list(KEGIATAN_OPTIONS.keys()),
                          variable=self.kegiatan_var,
                          fg_color=SOFT_PINK, button_color=ACCENT,
                          button_hover_color=ACCENT_HOV, text_color=TEXT,
                          dropdown_fg_color=CARD, dropdown_text_color=TEXT,
                          font=FONT_SMALL, corner_radius=10, width=180,
                          ).pack(side="left")

        # Month row (only for Komdat Posyandu)
        self.month_row = ctk.CTkFrame(card2, fg_color="transparent")
        # Hidden initially — shown when Komdat is selected
        ctk.CTkLabel(self.month_row, text="Bulan:", font=FONT_LABEL,
                     text_color=SUBTEXT).pack(side="left", padx=(0, 6))
        ctk.CTkOptionMenu(self.month_row,
                          values=["Januari", "Februari", "Maret", "April",
                                  "Mei", "Juni", "Juli", "Agustus",
                                  "September", "Oktober", "November", "Desember"],
                          variable=self.month_var,
                          fg_color=SOFT_PINK, button_color=ACCENT,
                          button_hover_color=ACCENT_HOV, text_color=TEXT,
                          dropdown_fg_color=CARD, dropdown_text_color=TEXT,
                          font=FONT_SMALL, corner_radius=10, width=180,
                          ).pack(side="left")

        # Mode row
        self._mode_row = ctk.CTkFrame(card2, fg_color="transparent")
        self._mode_row.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkLabel(self._mode_row, text="Mode:", font=FONT_LABEL,
                     text_color=SUBTEXT).pack(side="left", padx=(0, 8))
        for label, value in [("🔍 Test", "test"), ("✅ Submit", "submit")]:
            ctk.CTkRadioButton(self._mode_row, text=label, variable=self.mode_var,
                               value=value, font=FONT_SMALL, text_color=TEXT,
                               fg_color=ACCENT, hover_color=ACCENT_HOV,
                               border_color=ACCENT).pack(side="left", padx=6)

        # ── Start / Stop buttons ────────────────────────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=10)
        self.start_btn = ctk.CTkButton(
            btn_row, text="▶  Mulai Automation", state="disabled",
            fg_color=ACCENT, hover_color=ACCENT_HOV, text_color="white",
            font=("Helvetica", 14, "bold"), height=44, corner_radius=12,
            command=self._start)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.stop_btn = ctk.CTkButton(
            btn_row, text="⏹  Stop", state="disabled",
            fg_color=RED, hover_color=RED_TXT, text_color="white",
            font=("Helvetica", 14, "bold"), height=44, corner_radius=12,
            width=120, command=self._stop)
        self.stop_btn.pack(side="right")

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

    def _stop(self):
        self._stop_flag = True
        self.stop_btn.configure(state="disabled")
        self._log("🛑 Stop requested, akan berhenti setelah row saat ini...")

    def _on_automation_change(self, choice):
        if choice == AUTOMATION_OPTIONS[0]:
            # Pendaftaran Kegiatan: show kegiatan, hide month, show CSV
            self.csv_card.pack(fill="x", padx=24, pady=(18, 6), before=self.settings_card)
            self.kegiatan_row.pack(fill="x", padx=16, pady=(0, 6),
                                   before=self._mode_row)
            self.month_row.pack_forget()
            self.start_btn.configure(state="normal" if self.csv_path.get() else "disabled")
        elif choice == AUTOMATION_OPTIONS[2]:
            # Komdat Posyandu: show month, hide kegiatan, hide CSV
            self.csv_card.pack_forget()
            self.kegiatan_row.pack_forget()
            self.month_row.pack(fill="x", padx=16, pady=(0, 6),
                                before=self._mode_row)
            self.start_btn.configure(state="normal")
        elif choice == AUTOMATION_OPTIONS[3]:
            # Update Alamat CSV: hide kegiatan, hide month, show CSV browse
            self.csv_card.pack(fill="x", padx=24, pady=(18, 6), before=self.settings_card)
            self.kegiatan_row.pack_forget()
            self.month_row.pack_forget()
            self.start_btn.configure(state="normal" if self.csv_path.get() else "disabled")
        else:
            # Pendaftaran Peserta: hide kegiatan & month, show CSV
            self.csv_card.pack(fill="x", padx=24, pady=(18, 6), before=self.settings_card)
            self.kegiatan_row.pack_forget()
            self.month_row.pack_forget()
            self.start_btn.configure(state="normal" if self.csv_path.get() else "disabled")

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
        self._stop_flag = False
        self.start_btn.configure(state="disabled", text="⏳ Berjalan...")
        self.stop_btn.configure(state="normal")
        self.counts = {"success": 0, "skipped": 0, "error": 0, "test": 0}
        self.after(0, self._update_summary)
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        threading.Thread(target=self._run_automation, daemon=True).start()

    # ── Automation thread ────────────────────────────────────────────────────

    def _run_automation(self):
        is_komdat = self.automation_var.get() == AUTOMATION_OPTIONS[2]
        is_update_alamat = self.automation_var.get() == AUTOMATION_OPTIONS[3]

        if is_komdat:
            self._run_komdat_automation()
            return

        if is_update_alamat:
            self._run_update_alamat_automation()
            return

        csv_path    = self.csv_path.get()
        submit_form = self.mode_var.get() == "submit"
        is_peserta  = self.automation_var.get() == AUTOMATION_OPTIONS[1]
        form_url    = PESERTA_FORM_URL if is_peserta else FORM_URL
        kegiatan    = None if is_peserta else KEGIATAN_OPTIONS[self.kegiatan_var.get()]

        try:
            df = pd.read_csv(csv_path, dtype=str).fillna("")
        except Exception as e:
            self._log(f"ERROR membaca CSV: {e}")
            self.after(0, lambda: self.start_btn.configure(state="normal", text="▶  Mulai Automation"))
            return

        self._log(f"✨ Loaded {len(df)} data dari CSV")
        self._log(f"Automation: {self.automation_var.get()}")
        if kegiatan:
            self._log(f"Kegiatan : {self.kegiatan_var.get()}")
        self._log(f"Mode     : {'SUBMIT 🚀' if submit_form else 'TEST 🔍'}")
        self._log("─" * 50)

        try:
            with Stealth().use_sync(sync_playwright()) as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir="browser_session", headless=False,
                    channel="chrome",
                    args=["--disable-blink-features=AutomationControlled"])
                page = browser.pages[0]
                page.goto(form_url)

                self._login_event = threading.Event()
                self.after(0, self._show_login_dialog)
                self._login_event.wait()

                # Validate page
                try:
                    page.locator("#txtnokartu").wait_for(state="visible", timeout=5000)
                    page.locator("#btnCariPeserta").wait_for(state="visible", timeout=5000)
                except Exception:
                    self._log("❌ Halaman tidak valid atau belum login.")
                    browser.close()
                    return

                self._log("🌸 Automation dimulai...")

                # Save the date the user selected so we can restore after reload
                date_selector = "#txt_tglMulai" if is_peserta else "#txttanggal"
                saved_date = page.locator(date_selector).input_value()

                for index, row in df.iterrows():
                    if self._stop_flag:
                        self._log("🛑 Automation dihentikan oleh user.")
                        break
                    no_bpjs = str(row["NO_BPJS"]).strip()
                    self._log(f"[{index + 1}/{len(df)}] {no_bpjs}")
                    try:
                        if is_peserta:
                            result, msg = fill_peserta_row(page, row, index, submit_form, tanggal=saved_date, log=self._log)
                        else:
                            result, msg = self._fill_one_row(page, row, index, submit_form, kegiatan, saved_date=saved_date)
                        self.counts[result] += 1
                        icons = {"success": "✅", "skipped": "⏭", "error": "❌", "test": "🔍"}
                        self._log(f"  {icons[result]} {result.upper()}{': ' + msg if msg else ''}")
                    except Exception as e:
                        self.counts["error"] += 1
                        self._log(f"  ❌ ERROR: {e}")
                        self.after(0, self._update_summary)
                        try:
                            page.goto(form_url, wait_until="domcontentloaded")
                            _dismiss_load_modals(page)
                            page.wait_for_timeout(3000)
                            page.locator("#txtnokartu").wait_for(state="visible", timeout=15000)
                            if saved_date:
                                page.evaluate("""(args) => {
                                    const el = document.querySelector(args.sel);
                                    if (el) { el.value = args.date; el.dispatchEvent(new Event('change', { bubbles: true })); }
                                }""", {"sel": date_selector, "date": saved_date})
                        except Exception:
                            self._log("  ⚠️ Gagal reload halaman, coba sekali lagi...")
                            try:
                                page.wait_for_timeout(5000)
                                page.goto(form_url, wait_until="domcontentloaded")
                                _dismiss_load_modals(page)
                                page.locator("#txtnokartu").wait_for(state="visible", timeout=20000)
                                if saved_date:
                                    page.evaluate("""(args) => {
                                        const el = document.querySelector(args.sel);
                                        if (el) { el.value = args.date; el.dispatchEvent(new Event('change', { bubbles: true })); }
                                    }""", {"sel": date_selector, "date": saved_date})
                            except Exception:
                                self._log("  ⚠️ Browser tertutup, automation dihentikan.")
                                break

                    self.after(0, self._update_summary)
                    page.wait_for_timeout(3000)

                self._log("─" * 50)
                self._log(f"🎀 Selesai! SUCCESS:{self.counts['success']} SKIPPED:{self.counts['skipped']} ERROR:{self.counts['error']} TEST:{self.counts['test']}")

                # Save log to file
                self._save_log()

                self._review_event = threading.Event()
                self.after(0, self._show_review_dialog)
                self._review_event.wait()

                browser.close()

        except Exception as e:
            self._log(f"❌ Automation berhenti: {e}")
        finally:
            self.after(0, lambda: self.start_btn.configure(state="normal", text="▶  Mulai Automation"))
            self.after(0, lambda: self.stop_btn.configure(state="disabled"))

    def _run_komdat_automation(self):
        month_str = self.month_var.get()
        submit_form = self.mode_var.get() == "submit"
        try:
            month_num = parse_month(month_str)
        except ValueError as e:
            self._log(f"❌ {e}")
            self.after(0, lambda: self.start_btn.configure(state="normal", text="▶  Mulai Automation"))
            return

        self._log(f"🏥 Komdat Posyandu — Bulan: {month_str} ({month_num})")
        self._log(f"Mode     : {'SUBMIT 🚀' if submit_form else 'TEST 🔍'}")
        self._log("─" * 50)

        try:
            with Stealth().use_sync(sync_playwright()) as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir="browser_session_komdat", headless=False,
                    channel="chrome",
                    args=["--disable-blink-features=AutomationControlled"])
                page = browser.pages[0]
                page.goto(KOMDAT_LOGIN_URL)

                self._login_event = threading.Event()
                self.after(0, self._show_komdat_login_dialog)
                self._login_event.wait()

                # Click Edit button on the Kegiatan Posyandu page
                self._log("🔄 Klik Edit...")
                navigate_to_table(page)
                self._log("✅ Table loaded")

                # Run the automation
                def _on_progress(proc, skip, err):
                    if submit_form:
                        self.counts["success"] = proc
                    else:
                        self.counts["test"] = proc
                    self.counts["skipped"] = skip
                    self.counts["error"] = err
                    self.after(0, self._update_summary)

                processed, skipped, errors = run_komdat(
                    page, month_num, submit_form, self._log, lambda: self._stop_flag,
                    on_progress=_on_progress)

                if submit_form:
                    self.counts["success"] = processed
                else:
                    self.counts["test"] = processed
                self.counts["skipped"] = skipped
                self.counts["error"] = errors
                self.after(0, self._update_summary)

                self._log("─" * 50)
                self._log(f"🎀 Selesai! Processed: {processed}, Skipped: {skipped}, Error: {errors}")
                self._save_log()

                self._review_event = threading.Event()
                self.after(0, self._show_review_dialog)
                self._review_event.wait()

                browser.close()

        except Exception as e:
            self._log(f"❌ Automation berhenti: {e}")
        finally:
            self.after(0, lambda: self.start_btn.configure(state="normal", text="▶  Mulai Automation"))
            self.after(0, lambda: self.stop_btn.configure(state="disabled"))

    def _run_update_alamat_automation(self):
        import os

        csv_path = self.csv_path.get()
        submit_form = self.mode_var.get() == "submit"

        if not csv_path or not os.path.isfile(csv_path):
            self._log("❌ File CSV tidak valid")
            self.after(0, lambda: self.start_btn.configure(state="normal", text="▶  Mulai Automation"))
            return

        self._log(f"📍 Update Alamat CSV")
        self._log(f"File: {os.path.basename(csv_path)}")
        self._log(f"Mode     : {'SUBMIT 🚀 (update CSV)' if submit_form else 'TEST 🔍 (hanya cari)'}")
        self._log("─" * 50)

        try:
            with Stealth().use_sync(sync_playwright()) as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir="browser_session_epuskesmas", headless=False,
                    channel="chrome",
                    args=["--disable-blink-features=AutomationControlled"])
                page = browser.pages[0]
                page.goto(EPUSKESMAS_LOGIN_URL)

                self._login_event = threading.Event()
                self.after(0, self._show_epuskesmas_login_dialog)
                self._login_event.wait()

                # Navigate to pasien page
                page.goto(EPUSKESMAS_PASIEN_URL)
                try:
                    page.locator('#form_search').wait_for(state="visible", timeout=10000)
                except Exception:
                    self._log("❌ Halaman pasien tidak valid atau belum login.")
                    browser.close()
                    return

                self._log("🌸 Automation dimulai...")

                counts = run_update_alamat(page, csv_path, submit_form=submit_form, log=self._log, stop_check=lambda: self._stop_flag)

                # Update summary
                self.counts["success"] = counts["success"]
                self.counts["skipped"] = counts["skipped"] + counts["not_found"]
                self.counts["error"] = counts["error"]
                self.after(0, self._update_summary)

                self._log("─" * 50)
                self._log(f"🎀 Selesai! Updated: {counts['success']}, "
                          f"Not Found: {counts['not_found']}, "
                          f"Skipped: {counts['skipped']}, "
                          f"Error: {counts['error']}")
                self._save_log()

                self._review_event = threading.Event()
                self.after(0, self._show_review_dialog)
                self._review_event.wait()

                browser.close()

        except Exception as e:
            self._log(f"❌ Automation berhenti: {e}")
        finally:
            self.after(0, lambda: self.start_btn.configure(state="normal", text="▶  Mulai Automation"))
            self.after(0, lambda: self.stop_btn.configure(state="disabled"))

    def _show_epuskesmas_login_dialog(self):
        messagebox.showinfo("Login Required 📍",
                            "Login ke ePuskesmas,\nlalu klik OK untuk mulai ✨")
        self._login_event.set()

    def _show_login_dialog(self):
        messagebox.showinfo("Login Required 🌸",
                            "Login dulu dan atur tanggal,\nlalu klik OK untuk mulai ✨")
        self._login_event.set()

    def _show_komdat_login_dialog(self):
        messagebox.showinfo("Login Required 🏥",
                            "Login dulu, lalu buka halaman\n'Kegiatan Posyandu'.\n\nKlik OK setelah sudah di halaman tersebut ✨")
        self._login_event.set()

    def _show_review_dialog(self):
        messagebox.showinfo("Selesai 🎀",
                            "Automation selesai!\nCek hasil di browser, lalu klik OK untuk menutup 💖")
        self._review_event.set()

    def _save_log(self):
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        automation_name = "kegiatan" if self.automation_var.get() == AUTOMATION_OPTIONS[0] else \
                         "komdat" if self.automation_var.get() == AUTOMATION_OPTIONS[2] else \
                         "update_alamat" if self.automation_var.get() == AUTOMATION_OPTIONS[3] else "peserta"
        filename = f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_{automation_name}.txt"
        log_content = self.log_box.get("1.0", "end").strip()
        with open(os.path.join(log_dir, filename), "w") as f:
            f.write(log_content)
        self._log(f"📁 Log disimpan: logs/{filename}")

    def _fill_one_row(self, page, row, index, submit_form, kegiatan, saved_date=None):
        no_bpjs = str(row["NO_BPJS"]).strip()
        tinggi_badan, berat_badan = split_value(row["TB_BB"])
        lingkar_perut = str(row["LP"]).strip()
        sistole, diastole = split_value(row["TD"])

        # Wait for Turnstile token (retry up to 3 times)
        from pcare_pendaftaran_peserta import _wait_turnstile
        turnstile_ready = _wait_turnstile(page, timeout=10000)
        if not turnstile_ready:
            # Token not ready — notify user to click Turnstile checkbox
            self._log("  ⚠️ Klik checkbox Turnstile di browser, menunggu...")
            try:
                import platform
                if platform.system() == "Darwin":
                    import subprocess
                    subprocess.Popen(['osascript', '-e',
                        'display notification "Klik checkbox Turnstile di browser!" with title "PCare Automation" sound name "Ping"'])
                elif platform.system() == "Windows":
                    from tkinter import messagebox as _mb
                    # Show non-blocking messagebox in a thread so it doesn't freeze automation
                    import threading
                    threading.Thread(target=lambda: _mb.showwarning(
                        "PCare Automation", "Klik checkbox Turnstile di browser!"), daemon=True).start()
                else:
                    print("\a")  # terminal bell
            except Exception:
                pass
            # Wait indefinitely for user to click checkbox (max 10 min)
            turnstile_ready = _wait_turnstile(page, timeout=600000)
        if not turnstile_ready:
            return "skipped", "Turnstile token belum siap (timeout 10 menit)"

        # Ensure no overlay is blocking before interacting with form
        _dismiss_load_modals(page, after_reload=False)

        page.locator("#txtnokartu").fill(no_bpjs)
        page.locator("#btnCariPeserta").click()

        # Clear token value after search so next check waits for fresh token
        page.evaluate("""() => {
            const el = document.querySelector('[name="cf-turnstile-response"]');
            if (el) el.value = '';
        }""")

        try:
            page.locator("#lblnmpst:not(:empty), .alert-danger, .alert-warning").first.wait_for(state="visible", timeout=20000)
        except PlaywrightTimeoutError:
            # No response — Turnstile token expired
            # Auto-retry: click Cari every 8 seconds until response (max ~1 min)
            self._log("  ⚠️ Token expired, retry klik Cari otomatis...")
            got_response = False
            for retry in range(8):
                page.wait_for_timeout(8000)  # wait 8s for token to regenerate
                # Make sure nomor is still in field
                page.locator("#txtnokartu").fill(no_bpjs)
                page.locator("#btnCariPeserta").click()
                # Clear token after click for next iteration
                page.evaluate("""() => {
                    const el = document.querySelector('[name="cf-turnstile-response"]');
                    if (el) el.value = '';
                }""")
                try:
                    page.locator("#lblnmpst:not(:empty), .alert-danger, .alert-warning").first.wait_for(state="visible", timeout=10000)
                    got_response = True
                    break
                except PlaywrightTimeoutError:
                    self._log(f"    retry {retry + 1}/8...")
                    continue
            if not got_response:
                page.locator("#txtnokartu").fill("")
                return "skipped", "tidak ada respons setelah 8 retry"

        # Small buffer to allow delayed modals (e.g. non-aktif) to appear after patient data loads
        page.wait_for_timeout(800)

        # Dismiss system modals that may appear during/after search (not patient-specific)
        _dismiss_load_modals(page, after_reload=False)

        alert = page.locator(".alert-danger, .alert-warning, .bootbox-body").first
        if alert.is_visible():
            msg = alert.inner_text().strip()
            # Skip only for patient-specific alerts, not system modals
            if "Belum Entri Pelayanan" in msg or "HFIS" in msg or "pakta integritas" in msg.lower():
                # System modal — dismiss and continue
                dismiss = page.locator(".bootbox-cancel, .bootbox-accept, .bootbox .btn-primary, .alert .close, [data-notify='dismiss']").first
                if dismiss.is_visible():
                    dismiss.click()
                    page.wait_for_timeout(500)
            elif "erifikasi keamanan gagal" in msg:
                # Turnstile verification failed — dismiss and retry search
                dismiss = page.locator(".bootbox-cancel, .bootbox-accept, .bootbox .btn-primary, .alert .close").first
                if dismiss.is_visible():
                    dismiss.click()
                    page.wait_for_timeout(500)
                self._log("  ⚠️ Verifikasi gagal, retry...")
                page.locator("#txtnokartu").fill("")
                page.wait_for_timeout(8000)
                page.locator("#txtnokartu").fill(no_bpjs)
                page.locator("#btnCariPeserta").click()
                page.evaluate("""() => {
                    const el = document.querySelector('[name="cf-turnstile-response"]');
                    if (el) el.value = '';
                }""")
                try:
                    page.locator("#lblnmpst:not(:empty), .alert-danger, .alert-warning").first.wait_for(state="visible", timeout=15000)
                    # Check if it failed again
                    alert2 = page.locator(".alert-danger, .alert-warning, .bootbox-body").first
                    if alert2.is_visible():
                        msg2 = alert2.inner_text().strip()
                        dismiss2 = page.locator(".bootbox-cancel, .bootbox-accept, .bootbox .btn-primary, .alert .close").first
                        if dismiss2.is_visible():
                            dismiss2.click()
                            page.wait_for_timeout(500)
                        page.locator("#txtnokartu").fill("")
                        return "skipped", msg2
                except PlaywrightTimeoutError:
                    page.locator("#txtnokartu").fill("")
                    return "skipped", "tidak ada respons setelah retry verifikasi"
            else:
                # Patient-specific alert — dismiss without reload
                dismiss = page.locator(".bootbox-cancel, .bootbox-accept, .bootbox .btn-primary, .alert .close").first
                if dismiss.is_visible():
                    dismiss.click()
                    page.wait_for_timeout(500)
                # Clear form for next patient (no reload needed)
                page.locator("#txtnokartu").fill("")
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
                # Click Batal to reset form instead of reloading
                try:
                    page.locator("#Aktivitas").click()
                    page.wait_for_timeout(500)
                except Exception:
                    pass
                page.locator("#txtnokartu").fill("")
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
