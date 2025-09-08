import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import time
import json
import os
from datetime import datetime
from typing import Optional, Dict, List
from trading_bot import BTCTurkTradingBot
from trading_strategy import TradingStrategy, RiskManager
from loguru import logger
# Matplotlib kaldırıldı - grafik artık yok

# CustomTkinter tema ayarları
ctk.set_appearance_mode("dark")  # "dark" veya "light"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class TradingBotGUI:
    """
    BTCTurk Trading Bot için modern GUI arayüzü - Sekme yapısı ile
    """
    
    def __init__(self, root, bot, settings_manager, error_handler, app):
        # Ana pencere
        self.root = root
        self.bot = bot
        self.settings_manager = settings_manager
        self.error_handler = error_handler
        self.app = app
        
        # Bot ve strateji nesneleri
        self.strategy = TradingStrategy()
        # Risk manager'ı ayarlardan oluştur
        settings = self.settings_manager.get_all_settings()
        self.risk_manager = RiskManager(
            max_daily_loss=settings.get('max_daily_loss', 5.0),
            max_position_size=settings.get('max_position_size', 50.0)
        )
        
        # GUI değişkenleri
        self.selected_coin = ctk.StringVar(value="BTCTRY")
        self.target_percentage = ctk.StringVar(value="2.0")
        self.trade_amount = ctk.StringVar(value="100.0")
        self.api_key = ctk.StringVar()
        self.api_secret = ctk.StringVar()
        
        # Durum değişkenleri
        self.current_price = ctk.StringVar(value="0.00")
        self.current_profit = ctk.StringVar(value="0.00%")
        self.bot_status = ctk.StringVar(value="Durduruldu")
        self.balance_info = ctk.StringVar(value="Bakiye: 0.00 TRY")
        
        # API Profilleri
        self.api_profiles = {}
        self.current_profile = ctk.StringVar(value="Varsayılan")
        
        # İşlem geçmişi
        self.trade_history = []
        
        # Log bölümlerinin açık/kapalı durumu
        self.log_sections_expanded = {
            "bot_logs": True,
            "api_logs": False,
            "error_logs": False,
            "trade_logs": True
        }
        
        # Grafik verileri
        self.price_data = []
        self.time_data = []
        
        # Widget'ları oluştur
        self.create_widgets()
        
        # Başlangıçta kaydedilmiş API anahtarlarını yükle
        self.load_saved_api_keys()
        
    def create_widgets(self):
        """
        GUI bileşenlerini oluşturur - Sekme yapısı ile
        """
        # Ana frame
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Sekme yapısı oluştur
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Sekmeler
        self.tab_trading = self.tabview.add("Trading")
        self.tab_api_profiles = self.tabview.add("API Profilleri")
        self.tab_history = self.tabview.add("İşlem Geçmişi")
        self.tab_logs = self.tabview.add("Log Kayıtları")
        
        # Her sekme için içerik oluştur
        self.create_trading_tab()
        self.create_api_profiles_tab()
        self.create_history_tab()
        self.create_logs_tab()
    
    def create_settings_panel(self):
        """
        Ayarlar panelini oluşturur
        """
        # Scrollable frame oluştur
        self.settings_scroll = ctk.CTkScrollableFrame(self.left_panel)
        self.settings_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Başlık
        title = ctk.CTkLabel(self.settings_scroll, text="Bot Ayarları", 
                           font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(10, 20))
        
        # API Ayarları
        api_frame = ctk.CTkFrame(self.settings_scroll)
        api_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(api_frame, text="API Ayarları", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        ctk.CTkLabel(api_frame, text="API Key:").pack(anchor="w", padx=10)
        self.api_key_entry = ctk.CTkEntry(api_frame, textvariable=self.api_key, 
                                         placeholder_text="BTCTurk API Key", show="*")
        self.api_key_entry.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(api_frame, text="API Secret:").pack(anchor="w", padx=10)
        self.api_secret_entry = ctk.CTkEntry(api_frame, textvariable=self.api_secret, 
                                           placeholder_text="BTCTurk API Secret", show="*")
        self.api_secret_entry.pack(fill="x", padx=10, pady=(5, 15))
        
        # API anahtarı butonları
        button_frame = ctk.CTkFrame(api_frame)
        button_frame.pack(fill="x", padx=10, pady=(5, 15))
        
        # Kaydet butonu
        self.save_api_btn = ctk.CTkButton(button_frame, text="Kaydet", 
                                        command=self.save_api_keys, width=80)
        self.save_api_btn.pack(side="left", padx=(0, 5))
        
        # Yükle butonu
        self.load_api_btn = ctk.CTkButton(button_frame, text="Yükle", 
                                        command=self.load_api_keys, width=80)
        self.load_api_btn.pack(side="left", padx=5)
        
        # Bağlantı butonu
        self.connect_btn = ctk.CTkButton(button_frame, text="Bağlan", 
                                       command=self.connect_to_api, width=80)
        self.connect_btn.pack(side="right")
        
        # Trading Ayarları
        trading_frame = ctk.CTkFrame(self.settings_scroll)
        trading_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(trading_frame, text="Trading Ayarları", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        # Coin seçimi
        ctk.CTkLabel(trading_frame, text="Coin Çifti:").pack(anchor="w", padx=10)
        # BTCTurk'te mevcut olan tüm coin çiftleri
        default_coins = [
            # Ana coin çiftleri (TRY)
            "BTCTRY", "ETHTRY", "ADATRY", "DOGETRY", "XRPTRY", "LTCTRY", 
            "BNBTRY", "AVXTRY", "SOLTRY", "MATTRY", "DOTRY", "LINKTRY",
            "UNICTRY", "ATOMTRY", "FILETRY", "SANDTRY", "MANATRY", "AXSTRY",
            "CHZTRY", "BATSTRY", "ZRXTRY", "OMGTRY", "HOTTRY", "ENJINTRY",
            "NEOTRY", "XLMTRY", "EOSTRY", "TRXTRY", "VETRY", "ZIGTRY",
            
            # Yeni eklenen coinler (TRY)
            "ASRTRY", "NMRTRY", "PYTHTRY", "API3TRY", "PUMPTRY", "WLDTRY",
            "MEMETRY", "RLCTRY", "SKLTRY", "LPTTRY", "AIXBTTRY", "FLRTRY",
            "PEPETRY", "VANATRY", "SPKTRY", "BONKTRY", "ENATRY", "ATMTRY",
            "MAGICTRY", "XCNTRY", "PENGUTRY", "CTSITRY", "UMATRY", "EIGENTRY",
            "BANDTRY", "PNUTTRY", "TRUMPTRY", "FETTRY", "JUVTRY", "SPELLTRY",
            "RADTRY", "OMTRY", "HNTTRY", "ALGOTRY", "ANKRTRY", "MASKTRY",
            "STRKTRY", "SUPERTRY", "CHILTRY", "SHIBTRY", "APETRY", "BNTTRY",
            "OPTRY", "ZKTRY", "ZROTRY", "TONTRY", "SNXTRY", "LUNATRY",
            
            # USDT çiftleri
            "BTCUSDT", "ETHUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT",
            "SOLUSDT", "DOTUSDT", "LINKUSDT", "LTCUSDT", "UNIUSDT", "ATOMUSDT",
            "FILUSDT", "TRXUSDT", "XLMUSDT", "EOSUSDT", "VETUSDT", "ALGOUSDT",
            "ANKRUSDT", "MASKUSDT", "LPTUSDT", "SNXUSDT", "LUNAUSDT", "HOTUSDT",
            "ASRUSDT", "NMRUSDT", "PYTHUSDT", "API3USDT", "PUMPUSDT", "WLDUSDT",
            "ENAUSDT", "PEPEUSDT", "AVAXUSDT", "PYTHUSDT"
        ]
        self.coin_combo = ctk.CTkComboBox(trading_frame, 
                                         values=default_coins,
                                         variable=self.selected_coin)
        self.coin_combo.pack(fill="x", padx=10, pady=5)
        
        # Hedef kar yüzdesi
        ctk.CTkLabel(trading_frame, text="Hedef Kar (%):").pack(anchor="w", padx=10)
        self.target_entry = ctk.CTkEntry(trading_frame, textvariable=self.target_percentage)
        self.target_entry.pack(fill="x", padx=10, pady=5)
        
        # İşlem miktarı
        ctk.CTkLabel(trading_frame, text="İşlem Miktarı (TRY):").pack(anchor="w", padx=10)
        self.amount_entry = ctk.CTkEntry(trading_frame, textvariable=self.trade_amount)
        self.amount_entry.pack(fill="x", padx=10, pady=(5, 15))
        
        # Kontrol butonları
        button_frame = ctk.CTkFrame(self.settings_scroll)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        self.start_btn = ctk.CTkButton(button_frame, text="Bot'u Başlat", 
                                     command=self.start_bot, 
                                     fg_color="green", hover_color="darkgreen")
        self.start_btn.pack(fill="x", padx=10, pady=5)
        
        self.stop_btn = ctk.CTkButton(button_frame, text="Bot'u Durdur", 
                                    command=self.stop_bot,
                                    fg_color="red", hover_color="darkred")
        self.stop_btn.pack(fill="x", padx=10, pady=5)
        
        # Bakiye yenile butonu
        self.refresh_btn = ctk.CTkButton(button_frame, text="Bakiye Yenile", 
                                       command=self.refresh_balance)
        self.refresh_btn.pack(fill="x", padx=10, pady=5)
    

    
    def create_status_panel(self):
        """
        Durum panelini oluşturur
        """
        # Başlık
        title = ctk.CTkLabel(self.right_panel, text="Bot Durumu", 
                           font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=(20, 30))
        
        # Durum bilgileri
        status_frame = ctk.CTkFrame(self.right_panel)
        status_frame.pack(fill="x", padx=20, pady=10)
        
        # Bot durumu
        ctk.CTkLabel(status_frame, text="Durum:", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        self.status_label = ctk.CTkLabel(status_frame, textvariable=self.bot_status)
        self.status_label.pack(anchor="w", padx=20)
        
        # Güncel fiyat
        ctk.CTkLabel(status_frame, text="Güncel Fiyat:", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        self.price_label = ctk.CTkLabel(status_frame, textvariable=self.current_price,
                                       font=ctk.CTkFont(size=18, weight="bold"))
        self.price_label.pack(anchor="w", padx=20)
        
        # Kar/Zarar
        ctk.CTkLabel(status_frame, text="Kar/Zarar:", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        self.profit_label = ctk.CTkLabel(status_frame, textvariable=self.current_profit,
                                        font=ctk.CTkFont(size=16, weight="bold"))
        self.profit_label.pack(anchor="w", padx=20)
        
        # Bakiye
        ctk.CTkLabel(status_frame, text="Bakiye:", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        self.balance_label = ctk.CTkLabel(status_frame, textvariable=self.balance_info)
        self.balance_label.pack(anchor="w", padx=20, pady=(0, 15))
        
        # Performans istatistikleri
        perf_frame = ctk.CTkFrame(self.right_panel)
        perf_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(perf_frame, text="Performans", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        self.perf_text = ctk.CTkTextbox(perf_frame, height=150)
        self.perf_text.pack(fill="x", padx=10, pady=(5, 15))
    
    def create_log_panel(self):
        """
        Log panelini oluşturur
        """
        # Başlık
        title = ctk.CTkLabel(self.bottom_panel, text="İşlem Logları", 
                           font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(pady=(10, 5))
        
        # Log text widget
        self.log_text = ctk.CTkTextbox(self.bottom_panel, height=150)
        self.log_text.pack(fill="both", expand=True, padx=20, pady=(5, 20))
    
    def setup_layout(self):
        """
        Layout'u düzenler - 2 kolonlu tasarım
        """
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Grid layout - 2 kolon
        self.main_frame.grid_columnconfigure(0, weight=1, minsize=400)  # Sol panel genişletildi
        self.main_frame.grid_columnconfigure(1, weight=1, minsize=400)  # Sağ panel genişletildi
        self.main_frame.grid_rowconfigure(0, weight=4)     # Üst kısım
        self.main_frame.grid_rowconfigure(1, weight=1)     # Alt panel
        
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 3))
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(3, 0))
        self.bottom_panel.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))
    
    def connect_to_api(self):
        """
        BTCTurk API'ye bağlanır
        """
        api_key = self.api_key.get().strip()
        api_secret = self.api_secret.get().strip()
        
        if not api_key or not api_secret:
            messagebox.showerror("Hata", "API Key ve Secret gerekli!")
            return
        
        # Bağlantı durumunu güncelle
        self.connect_btn.configure(text="Bağlanıyor...", state="disabled")
        self.log_message("API'ye bağlanılıyor...")
        
        # Threading ile arka planda bağlan
        def connect_thread():
            try:
                # Bot'u oluştur
                self.bot = BTCTurkTradingBot(api_key, api_secret)
                
                # Callback'leri ayarla
                self.bot.set_callbacks(
                    price_callback=self.on_price_update,
                    status_callback=self.on_status_update,
                    trade_callback=self.on_trade_update,
                    balance_callback=self.refresh_balance
                )
                
                # Bağlantıyı test et
                pairs = self.bot.get_available_pairs()
                if pairs:
                    # Tüm coinleri göster, TRY çiftlerini önce sırala
                    try_pairs = [pair for pair in pairs if pair.endswith('TRY')]
                    other_pairs = [pair for pair in pairs if not pair.endswith('TRY')]
                    all_pairs = try_pairs + other_pairs
                    
                    # GUI güncellemelerini ana thread'de yap
                    self.root.after(0, lambda: self.coin_combo.configure(values=all_pairs))
                    self.root.after(0, lambda: self.log_message(f"API bağlantısı başarılı! {len(pairs)} coin çifti bulundu."))
                    self.root.after(0, lambda: self.log_message(f"TRY çiftleri: {len(try_pairs)}, Diğer çiftler: {len(other_pairs)}"))
                    self.root.after(0, lambda: self.connect_btn.configure(text="Bağlandı", state="disabled"))
                    self.root.after(0, self.refresh_balance)
                    
                    # Bot butonlarını aktif et
                    self.root.after(0, lambda: self.start_btn.configure(state="normal"))
                    self.root.after(0, lambda: self.stop_btn.configure(state="normal"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Hata", "API bağlantısı başarısız!"))
                    self.root.after(0, lambda: self.connect_btn.configure(text="Bağlan", state="normal"))
                    
            except Exception as e:
                if "Authentication" in str(e):
                    error_msg = "API anahtarları geçersiz! Lütfen doğru API Key ve Secret girin."
                    self.root.after(0, lambda: messagebox.showerror("Kimlik Doğrulama Hatası", error_msg))
                    self.root.after(0, lambda: self.log_message("❌ API kimlik doğrulama başarısız - Anahtarları kontrol edin"))
                else:
                    error_msg = f"Bağlantı hatası: {str(e)}"
                    self.root.after(0, lambda: messagebox.showerror("Hata", error_msg))
                    self.root.after(0, lambda: self.log_message(f"API bağlantı hatası: {e}"))
                
                self.root.after(0, lambda: self.connect_btn.configure(text="Bağlan", state="normal"))
                logger.error(f"API bağlantı hatası: {e}")
        
        # Thread'i başlat
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def start_bot(self):
        """
        Bot'u başlatır
        """
        if not self.bot:
            messagebox.showerror("Hata", "Önce API'ye bağlanın!")
            return
        
        try:
            coin = self.selected_coin.get()
            
            # String değerleri float'a çevir
            try:
                target_str = self.target_entry.get().strip()
                # Yüzde işaretini kaldır
                if target_str.endswith('%'):
                    target_str = target_str[:-1]
                target = float(target_str)
            except (ValueError, AttributeError):
                target = self.target_percentage.get()
            
            try:
                amount_str = self.amount_entry.get().strip()
                amount = float(amount_str)
            except (ValueError, AttributeError):
                amount = self.trade_amount.get()
            
            if target <= 0 or amount <= 0:
                messagebox.showerror("Hata", "Geçerli değerler girin!")
                return
            
            # Risk kontrolü
            balance = self.get_try_balance()
            can_trade, reason = self.risk_manager.can_trade(amount, balance)
            
            if not can_trade:
                messagebox.showerror("Risk Uyarısı", reason)
                return
            
            # Bot'u başlat
            threading.Thread(target=self.bot.start_trading, 
                           args=(coin, target, amount), daemon=True).start()
            
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            
            self.log_message(f"Bot başlatıldı: {coin} - Hedef: %{target} - Miktar: {amount} TRY")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Bot başlatma hatası: {str(e)}")
            logger.error(f"Bot başlatma hatası: {e}")
    
    def stop_bot(self):
        """
        Bot'u durdurur
        """
        if self.bot:
            self.bot.stop_trading()
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.log_message("Bot durduruldu")
    
    def refresh_balance(self):
        """
        Bakiye bilgilerini yeniler (thread-safe)
        """
        if not self.bot:
            return
        
        def update_balance():
            try:
                balance = self.bot.get_account_balance()
                try_balance = balance.get('TRY', {}).get('free', '0')
                self.balance_info.set(f"Bakiye: {float(try_balance):.2f} TRY")
                
                # Bakiye label'ını da güncelle
                if hasattr(self, 'balance_label'):
                    self.balance_label.configure(text=f"Bakiye: {float(try_balance):.2f} TRY")
                
                logger.info(f"Bakiye güncellendi: {float(try_balance):.2f} TRY")
                
            except Exception as e:
                logger.error(f"Bakiye yenileme hatası: {e}")
        
        # Ana thread'de çalıştır
        self.root.after(0, update_balance)
    
    def get_try_balance(self) -> float:
        """
        TRY bakiyesini döndürür
        """
        if not self.bot:
            return 0.0
        
        try:
            balance = self.bot.get_account_balance()
            return float(balance.get('TRY', {}).get('free', '0'))
        except:
            return 0.0
    
    def on_price_update(self, price: float, profit_pct: float):
        """
        Fiyat güncellemesi callback'i
        """
        self.current_price.set(f"{price:.2f} TRY")
        
        # Kar/zarar bilgisini güncelle
        if profit_pct != 0:
            color = "green" if profit_pct > 0 else "red"
            self.current_profit.set(f"{profit_pct:+.2f}%")
            if hasattr(self, 'profit_label'):
                self.profit_label.configure(text_color=color)
        else:
            self.current_profit.set("0.00%")
            if hasattr(self, 'profit_label'):
                self.profit_label.configure(text_color="white")
        
        # Fiyat label'ını da güncelle
        if hasattr(self, 'price_label'):
            self.price_label.configure(text=f"Güncel Fiyat: {price:.2f} TRY")
        
        # Grafik verilerini güncelle
        self.price_data.append(price)
        self.time_data.append(datetime.now())
        
        # Son 100 veriyi tut
        if len(self.price_data) > 100:
            self.price_data = self.price_data[-100:]
            self.time_data = self.time_data[-100:]
        
        # Strateji verilerini güncelle
        self.strategy.add_price_point(price)
    
    def on_status_update(self, status: str):
        """
        Bot durumu güncellendiğinde çağrılır
        """
        self.bot_status.set(status)
        self.log_message(f"Durum: {status}")
    
    def update_status(self, status: str, status_type: str = "info"):
        """
        Bot durumunu günceller (alias for on_status_update)
        
        Args:
            status: Durum mesajı
            status_type: Durum tipi (info, success, error, warning, trading, stopped, paused, emergency)
        """
        # Durum tipine göre renk ayarla
        color_map = {
            "success": "green",
            "error": "red", 
            "warning": "orange",
            "trading": "blue",
            "stopped": "gray",
            "paused": "yellow",
            "emergency": "red",
            "info": "white"
        }
        
        color = color_map.get(status_type, "white")
        
        # Status label'ı güncelle
        self.bot_status.set(status)
        if hasattr(self, 'status_label'):
            self.status_label.configure(text_color=color)
        
        self.log_message(f"Durum: {status}")
    
    def on_trade_update(self, trade_info: str):
        """
        İşlem güncellemesi callback'i
        """
        self.log_message(trade_info)
    
    def log_message(self, message: str):
        """
        Log mesajı ekler
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert("end", log_entry)
        self.log_text.see("end")
    

    
    def update_performance(self):
        """
        Performans istatistiklerini günceller
        """
        stats = self.strategy.get_performance_stats()
        
        perf_text = f"""Toplam İşlem: {stats['total_trades']}
Karlı İşlem: {stats['profitable_trades']}
Zararlı İşlem: {stats['loss_trades']}
Ortalama Kar: %{stats['average_profit']:.2f}
Toplam Kar: %{stats['total_profit']:.2f}
Başarı Oranı: %{stats['win_rate']:.1f}"""
        
        self.perf_text.delete("1.0", "end")
        self.perf_text.insert("1.0", perf_text)
    
    def update_gui(self):
        """
        GUI'yi periyodik olarak günceller
        """
        # Bot bağlıysa ve coin seçiliyse fiyat güncelle
        if self.bot and hasattr(self.bot, 'client') and self.selected_coin.get():
            try:
                current_price = self.bot.get_current_price(self.selected_coin.get())
                if current_price > 0:
                    # Fiyat callback'ini manuel çağır
                    profit_pct = 0
                    if self.bot.is_position_open and self.bot.buy_price > 0:
                        profit_pct = ((current_price - self.bot.buy_price) / self.bot.buy_price) * 100
                    
                    self.on_price_update(current_price, profit_pct)
                else:
                    # Fiyat alınamazsa "Fiyat verisi bekleniyor..." göster
                    self.current_price.set("Fiyat verisi bekleniyor...")
            except Exception as e:
                self.current_price.set("Fiyat verisi bekleniyor...")
                logger.debug(f"Fiyat güncelleme hatası: {e}")
        else:
            # Bot bağlı değilse demo fiyat verisi ekle (test için)
            if not self.price_data:
                import random
                base_price = 3500000  # ASRTRY için örnek fiyat
                demo_price = base_price + random.uniform(-50000, 50000)
                self.on_price_update(demo_price, 0)
        
        # Grafik kaldırıldı - daha hızlı takip için
        
        # Performans istatistiklerini güncelle
        self.update_performance()
        
        # 2 saniye sonra tekrar çağır
        self.root.after(2000, self.update_gui)
    
    def save_api_keys(self):
        """
        API anahtarlarını ayarlara kaydeder
        """
        try:
            api_key = self.api_key.get().strip()
            api_secret = self.api_secret.get().strip()
            
            if not api_key or not api_secret:
                messagebox.showwarning("Uyarı", "API Key ve Secret boş olamaz!")
                return
            
            # Ayarlara kaydet
            self.settings_manager.settings.api_key = api_key
            self.settings_manager.settings.api_secret = api_secret
            self.settings_manager.save_settings()
            
            messagebox.showinfo("Başarılı", "API anahtarları başarıyla kaydedildi!")
            self.log_message("API anahtarları kaydedildi")
            
        except Exception as e:
            messagebox.showerror("Hata", f"API anahtarları kaydedilemedi: {str(e)}")
            logger.error(f"API kaydetme hatası: {e}")
    
    def load_api_keys(self):
        """
        Kaydedilmiş API anahtarlarını yükler
        """
        try:
            # Ayarları yükle
            self.settings_manager.load_settings()
            
            api_key = self.settings_manager.settings.api_key
            api_secret = self.settings_manager.settings.api_secret
            
            if api_key and api_secret:
                self.api_key.set(api_key)
                self.api_secret.set(api_secret)
                messagebox.showinfo("Başarılı", "API anahtarları başarıyla yüklendi!")
                self.log_message("API anahtarları yüklendi")
            else:
                messagebox.showwarning("Uyarı", "Kaydedilmiş API anahtarı bulunamadı!")
                
        except Exception as e:
             messagebox.showerror("Hata", f"API anahtarları yüklenemedi: {str(e)}")
             logger.error(f"API yükleme hatası: {e}")
    
    def load_saved_api_keys(self):
        """
        Başlangıçta kaydedilmiş API anahtarlarını sessizce yükler
        """
        try:
            # Ayarları yükle
            self.settings_manager.load_settings()
            
            api_key = self.settings_manager.settings.api_key
            api_secret = self.settings_manager.settings.api_secret
            
            if api_key and api_secret:
                self.api_key.set(api_key)
                self.api_secret.set(api_secret)
                logger.info("Kaydedilmiş API anahtarları yüklendi")
                
        except Exception as e:
            logger.debug(f"API anahtarları yüklenemedi: {e}")
    
    def load_api_profiles(self):
        """
        API profillerini yükler
        """
        # Dosyadan profilleri yükle
        self.load_api_profiles_from_file()
        
        # Varsayılan profil yoksa oluştur
        if not self.api_profiles:
            self.api_profiles = {
                "Varsayılan": {
                    "api_key": "",
                    "api_secret": "",
                    "description": "Varsayılan API profili",
                    "created_at": datetime.now().isoformat()
                }
            }
            self.save_api_profiles_to_file()
    
    def create_trading_tab(self):
        """
        Trading sekmesini oluşturur
        """
        # Ana frame
        main_frame = ctk.CTkFrame(self.tab_trading)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Sol panel - Ayarlar
        left_panel = ctk.CTkFrame(main_frame)
        left_panel.pack(side="left", fill="y", padx=(0, 5))
        
        # API Ayarları
        api_frame = ctk.CTkFrame(left_panel)
        api_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(api_frame, text="API Ayarları", font=("Arial", 16, "bold")).pack(pady=5)
        
        ctk.CTkLabel(api_frame, text="API Key:").pack(anchor="w", padx=10)
        self.api_key_entry = ctk.CTkEntry(api_frame, textvariable=self.api_key, width=300, show="*")
        self.api_key_entry.pack(padx=10, pady=2)
        
        ctk.CTkLabel(api_frame, text="API Secret:").pack(anchor="w", padx=10)
        self.api_secret_entry = ctk.CTkEntry(api_frame, textvariable=self.api_secret, width=300, show="*")
        self.api_secret_entry.pack(padx=10, pady=2)
        
        # Trading Ayarları
        trading_frame = ctk.CTkFrame(left_panel)
        trading_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(trading_frame, text="Trading Ayarları", font=("Arial", 16, "bold")).pack(pady=5)
        
        ctk.CTkLabel(trading_frame, text="Coin Seçimi:").pack(anchor="w", padx=10)
        self.coin_combo = ctk.CTkComboBox(trading_frame, variable=self.selected_coin, 
                                         values=["BTCTRY", "ETHTRY", "ADATRY"], width=300)
        self.coin_combo.pack(padx=10, pady=2)
        
        ctk.CTkLabel(trading_frame, text="Hedef Kar (%):").pack(anchor="w", padx=10)
        self.target_entry = ctk.CTkEntry(trading_frame, textvariable=self.target_percentage, width=300)
        self.target_entry.pack(padx=10, pady=2)
        
        ctk.CTkLabel(trading_frame, text="İşlem Miktarı (TRY):").pack(anchor="w", padx=10)
        self.amount_entry = ctk.CTkEntry(trading_frame, textvariable=self.trade_amount, width=300)
        self.amount_entry.pack(padx=10, pady=2)
        
        # Butonlar
        button_frame = ctk.CTkFrame(left_panel)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.connect_btn = ctk.CTkButton(button_frame, text="API'ye Bağlan", command=self.connect_to_api)
        self.connect_btn.pack(pady=5, padx=10, fill="x")
        
        self.start_btn = ctk.CTkButton(button_frame, text="Bot'u Başlat", command=self.start_bot, state="disabled")
        self.start_btn.pack(pady=5, padx=10, fill="x")
        
        self.stop_btn = ctk.CTkButton(button_frame, text="Bot'u Durdur", command=self.stop_bot, state="disabled")
        self.stop_btn.pack(pady=5, padx=10, fill="x")
        
        # Sağ panel - Durum ve Log
        right_panel = ctk.CTkFrame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Durum paneli
        self.create_status_panel_content(right_panel)
        
        # Log paneli
        self.create_log_panel_content(right_panel)
    
    def create_api_profiles_tab(self):
        """
        API Profilleri sekmesini oluşturur
        """
        main_frame = ctk.CTkFrame(self.tab_api_profiles)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Başlık
        title_label = ctk.CTkLabel(main_frame, text="API Profil Yönetimi", font=("Arial", 20, "bold"))
        title_label.pack(pady=(10, 20))
        
        # Ana container
        container = ctk.CTkFrame(main_frame)
        container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Sol panel - Profil listesi
        left_panel = ctk.CTkFrame(container)
        left_panel.pack(side="left", fill="y", padx=(10, 5), pady=10)
        
        ctk.CTkLabel(left_panel, text="Kayıtlı Profiller", font=("Arial", 14, "bold")).pack(pady=(10, 5))
        
        # Profil listesi
        self.profile_listbox = ctk.CTkScrollableFrame(left_panel, width=200, height=300)
        self.profile_listbox.pack(padx=10, pady=5, fill="both", expand=True)
        
        # Profil butonları
        profile_buttons_frame = ctk.CTkFrame(left_panel)
        profile_buttons_frame.pack(fill="x", padx=10, pady=5)
        
        self.new_profile_btn = ctk.CTkButton(profile_buttons_frame, text="Yeni Profil", command=self.create_new_profile)
        self.new_profile_btn.pack(pady=2, fill="x")
        
        self.delete_profile_btn = ctk.CTkButton(profile_buttons_frame, text="Profil Sil", command=self.delete_profile, fg_color="red")
        self.delete_profile_btn.pack(pady=2, fill="x")
        
        # Sağ panel - Profil detayları
        right_panel = ctk.CTkFrame(container)
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)
        
        ctk.CTkLabel(right_panel, text="Profil Detayları", font=("Arial", 14, "bold")).pack(pady=(10, 20))
        
        # Profil bilgileri formu
        form_frame = ctk.CTkFrame(right_panel)
        form_frame.pack(fill="x", padx=20, pady=10)
        
        # Profil adı
        ctk.CTkLabel(form_frame, text="Profil Adı:").pack(anchor="w", padx=10, pady=(10, 2))
        self.profile_name_var = ctk.StringVar()
        self.profile_name_entry = ctk.CTkEntry(form_frame, textvariable=self.profile_name_var, width=300)
        self.profile_name_entry.pack(padx=10, pady=(0, 10))
        
        # API Key
        ctk.CTkLabel(form_frame, text="API Key:").pack(anchor="w", padx=10, pady=(5, 2))
        self.profile_api_key_var = ctk.StringVar()
        self.profile_api_key_entry = ctk.CTkEntry(form_frame, textvariable=self.profile_api_key_var, width=300, show="*")
        self.profile_api_key_entry.pack(padx=10, pady=(0, 10))
        
        # API Secret
        ctk.CTkLabel(form_frame, text="API Secret:").pack(anchor="w", padx=10, pady=(5, 2))
        self.profile_api_secret_var = ctk.StringVar()
        self.profile_api_secret_entry = ctk.CTkEntry(form_frame, textvariable=self.profile_api_secret_var, width=300, show="*")
        self.profile_api_secret_entry.pack(padx=10, pady=(0, 10))
        
        # Açıklama
        ctk.CTkLabel(form_frame, text="Açıklama:").pack(anchor="w", padx=10, pady=(5, 2))
        self.profile_description_var = ctk.StringVar()
        self.profile_description_entry = ctk.CTkEntry(form_frame, textvariable=self.profile_description_var, width=300)
        self.profile_description_entry.pack(padx=10, pady=(0, 15))
        
        # Form butonları
        form_buttons_frame = ctk.CTkFrame(form_frame)
        form_buttons_frame.pack(fill="x", padx=10, pady=10)
        
        self.save_profile_btn = ctk.CTkButton(form_buttons_frame, text="Profil Kaydet", command=self.save_profile)
        self.save_profile_btn.pack(side="left", padx=(0, 5))
        
        self.test_profile_btn = ctk.CTkButton(form_buttons_frame, text="API Test Et", command=self.test_profile_api)
        self.test_profile_btn.pack(side="left", padx=5)
        
        self.use_profile_btn = ctk.CTkButton(form_buttons_frame, text="Bu Profili Kullan", command=self.use_selected_profile, fg_color="green")
        self.use_profile_btn.pack(side="right")
        
        # Durum bilgisi
        self.profile_status_label = ctk.CTkLabel(right_panel, text="Profil seçin veya yeni profil oluşturun", text_color="gray")
        self.profile_status_label.pack(pady=10)
        
        # Profilleri yükle
        self.load_profile_list()
        
        # Seçili profil
        self.selected_profile_name = None
    
    def create_history_tab(self):
        """
        İşlem Geçmişi sekmesini oluşturur
        """
        frame = ctk.CTkFrame(self.tab_history)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame, text="İşlem Geçmişi", font=("Arial", 20, "bold")).pack(pady=20)
        ctk.CTkLabel(frame, text="Bu özellik yakında eklenecek...").pack(pady=10)
    
    def create_logs_tab(self):
        """
        Log Kayıtları sekmesini oluşturur
        """
        frame = ctk.CTkFrame(self.tab_logs)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame, text="Log Kayıtları", font=("Arial", 20, "bold")).pack(pady=20)
        
        # Log text widget
        self.log_text = ctk.CTkTextbox(frame, height=400)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)
    
    def create_status_panel_content(self, parent):
        """
        Durum paneli içeriğini oluşturur
        """
        status_frame = ctk.CTkFrame(parent)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(status_frame, text="Bot Durumu", font=("Arial", 16, "bold")).pack(pady=5)
        
        self.status_label = ctk.CTkLabel(status_frame, text="Bağlantı Bekleniyor", 
                                        font=("Arial", 12))
        self.status_label.pack(pady=5)
        
        # Bakiye bilgileri
        balance_frame = ctk.CTkFrame(status_frame)
        balance_frame.pack(fill="x", padx=10, pady=5)
        
        self.balance_label = ctk.CTkLabel(balance_frame, text="Bakiye: -- TRY")
        self.balance_label.pack(pady=2)
        
        self.price_label = ctk.CTkLabel(balance_frame, text="Güncel Fiyat: --")
        self.price_label.pack(pady=2)
        
        self.profit_label = ctk.CTkLabel(balance_frame, text="Kar/Zarar: --%")
        self.profit_label.pack(pady=2)
    
    def create_log_panel_content(self, parent):
        """
        Log paneli içeriğini oluşturur
        """
        log_frame = ctk.CTkFrame(parent)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ctk.CTkLabel(log_frame, text="İşlem Logları", font=("Arial", 16, "bold")).pack(pady=5)
        
        # Log text widget - sadece trading sekmesi için küçük log
        log_text = ctk.CTkTextbox(log_frame, height=150)
        log_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Ana log text widget'ını referans olarak sakla
        if not hasattr(self, 'log_text'):
            self.log_text = log_text
    
    # API Profil Yönetimi Metodları
    def create_new_profile(self):
        """
        Yeni profil oluşturma formunu temizler
        """
        self.profile_name_var.set("")
        self.profile_api_key_var.set("")
        self.profile_api_secret_var.set("")
        self.profile_description_var.set("")
        self.selected_profile_name = None
        self.profile_status_label.configure(text="Yeni profil oluşturuluyor...", text_color="blue")
    
    def save_profile(self):
        """
        Profil bilgilerini kaydeder
        """
        name = self.profile_name_var.get().strip()
        api_key = self.profile_api_key_var.get().strip()
        api_secret = self.profile_api_secret_var.get().strip()
        description = self.profile_description_var.get().strip()
        
        if not name:
            messagebox.showerror("Hata", "Profil adı boş olamaz!")
            return
        
        if not api_key or not api_secret:
            messagebox.showerror("Hata", "API Key ve Secret boş olamaz!")
            return
        
        # Profil bilgilerini kaydet
        self.api_profiles[name] = {
            "api_key": api_key,
            "api_secret": api_secret,
            "description": description,
            "created_at": datetime.now().isoformat()
        }
        
        # Dosyaya kaydet
        self.save_api_profiles_to_file()
        
        # Listeyi güncelle
        self.load_profile_list()
        
        # Durum güncelle
        self.profile_status_label.configure(text=f"Profil '{name}' başarıyla kaydedildi!", text_color="green")
        
        messagebox.showinfo("Başarılı", f"Profil '{name}' başarıyla kaydedildi!")
    
    def delete_profile(self):
        """
        Seçili profili siler
        """
        if not self.selected_profile_name:
            messagebox.showwarning("Uyarı", "Silinecek profil seçin!")
            return
        
        # Onay al
        result = messagebox.askyesno("Profil Sil", f"'{self.selected_profile_name}' profilini silmek istediğinizden emin misiniz?")
        if result:
            # Profili sil
            if self.selected_profile_name in self.api_profiles:
                del self.api_profiles[self.selected_profile_name]
                
                # Dosyaya kaydet
                self.save_api_profiles_to_file()
                
                # Listeyi güncelle
                self.load_profile_list()
                
                # Formu temizle
                self.create_new_profile()
                
                messagebox.showinfo("Başarılı", f"Profil '{self.selected_profile_name}' silindi!")
    
    def load_profile_list(self):
        """
        Profil listesini yükler
        """
        # Mevcut butonları temizle
        for widget in self.profile_listbox.winfo_children():
            widget.destroy()
        
        # Profilleri listele
        for profile_name in self.api_profiles.keys():
            profile_btn = ctk.CTkButton(
                self.profile_listbox, 
                text=profile_name,
                command=lambda name=profile_name: self.select_profile(name),
                height=30
            )
            profile_btn.pack(fill="x", padx=5, pady=2)
    
    def select_profile(self, profile_name):
        """
        Profil seçer ve bilgilerini forma yükler
        """
        self.selected_profile_name = profile_name
        profile_data = self.api_profiles[profile_name]
        
        # Form alanlarını doldur
        self.profile_name_var.set(profile_name)
        self.profile_api_key_var.set(profile_data["api_key"])
        self.profile_api_secret_var.set(profile_data["api_secret"])
        self.profile_description_var.set(profile_data.get("description", ""))
        
        # Durum güncelle
        self.profile_status_label.configure(text=f"Profil '{profile_name}' seçildi", text_color="blue")
    
    def test_profile_api(self):
        """
        Seçili profilin API bilgilerini test eder
        """
        api_key = self.profile_api_key_var.get().strip()
        api_secret = self.profile_api_secret_var.get().strip()
        
        if not api_key or not api_secret:
            messagebox.showerror("Hata", "API Key ve Secret boş olamaz!")
            return
        
        try:
            # Test için geçici bot oluştur
            from trading_bot import BTCTurkTradingBot
            test_bot = BTCTurkTradingBot(api_key, api_secret)
            
            # Bakiye kontrolü ile test et
            balance = test_bot.get_balance()
            if balance is not None:
                self.profile_status_label.configure(text="API bağlantısı başarılı!", text_color="green")
                messagebox.showinfo("Başarılı", "API bağlantısı başarılı! Bakiye bilgileri alındı.")
            else:
                self.profile_status_label.configure(text="API bağlantısı başarısız!", text_color="red")
                messagebox.showerror("Hata", "API bağlantısı başarısız! Lütfen bilgileri kontrol edin.")
                
        except Exception as e:
            self.profile_status_label.configure(text="API test hatası!", text_color="red")
            messagebox.showerror("Hata", f"API test hatası: {str(e)}")
    
    def use_selected_profile(self):
        """
        Seçili profili ana trading sekmesinde kullanır
        """
        if not self.selected_profile_name:
            messagebox.showwarning("Uyarı", "Kullanılacak profil seçin!")
            return
        
        profile_data = self.api_profiles[self.selected_profile_name]
        
        # Ana trading sekmesindeki API bilgilerini güncelle
        self.api_key.set(profile_data["api_key"])
        self.api_secret.set(profile_data["api_secret"])
        
        # Mevcut profil olarak ayarla
        self.current_profile.set(self.selected_profile_name)
        
        # Trading sekmesine geç
        self.tabview.set("Trading")
        
        messagebox.showinfo("Başarılı", f"Profil '{self.selected_profile_name}' aktif edildi!")
    
    def save_api_profiles_to_file(self):
        """
        API profillerini dosyaya kaydeder
        """
        try:
            profiles_file = "api_profiles.json"
            with open(profiles_file, 'w', encoding='utf-8') as f:
                json.dump(self.api_profiles, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"API profilleri kaydedilemedi: {e}")
    
    def load_api_profiles_from_file(self):
        """
        API profillerini dosyadan yükler
        """
        try:
            profiles_file = "api_profiles.json"
            if os.path.exists(profiles_file):
                with open(profiles_file, 'r', encoding='utf-8') as f:
                    self.api_profiles = json.load(f)
        except Exception as e:
            logger.error(f"API profilleri yüklenemedi: {e}")
            self.api_profiles = {}
    
if __name__ == "__main__":
    # Test için basit çalıştırma
    from settings_manager import SettingsManager
    
    root = ctk.CTk()
    root.title("BTCTurk Trading Bot")
    root.geometry("1200x800")
    
    # Settings manager'ı başlat
    settings_manager = SettingsManager()
    
    app = TradingBotGUI(root, None, settings_manager, None, None)
    root.mainloop()