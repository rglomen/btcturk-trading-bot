from trading_bot import BTCTurkTradingBot
import customtkinter as ctk
import json
import os
import random
from tkinter import messagebox
from datetime import datetime

class CoinAddDialog:
    def __init__(self, parent, available_coins):
        self.result = None
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Coin Ekle")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (300 // 2)
        self.dialog.geometry(f"400x300+{x}+{y}")
        
        self.create_widgets(available_coins)
        
    def create_widgets(self, available_coins):
        # Main frame
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, text="Yeni Coin Ekle", font=("Arial", 18, "bold"))
        title_label.pack(pady=(10, 20))
        
        # Coin selection
        ctk.CTkLabel(main_frame, text="Coin Seçin:").pack(anchor="w", padx=10, pady=(0, 5))
        self.coin_var = ctk.StringVar(value=available_coins[0] if available_coins else "BTCTRY")
        self.coin_combo = ctk.CTkComboBox(main_frame, values=available_coins, variable=self.coin_var, width=300)
        self.coin_combo.pack(padx=10, pady=(0, 15))
        
        # Target percentage
        ctk.CTkLabel(main_frame, text="Hedef Kar Yüzdesi (%):").pack(anchor="w", padx=10, pady=(0, 5))
        self.target_var = ctk.StringVar(value="2.0")
        self.target_entry = ctk.CTkEntry(main_frame, textvariable=self.target_var, width=300)
        self.target_entry.pack(padx=10, pady=(0, 15))
        
        # Trade amount
        ctk.CTkLabel(main_frame, text="İşlem Miktarı (TRY):").pack(anchor="w", padx=10, pady=(0, 5))
        self.amount_var = ctk.StringVar(value="100")
        self.amount_entry = ctk.CTkEntry(main_frame, textvariable=self.amount_var, width=300)
        self.amount_entry.pack(padx=10, pady=(0, 20))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        cancel_btn = ctk.CTkButton(button_frame, text="İptal", command=self.cancel, fg_color="gray")
        cancel_btn.pack(side="left", padx=(0, 10))
        
        ok_btn = ctk.CTkButton(button_frame, text="Ekle", command=self.ok)
        ok_btn.pack(side="right")
        
    def ok(self):
        try:
            target = float(self.target_var.get())
            amount = float(self.amount_var.get())
            
            if target <= 0 or amount <= 0:
                messagebox.showerror("Hata", "Hedef yüzde ve miktar pozitif olmalıdır!")
                return
                
            self.result = {
                'coin': self.coin_var.get(),
                'target_percentage': target,
                'trade_amount': amount
            }
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin!")
            
    def cancel(self):
        self.result = None
        self.dialog.destroy()
        
    def get_result(self):
        self.dialog.wait_window()
        return self.result



class TradingBotGUI:
    def __init__(self, root, api_key, settings_manager, api_secret, current_profile, app_instance=None):
        self.root = root
        self.api_key = api_key
        self.settings_manager = settings_manager
        self.api_secret = api_secret
        self.current_profile = current_profile
        self.app_instance = app_instance
        self.trade_history = []
        self.price_data = []
        self.time_data = []
        self.strategy = None
        
        # GUI değişkenlerini başlat
        self.setup_variables()
        
        # GUI'yi oluştur
        self.setup_gui()
        
    def setup_variables(self):
        """GUI değişkenlerini başlatır"""
        import tkinter as tk
        
        # API değişkenleri
        self.api_key = tk.StringVar(value="")
        self.api_secret = tk.StringVar(value="")
        
        # Çoklu coin trading değişkenleri
        self.active_coins = {}  # {coin_symbol: {bot_instance, settings, status}}
        self.coin_widgets = {}  # UI widget'ları için
        self.selected_coin = tk.StringVar(value="BTCTRY")
        self.target_percentage = tk.StringVar(value="1.0")
        self.trade_amount = tk.StringVar(value="100")
        
        # Profil değişkenleri
        self.current_profile = tk.StringVar(value="")
        self.profile_name_var = tk.StringVar(value="")
        self.profile_api_key_var = tk.StringVar(value="")
        self.profile_api_secret_var = tk.StringVar(value="")
        
        # API profilleri
        self.api_profiles = {}
        self.selected_profile_name = ""
        
        # Log durumları
        self.system_logs_visible = True
        self.trading_logs_visible = True
        self.api_logs_visible = True
        self.error_logs_visible = True
        
    def setup_gui(self):
        """Ana GUI'yi oluşturur"""
        # Ana tab view oluştur
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Sekmeleri oluştur
        self.tab_trading = self.tabview.add("Trading")
        self.tab_history = self.tabview.add("İşlem Geçmişi")
        self.tab_logs = self.tabview.add("Sistem Logu")
        self.tab_profiles = self.tabview.add("API Profilleri")
        
        # Sekme içeriklerini oluştur
        self.create_trading_tab()
        self.create_history_tab()
        self.create_logs_tab()
        self.create_profiles_tab()
    
    def create_history_tab(self):
        """
        İşlem Geçmişi sekmesini oluşturur
        """
        # Ana frame
        main_frame = ctk.CTkFrame(self.tab_history)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Üst panel - Filtreler ve Kontroller
        top_panel = ctk.CTkFrame(main_frame)
        top_panel.pack(fill="x", padx=5, pady=(0, 5))
        
        # Filtre bölümü
        filter_frame = ctk.CTkFrame(top_panel)
        filter_frame.pack(side="left", fill="y", padx=(10, 5), pady=10)
        
        ctk.CTkLabel(filter_frame, text="Filtreler", font=("Arial", 14, "bold")).pack(pady=5)
        
        # Tarih filtresi
        ctk.CTkLabel(filter_frame, text="Tarih:").pack(anchor="w", padx=10)
        self.date_filter = ctk.CTkComboBox(filter_frame, values=["Tümü", "Bugün", "Bu Hafta", "Bu Ay"], width=150)
        self.date_filter.pack(padx=10, pady=2)
        self.date_filter.set("Tümü")
        
        # Tür filtresi
        ctk.CTkLabel(filter_frame, text="İşlem Türü:").pack(anchor="w", padx=10)
        self.type_filter = ctk.CTkComboBox(filter_frame, values=["Tümü", "Alış", "Satış"], width=150)
        self.type_filter.pack(padx=10, pady=2)
        self.type_filter.set("Tümü")
        
        # Coin filtresi
        ctk.CTkLabel(filter_frame, text="Coin:").pack(anchor="w", padx=10)
        self.coin_filter = ctk.CTkComboBox(filter_frame, values=["Tümü"], width=150)
        self.coin_filter.pack(padx=10, pady=2)
        self.coin_filter.set("Tümü")
        
        # Filtre uygula butonu
        ctk.CTkButton(filter_frame, text="Filtre Uygula", command=self.apply_filters).pack(pady=10, padx=10, fill="x")
        
        # Kontrol bölümü
        control_frame = ctk.CTkFrame(top_panel)
        control_frame.pack(side="right", fill="y", padx=(5, 10), pady=10)
        
        ctk.CTkLabel(control_frame, text="İşlemler", font=("Arial", 14, "bold")).pack(pady=5)
        
        ctk.CTkButton(control_frame, text="Yenile", command=self.refresh_trade_history).pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(control_frame, text="CSV'ye Aktar", command=self.export_to_csv).pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(control_frame, text="Geçmişi Temizle", command=self.clear_trade_history, fg_color="red").pack(pady=5, padx=10, fill="x")
        
        # İstatistikler paneli
        stats_frame = ctk.CTkFrame(main_frame)
        stats_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(stats_frame, text="İstatistikler", font=("Arial", 14, "bold")).pack(pady=5)
        
        stats_content = ctk.CTkFrame(stats_frame)
        stats_content.pack(fill="x", padx=10, pady=(0, 10))
        
        # İstatistik labelları
        self.total_trades_label = ctk.CTkLabel(stats_content, text="Toplam İşlem: 0")
        self.total_trades_label.pack(side="left", padx=20, pady=5)
        
        self.total_profit_label = ctk.CTkLabel(stats_content, text="Toplam Kar/Zarar: 0.00 TRY")
        self.total_profit_label.pack(side="left", padx=20, pady=5)
        
        self.success_rate_label = ctk.CTkLabel(stats_content, text="Başarı Oranı: 0%")
        self.success_rate_label.pack(side="left", padx=20, pady=5)
        
        # İşlem geçmişi tablosu
        table_frame = ctk.CTkFrame(main_frame)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(table_frame, text="İşlem Geçmişi", font=("Arial", 14, "bold")).pack(pady=5)
        
        # Tablo başlıkları
        headers_frame = ctk.CTkFrame(table_frame)
        headers_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        headers = ["Tarih", "Tür", "Coin", "Miktar", "Fiyat", "Toplam", "Kar/Zarar", "Durum"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(headers_frame, text=header, font=("Arial", 12, "bold"))
            label.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
        
        # Scrollable frame for history
        self.history_scrollable = ctk.CTkScrollableFrame(table_frame, height=300)
        self.history_scrollable.pack(fill="both", expand=True, padx=10, pady=10)
        
        # İşlem geçmişini yükle
        self.trade_history = []
        self.refresh_trade_history()
    
    def create_logs_tab(self):
        """
        Sistem Logu sekmesini oluşturur (terminal benzeri)
        """
        # Ana frame
        main_frame = ctk.CTkFrame(self.tab_logs)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Üst panel - Kontroller
        top_panel = ctk.CTkFrame(main_frame)
        top_panel.pack(fill="x", padx=5, pady=(0, 5))
        
        ctk.CTkLabel(top_panel, text="Sistem Terminal Logu", font=("Arial", 16, "bold")).pack(side="left", padx=10, pady=10)
        
        # Kontrol butonları
        button_frame = ctk.CTkFrame(top_panel)
        button_frame.pack(side="right", padx=10, pady=10)
        
        ctk.CTkButton(button_frame, text="Temizle", command=self.clear_system_logs, width=80).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Kaydet", command=self.save_system_logs, width=80).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Yenile", command=self.refresh_system_logs, width=80).pack(side="left", padx=5)
        
        # Log seviye filtresi
        ctk.CTkLabel(button_frame, text="Seviye:").pack(side="left", padx=(10, 5))
        self.log_level_filter = ctk.CTkComboBox(button_frame, values=["Tümü", "INFO", "WARNING", "ERROR"], width=100)
        self.log_level_filter.pack(side="left", padx=5)
        self.log_level_filter.set("Tümü")
        
        # Terminal benzeri log alanı
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Scrollable text area
        self.system_log_text = ctk.CTkTextbox(log_frame, font=("Consolas", 11), text_color="#00FF00", fg_color="#000000")
        self.system_log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # İlk log mesajı
        self.add_system_log("Sistem logu başlatıldı...", "INFO")
        self.add_system_log(f"BTCTurk Trading Bot v1.1.0 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.add_system_log("="*60, "INFO")
    
    def create_trading_tab(self):
        """
        Çoklu Coin Trading sekmesini oluşturur
        """
        # Ana frame
        main_frame = ctk.CTkFrame(self.tab_trading)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Üst panel - API Ayarları ve Genel Kontroller
        top_panel = ctk.CTkFrame(main_frame)
        top_panel.pack(fill="x", padx=5, pady=(0, 5))
        
        # API Ayarları
        api_frame = ctk.CTkFrame(top_panel)
        api_frame.pack(side="left", fill="y", padx=(10, 5), pady=10)
        
        ctk.CTkLabel(api_frame, text="API Ayarları", font=("Arial", 14, "bold")).pack(pady=5)
        
        ctk.CTkLabel(api_frame, text="API Key:").pack(anchor="w", padx=10)
        self.api_key_entry = ctk.CTkEntry(api_frame, textvariable=self.api_key, width=250, show="*")
        self.api_key_entry.pack(padx=10, pady=2)
        
        ctk.CTkLabel(api_frame, text="API Secret:").pack(anchor="w", padx=10)
        self.api_secret_entry = ctk.CTkEntry(api_frame, textvariable=self.api_secret, width=250, show="*")
        self.api_secret_entry.pack(padx=10, pady=2)
        
        self.connect_btn = ctk.CTkButton(api_frame, text="API'ye Bağlan", command=self.connect_to_api)
        self.connect_btn.pack(pady=10, padx=10, fill="x")
        
        # Genel Kontroller
        control_frame = ctk.CTkFrame(top_panel)
        control_frame.pack(side="right", fill="y", padx=(5, 10), pady=10)
        
        ctk.CTkLabel(control_frame, text="Genel Kontroller", font=("Arial", 14, "bold")).pack(pady=5)
        
        self.start_all_btn = ctk.CTkButton(control_frame, text="Tüm Botları Başlat", 
                                          command=self.start_all_bots, state="disabled", fg_color="green")
        self.start_all_btn.pack(pady=5, padx=10, fill="x")
        
        self.stop_all_btn = ctk.CTkButton(control_frame, text="Tüm Botları Durdur", 
                                         command=self.stop_all_bots, state="disabled", fg_color="red")
        self.stop_all_btn.pack(pady=5, padx=10, fill="x")
        
        self.add_coin_btn = ctk.CTkButton(control_frame, text="Coin Ekle", command=self.add_coin_to_list)
        self.add_coin_btn.pack(pady=5, padx=10, fill="x")
        
        self.settings_btn = ctk.CTkButton(control_frame, text="Ayarlar", command=self.show_settings, fg_color="orange")
        self.settings_btn.pack(pady=5, padx=10, fill="x")
        
        # Orta panel - Coin Listesi ve Ayarları
        middle_panel = ctk.CTkFrame(main_frame)
        middle_panel.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Coin listesi başlığı
        header_frame = ctk.CTkFrame(middle_panel)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(header_frame, text="Aktif Coin Listesi", font=("Arial", 16, "bold")).pack(side="left", padx=10, pady=5)
        
        # Coin listesi tablosu
        self.create_coin_table(middle_panel)
        
        # Alt panel - Durum ve Log
        bottom_panel = ctk.CTkFrame(main_frame)
        bottom_panel.pack(fill="both", expand=True, padx=5, pady=(5, 0))
        
        # Durum paneli
        self.create_status_panel_content(bottom_panel)
        
        # Trading sekmesindeki log paneli kaldırıldı - artık ayrı Sistem Logu sekmesi var
    
    def create_coin_table(self, parent):
        """
        Coin listesi tablosunu oluşturur
        """
        # Tablo container
        table_frame = ctk.CTkScrollableFrame(parent, height=300)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tablo başlıkları
        headers_frame = ctk.CTkFrame(table_frame)
        headers_frame.pack(fill="x", pady=(0, 5))
        
        headers = ["Coin", "Fiyat", "Hedef Kar (%)", "Miktar (TRY)", "Durum", "Kar/Zarar", "İşlemler"]
        header_widths = [80, 120, 100, 100, 120, 100, 200]
        
        for i, (header, width) in enumerate(zip(headers, header_widths)):
            label = ctk.CTkLabel(headers_frame, text=header, font=("Arial", 12, "bold"), width=width)
            label.grid(row=0, column=i, padx=2, pady=5, sticky="ew")
        
        # Coin satırları için frame
        self.coins_container = ctk.CTkFrame(table_frame)
        self.coins_container.pack(fill="both", expand=True)
        
        # Başlangıçta boş tablo mesajı
        self.empty_message = ctk.CTkLabel(self.coins_container, 
                                         text="Henüz coin eklenmemiş. 'Coin Ekle' butonunu kullanarak coin ekleyin.",
                                         font=("Arial", 12), text_color="gray")
        self.empty_message.pack(pady=50)
    
    def add_coin_to_list(self):
        """
        Yeni coin ekleme dialog'unu açar
        """
        try:
            self.add_log("Coin ekleme dialog'u açılıyor...", "system", "INFO")
            
            # Mevcut coin listesini al
            available_coins = ["BTCTRY", "ETHTRY", "ADATRY", "XRPTRY", "LTCTRY", "DOGETRY"]
            
            # Eğer API'den coin listesi alınmışsa onu kullan
            if hasattr(self, 'bot') and self.bot:
                try:
                    pairs = self.bot.get_available_pairs()
                    if pairs:
                        available_coins = [pair for pair in pairs if pair.endswith('TRY')]
                        self.add_log(f"API'den {len(available_coins)} coin alındı", "system", "INFO")
                except Exception as e:
                    self.add_log(f"API'den coin listesi alınamadı: {e}", "system", "WARNING")
            
            dialog = CoinAddDialog(self.root, available_coins)
            coin_data = dialog.get_result()
            
            if coin_data:
                self.add_log(f"Coin ekleniyor: {coin_data}", "system", "INFO")
                self.add_coin_row(coin_data)
            else:
                self.add_log("Coin ekleme iptal edildi", "system", "INFO")
                
        except Exception as e:
            self.add_log(f"Coin ekleme hatası: {e}", "system", "ERROR")
            from tkinter import messagebox
            messagebox.showerror("Hata", f"Coin ekleme hatası: {str(e)}")
    
    def add_coin_row(self, coin_data):
        """
        Tabloya yeni coin satırı ekler
        """
        coin_symbol = coin_data['coin']
        
        # Eğer coin zaten varsa uyarı ver
        if coin_symbol in self.active_coins:
            from tkinter import messagebox
            messagebox.showwarning("Uyarı", f"{coin_symbol} zaten listede mevcut!")
            return
        
        # Boş mesajı gizle
        if hasattr(self, 'empty_message'):
            self.empty_message.pack_forget()
        
        # Coin verilerini kaydet
        self.active_coins[coin_symbol] = {
            'settings': coin_data,
            'bot_instance': None,
            'status': 'Durduruldu',
            'profit_loss': 0.0,
            'current_price': 0.0
        }
        
        # Satır frame'i oluştur
        row_frame = ctk.CTkFrame(self.coins_container)
        row_frame.pack(fill="x", pady=2, padx=5)
        
        # Widget'ları oluştur ve kaydet
        widgets = {}
        
        # Coin adı
        widgets['coin_label'] = ctk.CTkLabel(row_frame, text=coin_symbol, width=80)
        widgets['coin_label'].grid(row=0, column=0, padx=2, pady=5)
        
        # Fiyat
        widgets['price_label'] = ctk.CTkLabel(row_frame, text="0.00 TRY", width=120)
        widgets['price_label'].grid(row=0, column=1, padx=2, pady=5)
        
        # Hedef kar
        widgets['target_label'] = ctk.CTkLabel(row_frame, text=f"%{coin_data['target_percentage']}", width=100)
        widgets['target_label'].grid(row=0, column=2, padx=2, pady=5)
        
        # Miktar
        widgets['amount_label'] = ctk.CTkLabel(row_frame, text=f"{coin_data['trade_amount']} TRY", width=100)
        widgets['amount_label'].grid(row=0, column=3, padx=2, pady=5)
        
        # Durum
        widgets['status_label'] = ctk.CTkLabel(row_frame, text="Durduruldu", width=120, text_color="red")
        widgets['status_label'].grid(row=0, column=4, padx=2, pady=5)
        
        # Kar/Zarar
        widgets['profit_label'] = ctk.CTkLabel(row_frame, text="0.00 TRY", width=100)
        widgets['profit_label'].grid(row=0, column=5, padx=2, pady=5)
        
        # İşlem butonları
        buttons_frame = ctk.CTkFrame(row_frame)
        buttons_frame.grid(row=0, column=6, padx=2, pady=5)
        
        widgets['start_btn'] = ctk.CTkButton(buttons_frame, text="Başlat", width=60, height=25,
                                           command=lambda: self.start_coin_bot(coin_symbol))
        widgets['start_btn'].pack(side="left", padx=2)
        
        widgets['stop_btn'] = ctk.CTkButton(buttons_frame, text="Durdur", width=60, height=25,
                                          command=lambda: self.stop_coin_bot(coin_symbol), state="disabled")
        widgets['stop_btn'].pack(side="left", padx=2)
        
        widgets['remove_btn'] = ctk.CTkButton(buttons_frame, text="Sil", width=40, height=25,
                                            command=lambda: self.remove_coin(coin_symbol), fg_color="red")
        widgets['remove_btn'].pack(side="left", padx=2)
        
        # Widget'ları kaydet
        self.coin_widgets[coin_symbol] = {
            'row_frame': row_frame,
            'widgets': widgets
        }
    
    def start_coin_bot(self, coin_symbol):
        """
        Belirli bir coin için bot başlatır
        """
        if coin_symbol not in self.active_coins:
            return
        
        # API bağlantısı kontrolü
        if not hasattr(self, 'bot') or not self.bot:
            from tkinter import messagebox
            messagebox.showerror("Hata", "Önce API'ye bağlanmalısınız!")
            return
        
        coin_data = self.active_coins[coin_symbol]
        settings = coin_data['settings']
        
        try:
            # Yeni bot instance oluştur
            from trading_bot import BTCTurkTradingBot
            bot_instance = BTCTurkTradingBot(self.api_key.get(), self.api_secret.get())
            
            # Callback fonksiyonlarını ayarla
            bot_instance.set_callbacks(
                price_callback=lambda price, profit_pct=0: self.update_coin_price(coin_symbol, price, profit_pct),
                status_callback=lambda status: self.update_coin_status(coin_symbol, status),
                trade_callback=lambda trade_info: self.on_coin_trade_completed(coin_symbol, trade_info),
                balance_callback=self.update_balance_from_bot
            )
            
            # Bot'u başlat
            bot_instance.start_trading(
                settings['coin'],
                settings['target_percentage'],
                settings['trade_amount']
            )
            
            # Bot instance'ını kaydet
            coin_data['bot_instance'] = bot_instance
            coin_data['status'] = 'Çalışıyor'
            
            # UI güncelle
            widgets = self.coin_widgets[coin_symbol]['widgets']
            widgets['status_label'].configure(text="Çalışıyor", text_color="green")
            widgets['start_btn'].configure(state="disabled")
            widgets['stop_btn'].configure(state="normal")
            
            self.add_log(f"{coin_symbol} botu başlatıldı - Hedef: %{settings['target_percentage']} - Miktar: {settings['trade_amount']} TRY", "trading", "INFO")
            
            # Genel kontrol butonlarını güncelle
            self.update_general_buttons()
            
            # Dashboard'u güncelle
            self.update_dashboard()
            
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Hata", f"{coin_symbol} botu başlatılamadı: {str(e)}")
            self.add_log(f"{coin_symbol} bot başlatma hatası: {str(e)}", "trading", "ERROR")
    
    def stop_coin_bot(self, coin_symbol):
        """
        Belirli bir coin için bot durdurur
        """
        if coin_symbol not in self.active_coins:
            return
        
        coin_data = self.active_coins[coin_symbol]
        
        if coin_data['bot_instance']:
            coin_data['bot_instance'].stop_trading()
            coin_data['bot_instance'] = None
        
        coin_data['status'] = 'Durduruldu'
        
        # UI güncelle
        widgets = self.coin_widgets[coin_symbol]['widgets']
        widgets['status_label'].configure(text="Durduruldu", text_color="red")
        widgets['start_btn'].configure(state="normal")
        widgets['stop_btn'].configure(state="disabled")
        
        self.add_log(f"{coin_symbol} botu durduruldu", "trading", "INFO")
        
        # Genel kontrol butonlarını güncelle
        self.update_general_buttons()
        
        # Dashboard'u güncelle
        self.update_dashboard()
    
    def remove_coin(self, coin_symbol):
        """
        Coin'i listeden kaldırır
        """
        from tkinter import messagebox
        
        # Onay al
        if not messagebox.askyesno("Onay", f"{coin_symbol} coin'ini listeden kaldırmak istediğinizden emin misiniz?"):
            return
        
        # Bot'u durdur
        if coin_symbol in self.active_coins:
            self.stop_coin_bot(coin_symbol)
            
            # UI'dan kaldır
            if coin_symbol in self.coin_widgets:
                self.coin_widgets[coin_symbol]['row_frame'].destroy()
                del self.coin_widgets[coin_symbol]
            
            # Veriyi kaldır
            del self.active_coins[coin_symbol]
            
            self.add_log(f"{coin_symbol} listeden kaldırıldı", "system", "INFO")
            
            # Eğer liste boşsa boş mesajı göster
            if not self.active_coins:
                self.empty_message.pack(pady=50)
            
            # Genel kontrol butonlarını güncelle
            self.update_general_buttons()
    
    def start_all_bots(self):
        """
        Tüm coin botlarını başlatır
        """
        for coin_symbol in self.active_coins:
            if self.active_coins[coin_symbol]['status'] == 'Durduruldu':
                self.start_coin_bot(coin_symbol)
    
    def stop_all_bots(self):
        """
        Tüm coin botlarını durdurur
        """
        for coin_symbol in self.active_coins:
            if self.active_coins[coin_symbol]['status'] == 'Çalışıyor':
                self.stop_coin_bot(coin_symbol)
    
    def update_general_buttons(self):
        """
        Genel kontrol butonlarının durumunu günceller
        """
        has_stopped = any(coin['status'] == 'Durduruldu' for coin in self.active_coins.values())
        has_running = any(coin['status'] == 'Çalışıyor' for coin in self.active_coins.values())
        
        # API bağlantısı varsa ve durdurulmuş botlar varsa başlat butonunu aktif et
        if hasattr(self, 'trading_bot') and self.trading_bot and has_stopped:
            self.start_all_btn.configure(state="normal")
        else:
            self.start_all_btn.configure(state="disabled")
        
        # Çalışan botlar varsa durdur butonunu aktif et
        if has_running:
            self.stop_all_btn.configure(state="normal")
        else:
            self.stop_all_btn.configure(state="disabled")
    
    def update_coin_price(self, coin_symbol, price, profit_pct=0):
        """
        Belirli bir coin için fiyat güncellemesi yapar
        """
        if coin_symbol in self.coin_widgets:
            widgets = self.coin_widgets[coin_symbol]['widgets']
            # Fiyat widget'ını güncelle
            widgets['price_label'].configure(text=f"{price:.4f} TRY")
            
            # Kar/zarar widget'ını güncelle
            if profit_pct != 0:
                color = "green" if profit_pct > 0 else "red" if profit_pct < 0 else "gray"
                widgets['profit_label'].configure(text=f"%{profit_pct:.2f}", text_color=color)
        
        # Aktif coin verilerini güncelle
        if coin_symbol in self.active_coins:
            self.active_coins[coin_symbol]['current_price'] = price
            self.active_coins[coin_symbol]['profit_loss'] = profit_pct
        
        self.add_log(f"{coin_symbol} fiyat güncellendi: {price:.4f} TRY (Kar: %{profit_pct:.2f})", "trading", "DEBUG")
    
    def update_coin_status(self, coin_symbol, status_message):
        """
        Belirli bir coin için durum güncellemesi yapar
        """
        if coin_symbol in self.coin_widgets:
            widgets = self.coin_widgets[coin_symbol]['widgets']
            
            # Durum widget'ını güncelle
            if "çalışıyor" in status_message.lower() or "bekleniyor" in status_message.lower():
                widgets['status_label'].configure(text="Çalışıyor", text_color="green")
            elif "durdur" in status_message.lower() or "hata" in status_message.lower():
                widgets['status_label'].configure(text="Durduruldu", text_color="red")
            elif "satış" in status_message.lower():
                widgets['status_label'].configure(text="Satış Bekleniyor", text_color="orange")
            else:
                widgets['status_label'].configure(text="Çalışıyor", text_color="blue")
        
        # Aktif coin verilerini güncelle
        if coin_symbol in self.active_coins:
            self.active_coins[coin_symbol]['status'] = status_message
            
        # Durum mesajını log'a ekle
        self.add_log(f"{coin_symbol}: {status_message}", "trading", "INFO")
    
    def on_coin_trade_completed(self, coin_symbol, trade_info):
        """
        Belirli bir coin için işlem tamamlandığında çalışır
        """
        if coin_symbol in self.coin_widgets and coin_symbol in self.active_coins:
            widgets = self.coin_widgets[coin_symbol]['widgets']
            
            # Kar/zarar hesapla ve güncelle
            if 'profit' in trade_info:
                profit = trade_info['profit']
                profit_text = f"{profit:.2f} TRY"
                profit_color = "green" if profit > 0 else "red" if profit < 0 else "gray"
                widgets['profit_label'].configure(text=profit_text, text_color=profit_color)
            
            # İşlem logunu ekle
            trade_type = trade_info.get('type', 'Bilinmeyen')
            amount = trade_info.get('amount', 0)
            price = trade_info.get('price', 0)
            
            self.add_log(f"{coin_symbol} işlem tamamlandı - {trade_type}: {amount:.6f} @ {price:.2f} TRY", "trading", "INFO")
            
            # Dashboard'u güncelle
            self.update_dashboard()
    
    def update_dashboard(self):
        """
        Dashboard bilgilerini günceller
        """
        try:
            # Toplam ve aktif bot sayıları
            total_bots = len(self.active_coins)
            active_bots = sum(1 for coin in self.active_coins.values() if coin['status'] == 'Çalışıyor')
            
            self.total_bots_label.configure(text=f"Toplam Bot: {total_bots}")
            self.active_bots_label.configure(text=f"Aktif Bot: {active_bots}")
            
            # Toplam kar/zarar hesapla
            total_profit = 0.0
            for coin_symbol in self.coin_widgets:
                if coin_symbol in self.active_coins:
                    # Widget'tan kar/zarar bilgisini al
                    profit_text = self.coin_widgets[coin_symbol]['widgets']['profit_label'].cget('text')
                    try:
                        # "X.XX TRY" formatından sayıyı çıkar
                        profit_value = float(profit_text.replace(' TRY', '').replace(',', '.'))
                        total_profit += profit_value
                    except:
                        pass
            
            # Toplam kar/zarar rengini belirle
            profit_color = "green" if total_profit > 0 else "red" if total_profit < 0 else "gray"
            self.total_profit_label.configure(text=f"Toplam Kar/Zarar: {total_profit:.2f} TRY", text_color=profit_color)
            
            # Hızlı özet güncelle
            self.update_summary_panel()
            
        except Exception as e:
            self.add_log(f"Dashboard güncelleme hatası: {str(e)}", "system", "ERROR")
    
    def update_summary_panel(self):
        """
        Hızlı özet panelini günceller
        """
        # Mevcut özet widget'larını temizle
        for widget in self.summary_frame.winfo_children():
            widget.destroy()
        
        if not self.active_coins:
            # Boş mesaj göster
            self.summary_empty_label = ctk.CTkLabel(self.summary_frame, 
                                                  text="Henüz aktif bot bulunmuyor", 
                                                  font=("Arial", 12), text_color="gray")
            self.summary_empty_label.pack(pady=20)
        else:
            # Her coin için özet satırı oluştur
            for coin_symbol, coin_data in self.active_coins.items():
                summary_row = ctk.CTkFrame(self.summary_frame)
                summary_row.pack(fill="x", padx=5, pady=2)
                
                # Coin adı ve durumu
                status_color = "green" if coin_data['status'] == 'Çalışıyor' else "red"
                coin_label = ctk.CTkLabel(summary_row, text=f"{coin_symbol}: {coin_data['status']}", 
                                        font=("Arial", 11), text_color=status_color, width=120)
                coin_label.pack(side="left", padx=5, pady=2)
                
                # Kar/zarar bilgisi
                if coin_symbol in self.coin_widgets:
                    profit_text = self.coin_widgets[coin_symbol]['widgets']['profit_label'].cget('text')
                    profit_label = ctk.CTkLabel(summary_row, text=profit_text, font=("Arial", 11), width=80)
                    profit_label.pack(side="right", padx=5, pady=2)
    
    def update_api_status(self, connected=False):
        """
        API bağlantı durumunu günceller
        """
        if connected:
            self.api_status_label.configure(text="API: Bağlandı ✓", text_color="green")
        else:
            self.api_status_label.configure(text="API: Bağlantı Bekleniyor", text_color="orange")
    
    def create_profiles_tab(self):
        """
        API Profilleri sekmesini oluşturur
        """
        # API profillerini önce yükle
        self.load_api_profiles_from_file()
        
        main_frame = ctk.CTkFrame(self.tab_profiles)
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
    

    

    
    def create_status_panel_content(self, parent):
        """
        Çoklu coin durumları için dashboard paneli oluşturur
        """
        # Sol panel - Genel durum
        left_panel = ctk.CTkFrame(parent)
        left_panel.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=5)
        
        ctk.CTkLabel(left_panel, text="Genel Durum", font=("Arial", 16, "bold")).pack(pady=5)
        
        # API bağlantı durumu
        self.api_status_label = ctk.CTkLabel(left_panel, text="API: Bağlantı Bekleniyor", 
                                           font=("Arial", 12), text_color="orange")
        self.api_status_label.pack(pady=2)
        
        # Toplam bot sayısı
        self.total_bots_label = ctk.CTkLabel(left_panel, text="Toplam Bot: 0", font=("Arial", 12))
        self.total_bots_label.pack(pady=2)
        
        # Aktif bot sayısı
        self.active_bots_label = ctk.CTkLabel(left_panel, text="Aktif Bot: 0", 
                                            font=("Arial", 12), text_color="green")
        self.active_bots_label.pack(pady=2)
        
        # Toplam bakiye
        self.total_balance_label = ctk.CTkLabel(left_panel, text="Toplam Bakiye: -- TRY", font=("Arial", 12))
        self.total_balance_label.pack(pady=2)
        
        # Toplam kar/zarar
        self.total_profit_label = ctk.CTkLabel(left_panel, text="Toplam Kar/Zarar: 0.00 TRY", 
                                             font=("Arial", 12), text_color="gray")
        self.total_profit_label.pack(pady=2)
        
        # Sağ panel - Coin özeti
        right_panel = ctk.CTkFrame(parent)
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=5)
        
        ctk.CTkLabel(right_panel, text="Coin Özeti", font=("Arial", 16, "bold")).pack(pady=5)
        
        # Summary frame - coin özetleri için scrollable frame
        self.summary_frame = ctk.CTkScrollableFrame(right_panel, height=200)
        self.summary_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Başlangıçta boş mesaj
        self.summary_empty_label = ctk.CTkLabel(self.summary_frame, 
                                              text="Henüz aktif coin yok", 
                                              font=("Arial", 12), text_color="gray")
        self.summary_empty_label.pack(pady=20)

    
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
    
    def refresh_trade_history(self):
        """
        İşlem geçmişini yeniler
        """
        try:
            # Mevcut kayıtları temizle
            for widget in self.history_scrollable.winfo_children():
                widget.destroy()
            
            # İşlem geçmişi dosyasını oku
            if os.path.exists('trade_history.json'):
                with open('trade_history.json', 'r', encoding='utf-8') as f:
                    self.trade_history = json.load(f)
            else:
                self.trade_history = []
            
            # Filtrelenmiş verileri göster
            self.apply_filters()
            
        except Exception as e:
            logger.error(f"İşlem geçmişi yüklenirken hata: {e}")
            messagebox.showerror("Hata", f"İşlem geçmişi yüklenirken hata: {e}")
    
    def clear_trade_history(self):
        """
        İşlem geçmişini temizler
        """
        result = messagebox.askyesno("Onay", "Tüm işlem geçmişini silmek istediğinizden emin misiniz?")
        if result:
            try:
                self.trade_history = []
                if os.path.exists('trade_history.json'):
                    os.remove('trade_history.json')
                self.refresh_trade_history()
                messagebox.showinfo("Başarılı", "İşlem geçmişi temizlendi.")
            except Exception as e:
                logger.error(f"İşlem geçmişi temizlenirken hata: {e}")
                messagebox.showerror("Hata", f"İşlem geçmişi temizlenirken hata: {e}")
    
    def export_trade_history(self):
        """
        İşlem geçmişini CSV dosyasına aktarır
        """
        try:
            import csv
            from tkinter import filedialog
            
            if not self.trade_history:
                messagebox.showwarning("Uyarı", "Dışa aktarılacak işlem geçmişi bulunamadı.")
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="İşlem Geçmişini Kaydet"
            )
            
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['timestamp', 'type', 'coin', 'amount', 'price', 'total', 'profit_loss', 'status']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for trade in self.trade_history:
                        writer.writerow(trade)
                
                messagebox.showinfo("Başarılı", f"İşlem geçmişi {filename} dosyasına aktarıldı.")
                
        except Exception as e:
            logger.error(f"İşlem geçmişi dışa aktarılırken hata: {e}")
            messagebox.showerror("Hata", f"İşlem geçmişi dışa aktarılırken hata: {e}")
    
    def export_to_csv(self):
        """
        CSV'ye aktarma için alias metodu
        """
        self.export_trade_history()
    
    def apply_filters(self):
        """
        Filtreleri uygular ve tabloyu günceller
        """
        try:
            # Mevcut kayıtları temizle
            for widget in self.history_scrollable.winfo_children():
                widget.destroy()
            
            # Filtreleri al
            date_filter = self.date_filter.get() if hasattr(self, 'date_filter') else "Tümü"
            type_filter = self.type_filter.get() if hasattr(self, 'type_filter') else "Tümü"
            coin_filter = self.coin_filter.get() if hasattr(self, 'coin_filter') else "Tümü"
            
            # Filtrelenmiş verileri hazırla
            filtered_trades = self.trade_history.copy()
            
            # Tarih filtresi
            if date_filter != "Tümü":
                from datetime import datetime, timedelta
                now = datetime.now()
                
                if date_filter == "Bugün":
                    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                elif date_filter == "Son 7 Gün":
                    start_date = now - timedelta(days=7)
                elif date_filter == "Son 30 Gün":
                    start_date = now - timedelta(days=30)
                
                filtered_trades = [
                    trade for trade in filtered_trades
                    if datetime.fromisoformat(trade['timestamp'].replace('Z', '+00:00')) >= start_date
                ]
            
            # Tür filtresi
            if type_filter != "Tümü":
                filtered_trades = [
                    trade for trade in filtered_trades
                    if trade['type'].lower() == type_filter.lower()
                ]
            
            # Coin filtresi
            if coin_filter != "Tümü":
                filtered_trades = [
                    trade for trade in filtered_trades
                    if trade['coin'] == coin_filter
                ]
            
            # Tabloyu doldur
            self.populate_trade_table(filtered_trades)
            
            # İstatistikleri güncelle
            self.update_trade_statistics(filtered_trades)
            
        except Exception as e:
            logger.error(f"Filtreler uygulanırken hata: {e}")
    
    def populate_trade_table(self, trades):
        """
        İşlem tablosunu doldurur
        """
        try:
            for i, trade in enumerate(trades):
                # Satır frame'i
                row_frame = ctk.CTkFrame(self.history_scrollable)
                row_frame.pack(fill="x", padx=2, pady=1)
                
                # Renk kodlaması (kar/zarar durumuna göre)
                bg_color = "#1f4f2f" if float(trade.get('profit_loss', 0)) > 0 else "#4f1f1f" if float(trade.get('profit_loss', 0)) < 0 else "#2f2f2f"
                row_frame.configure(fg_color=bg_color)
                
                # Sütunlar
                timestamp = datetime.fromisoformat(trade['timestamp'].replace('Z', '+00:00')).strftime('%d.%m.%Y %H:%M')
                
                data = [
                    timestamp,
                    trade['type'],
                    trade['coin'],
                    f"{float(trade['amount']):.6f}",
                    f"{float(trade['price']):.2f} TRY",
                    f"{float(trade['total']):.2f} TRY",
                    f"{float(trade.get('profit_loss', 0)):.2f} TRY",
                    trade.get('status', 'Tamamlandı')
                ]
                
                widths = [150, 60, 80, 100, 100, 120, 100, 80]
                
                for j, (value, width) in enumerate(zip(data, widths)):
                    label = ctk.CTkLabel(row_frame, text=str(value), width=width, font=("Arial", 10))
                    label.pack(side="left", padx=2, pady=2)
                    
        except Exception as e:
            logger.error(f"Tablo doldurulurken hata: {e}")
    
    def update_trade_statistics(self, trades):
        """
        İşlem istatistiklerini günceller
        """
        try:
            total_trades = len(trades)
            total_profit = sum(float(trade.get('profit_loss', 0)) for trade in trades)
            profitable_trades = len([trade for trade in trades if float(trade.get('profit_loss', 0)) > 0])
            success_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Etiketleri güncelle
            if hasattr(self, 'total_trades_label'):
                self.total_trades_label.configure(text=f"Toplam İşlem: {total_trades}")
            
            if hasattr(self, 'total_profit_label'):
                color = "#4CAF50" if total_profit > 0 else "#F44336" if total_profit < 0 else "#FFF"
                self.total_profit_label.configure(text=f"Toplam Kar/Zarar: {total_profit:.2f} TRY", text_color=color)
            
            if hasattr(self, 'success_rate_label'):
                self.success_rate_label.configure(text=f"Başarı Oranı: {success_rate:.1f}%")
                
        except Exception as e:
            logger.error(f"İstatistikler güncellenirken hata: {e}")
    
    def add_trade_to_history(self, trade_data):
        """
        Yeni işlemi geçmişe ekler
        """
        try:
            # İşlem verisini hazırla
            trade_record = {
                'timestamp': datetime.now().isoformat(),
                'type': trade_data.get('type', 'Alış'),
                'coin': trade_data.get('coin', 'BTCTRY'),
                'amount': str(trade_data.get('amount', 0)),
                'price': str(trade_data.get('price', 0)),
                'total': str(trade_data.get('total', 0)),
                'profit_loss': str(trade_data.get('profit_loss', 0)),
                'status': trade_data.get('status', 'Tamamlandı')
            }
            
            # Listeye ekle
            self.trade_history.append(trade_record)
            
            # Dosyaya kaydet
            with open('trade_history.json', 'w', encoding='utf-8') as f:
                json.dump(self.trade_history, f, ensure_ascii=False, indent=2)
            
            # Tabloyu güncelle
            self.apply_filters()
            
        except Exception as e:
            logger.error(f"İşlem geçmişine eklenirken hata: {e}")
    
    # Trading Bot Kontrol Metodları
    def connect_to_api(self):
        """API'ye bağlanır"""
        try:
            api_key = self.api_key.get().strip()
            api_secret = self.api_secret.get().strip()
            
            if not api_key or not api_secret:
                messagebox.showerror("Hata", "API Key ve Secret boş olamaz!")
                return
            
            # Bot oluştur ve test et
            from trading_bot import BTCTurkTradingBot
            self.bot = BTCTurkTradingBot(api_key, api_secret)
            
            # Bağlantıyı test et
            balance = self.bot.get_balance()
            if balance is not None:
                self.connect_btn.configure(text="Bağlandı ✓", state="disabled", fg_color="green")
                
                # Bakiye bilgilerini güncelle
                self.update_balance_display(balance)
                
                # Coin listesini güncelle
                self.update_coin_list()
                
                # Log mesajı ekle
                self.add_log("API bağlantısı başarılı - Bakiye ve coin listesi güncellendi", "api", "INFO")
                
                # API durumunu güncelle
                self.update_api_status(connected=True)
                
                # Dashboard'u güncelle
                self.update_dashboard()
                
                messagebox.showinfo("Başarılı", "API bağlantısı başarılı! Bakiye ve coin listesi güncellendi.")
            else:
                messagebox.showerror("Hata", "API bağlantısı başarısız!")
                
        except Exception as e:
            messagebox.showerror("Hata", f"API bağlantı hatası: {str(e)}")
    
    def update_balance_display(self, balance):
        """Bakiye bilgilerini GUI'de günceller"""
        try:
            if balance:
                # TRY bakiyesini güncelle
                try_balance = balance.get('TRY', {}).get('free', '0')
                self.total_balance_label.configure(text=f"Toplam Bakiye: {float(try_balance):.2f} TRY")
                
                # Güncel fiyatı güncelle (seçili coin için)
                if self.bot and hasattr(self, 'current_price_label'):
                    selected_coin = self.selected_coin.get()
                    if selected_coin:
                        current_price = self.bot.get_current_price(selected_coin)
                        self.current_price_label.configure(text=f"Güncel Fiyat: {current_price:.2f}")
                
                # Kar/Zarar bilgisini güncelle
                if hasattr(self, 'profit_label'):
                    self.profit_label.configure(text="Kar/Zarar: -- %")
                    
        except Exception as e:
            print(f"Bakiye güncelleme hatası: {e}")
    
    def add_system_log(self, message, level="INFO"):
        """Sistem loguna mesaj ekler"""
        try:
            if hasattr(self, 'system_log_text'):
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Renk kodları
                color_map = {
                    "INFO": "#00FF00",    # Yeşil
                    "WARNING": "#FFFF00", # Sarı
                    "ERROR": "#FF0000",   # Kırmızı
                    "DEBUG": "#00FFFF"    # Cyan
                }
                
                color = color_map.get(level, "#00FF00")
                log_entry = f"[{timestamp}] [{level}] {message}\n"
                
                # Log seviye filtresini kontrol et
                if hasattr(self, 'log_level_filter'):
                    selected_level = self.log_level_filter.get()
                    if selected_level != "Tümü" and selected_level != level:
                        return
                
                self.system_log_text.insert("end", log_entry)
                self.system_log_text.see("end")
                
        except Exception as e:
            print(f"Sistem log ekleme hatası: {e}")
    
    def clear_system_logs(self):
        """Sistem loglarını temizler"""
        try:
            if hasattr(self, 'system_log_text'):
                self.system_log_text.delete("1.0", "end")
                self.add_system_log("Log temizlendi", "INFO")
        except Exception as e:
            print(f"Log temizleme hatası: {e}")
    
    def save_system_logs(self):
        """Sistem loglarını dosyaya kaydeder"""
        try:
            if hasattr(self, 'system_log_text'):
                log_content = self.system_log_text.get("1.0", "end")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"system_logs_{timestamp}.txt"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                
                self.add_system_log(f"Loglar kaydedildi: {filename}", "INFO")
                from tkinter import messagebox
                messagebox.showinfo("Başarılı", f"Loglar {filename} dosyasına kaydedildi!")
                
        except Exception as e:
            print(f"Log kaydetme hatası: {e}")
            from tkinter import messagebox
            messagebox.showerror("Hata", f"Log kaydetme hatası: {str(e)}")
    
    def refresh_system_logs(self):
        """Sistem loglarını yeniler"""
        try:
            self.add_system_log("Loglar yenilendi", "INFO")
        except Exception as e:
            print(f"Log yenileme hatası: {e}")
    
    def update_coin_list(self):
        """Coin listesini API'den günceller"""
        try:
            if self.bot:
                # Mevcut coin çiftlerini al
                pairs = self.bot.get_available_pairs()
                if pairs:
                    # Sadece TRY çiftlerini filtrele
                    try_pairs = [pair for pair in pairs if pair.endswith('TRY')]
                    
                    # Coin combo'yu güncelle
                    if hasattr(self, 'coin_combo'):
                        self.coin_combo.configure(values=try_pairs)
                        if try_pairs:
                            self.coin_combo.set(try_pairs[0])  # İlk coin'i seç
                            
                    print(f"Coin listesi güncellendi: {len(try_pairs)} çift bulundu")
                else:
                    print("API'den coin listesi alınamadı, varsayılan liste kullanılıyor")
                    
        except Exception as e:
            print(f"Coin listesi güncelleme hatası: {e}")
    
    def start_bot(self):
        """Bot'u başlatır"""
        try:
            if not hasattr(self, 'bot') or self.bot is None:
                messagebox.showerror("Hata", "Önce API'ye bağlanın!")
                return
            
            coin = self.selected_coin.get()
            target = float(self.target_percentage.get())
            amount = float(self.trade_amount.get())
            
            if target <= 0 or amount <= 0:
                messagebox.showerror("Hata", "Hedef kar ve işlem miktarı 0'dan büyük olmalı!")
                return
            
            # Callback fonksiyonlarını ayarla
            self.bot.set_callbacks(
                price_callback=self.update_price_display,
                status_callback=self.update_status_display,
                trade_callback=self.on_trade_completed,
                balance_callback=self.update_balance_from_bot
            )
            
            # Bot'u başlat
            self.bot.start_trading(coin, target, amount)
            
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            
            # Log mesajı ekle
            self.add_log(f"Bot başlatıldı - {coin} - Hedef: %{target} - Miktar: {amount} TRY", "trading", "INFO")
            
            messagebox.showinfo("Başarılı", "Bot başlatıldı!")
            
        except ValueError:
            messagebox.showerror("Hata", "Hedef kar ve işlem miktarı sayısal değer olmalı!")
        except Exception as e:
            messagebox.showerror("Hata", f"Bot başlatma hatası: {str(e)}")
    
    def stop_bot(self):
        """Bot'u durdurur"""
        try:
            if hasattr(self, 'bot') and self.bot is not None:
                self.bot.stop_trading()
            
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            
            messagebox.showinfo("Başarılı", "Bot durduruldu!")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Bot durdurma hatası: {str(e)}")

    # Log Yönetimi Metodları
    def toggle_system_logs(self):
        """Sistem logları bölümünü açar/kapatır"""
        if self.system_logs_visible:
            self.system_logs_content.pack_forget()
            self.system_logs_button.configure(text="▶ Sistem Logları")
            self.system_logs_visible = False
        else:
            self.system_logs_content.pack(fill="both", expand=True, padx=5, pady=(0, 5))
            self.system_logs_button.configure(text="▼ Sistem Logları")
            self.system_logs_visible = True
    
    def toggle_trading_logs(self):
        """Trading logları bölümünü açar/kapatır"""
        if self.trading_logs_visible:
            self.trading_logs_content.pack_forget()
            self.trading_logs_button.configure(text="▶ Trading Logları")
            self.trading_logs_visible = False
        else:
            self.trading_logs_content.pack(fill="both", expand=True, padx=5, pady=(0, 5))
            self.trading_logs_button.configure(text="▼ Trading Logları")
            self.trading_logs_visible = True
    
    def toggle_api_logs(self):
        """API logları bölümünü açar/kapatır"""
        if self.api_logs_visible:
            self.api_logs_content.pack_forget()
            self.api_logs_button.configure(text="▶ API Logları")
            self.api_logs_visible = False
        else:
            self.api_logs_content.pack(fill="both", expand=True, padx=5, pady=(0, 5))
            self.api_logs_button.configure(text="▼ API Logları")
            self.api_logs_visible = True
    
    def toggle_error_logs(self):
        """Hata logları bölümünü açar/kapatır"""
        if self.error_logs_visible:
            self.error_logs_content.pack_forget()
            self.error_logs_button.configure(text="▶ Hata Logları")
            self.error_logs_visible = False
        else:
            self.error_logs_content.pack(fill="both", expand=True, padx=5, pady=(0, 5))
            self.error_logs_button.configure(text="▼ Hata Logları")
            self.error_logs_visible = True
    
    def clear_logs(self):
        """Tüm logları temizler"""
        try:
            self.system_log_text.delete("1.0", "end")
            self.trading_log_text.delete("1.0", "end")
            self.api_log_text.delete("1.0", "end")
            self.error_log_text.delete("1.0", "end")
            messagebox.showinfo("Başarılı", "Tüm loglar temizlendi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Loglar temizlenirken hata: {e}")
    
    def save_logs(self):
        """Logları dosyaya kaydeder"""
        try:
            from tkinter import filedialog
            from datetime import datetime
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Logları Kaydet",
                initialvalue=f"trading_bot_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"BTCTurk Trading Bot Logları - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 80 + "\n\n")
                    
                    f.write("SİSTEM LOGLARI:\n")
                    f.write("-" * 40 + "\n")
                    f.write(self.system_log_text.get("1.0", "end"))
                    f.write("\n\n")
                    
                    f.write("TRADING LOGLARI:\n")
                    f.write("-" * 40 + "\n")
                    f.write(self.trading_log_text.get("1.0", "end"))
                    f.write("\n\n")
                    
                    f.write("API LOGLARI:\n")
                    f.write("-" * 40 + "\n")
                    f.write(self.api_log_text.get("1.0", "end"))
                    f.write("\n\n")
                    
                    f.write("HATA LOGLARI:\n")
                    f.write("-" * 40 + "\n")
                    f.write(self.error_log_text.get("1.0", "end"))
                
                messagebox.showinfo("Başarılı", f"Loglar {filename} dosyasına kaydedildi.")
                
        except Exception as e:
            messagebox.showerror("Hata", f"Loglar kaydedilirken hata: {e}")
    
    def refresh_logs(self):
        """Logları yeniler"""
        try:
            # Örnek log mesajları ekle
            current_time = datetime.now().strftime('%H:%M:%S')
            
            # Sistem logları
            self.system_log_text.insert("end", f"[{current_time}] Sistem durumu kontrol edildi\n")
            
            # Trading logları
            self.trading_log_text.insert("end", f"[{current_time}] Piyasa verileri güncellendi\n")
            
            # API logları
            self.api_log_text.insert("end", f"[{current_time}] API bağlantısı kontrol edildi\n")
            
            # Scroll to bottom
            self.system_log_text.see("end")
            self.trading_log_text.see("end")
            self.api_log_text.see("end")
            
        except Exception as e:
            print(f"Log yenileme hatası: {e}")
    
    def filter_logs(self, level):
        """Log seviyesine göre filtreleme yapar"""
        # Bu metod log seviyesine göre filtreleme yapabilir
        # Şimdilik basit bir implementasyon
        pass
    
    def add_log(self, message, log_type="system", level="INFO"):
        """Log mesajı ekler"""
        try:
            # Sistem loguna her mesajı gönder (terminal benzeri)
            self.add_system_log(message, level)
            
            # Eski log sistemi kaldırıldı - artık sadece sistem logu kullanılıyor
                 
        except Exception as e:
            print(f"Log ekleme hatası: {e}")
    
    def update_price_display(self, price):
        """Fiyat güncellemelerini GUI'de gösterir"""
        try:
            if hasattr(self, 'current_price_label'):
                self.current_price_label.configure(text=f"Güncel Fiyat: {price:.2f}")
            self.add_log(f"Fiyat güncellendi: {price:.2f}", "trading", "DEBUG")
        except Exception as e:
            print(f"Fiyat güncelleme hatası: {e}")
    
    def update_status_display(self, status):
        """Durum güncellemelerini GUI'de gösterir"""
        try:
            if hasattr(self, 'status_label'):
                self.status_label.configure(text=f"Durum: {status}")
            self.add_log(f"Durum: {status}", "system", "INFO")
        except Exception as e:
            print(f"Durum güncelleme hatası: {e}")
    
    def update_status(self, message, status_type="info"):
        """
        Genel durum güncellemesi yapar
        
        Args:
            message: Durum mesajı
            status_type: Durum tipi (info, success, warning, error, trading, stopped, paused, emergency)
        """
        # Renk kodları
        color_map = {
            "info": "blue",
            "success": "green", 
            "warning": "orange",
            "error": "red",
            "trading": "green",
            "stopped": "red",
            "paused": "orange",
            "emergency": "red"
        }
        
        color = color_map.get(status_type, "blue")
        
        # API durum etiketini güncelle
        if hasattr(self, 'api_status_label'):
            self.api_status_label.configure(text=f"Durum: {message}", text_color=color)
        
        # Log'a ekle
        log_level = "ERROR" if status_type == "error" else "WARNING" if status_type == "warning" else "INFO"
        self.add_log(f"Sistem Durumu: {message}", "system", log_level)
    
    def on_trade_completed(self, trade_info):
        """İşlem tamamlandığında çağrılır"""
        try:
            self.add_log(f"İşlem tamamlandı: {trade_info}", "trading", "INFO")
            
            # İşlem geçmişine ekle (trade_info string ise parse et)
            if isinstance(trade_info, str):
                # Basit parsing - gerçek uygulamada daha detaylı olmalı
                trade_data = {
                    'type': 'Satış' if 'SATIŞ' in trade_info else 'Alış',
                    'coin': self.selected_coin.get(),
                    'status': 'Tamamlandı'
                }
            else:
                trade_data = trade_info
            
            self.add_trade_to_history(trade_data)
            
        except Exception as e:
            print(f"İşlem tamamlama hatası: {e}")
    
    def update_balance_from_bot(self):
        """Bot'tan bakiye güncellemesi"""
        try:
            if hasattr(self, 'bot') and self.bot:
                balance = self.bot.get_balance()
                if balance:
                    self.update_balance_display(balance)
                    self.add_log("Bakiye güncellendi", "api", "INFO")
        except Exception as e:
            print(f"Bakiye güncelleme hatası: {e}")
    
    def show_settings(self):
        """
        Ayarlar penceresini açar
        """
        try:
            # Ana uygulama referansını kullanarak ayarlar penceresini aç
            if hasattr(self, 'app_instance') and self.app_instance:
                self.app_instance.show_settings()
            else:
                # Fallback: Doğrudan SettingsWindow oluştur
                from settings_manager import SettingsWindow
                SettingsWindow(self.root, self.settings_manager)
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Hata", f"Ayarlar penceresi açılamadı: {str(e)}")
    
    def update_gui(self):
        """
        GUI güncellemelerini yapar
        """
        try:
            # Periyodik güncellemeler için gerekli işlemler
            self.root.after(1000, self.update_gui)  # Her saniye güncelle
        except Exception as e:
            print(f"GUI güncelleme hatası: {e}")

if __name__ == "__main__":
    try:
        # CustomTkinter ayarları
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Ana pencereyi oluştur
        root = ctk.CTk()
        root.title("BTCTurk Trading Bot v1.1.0")
        root.geometry("1200x800")
        root.minsize(800, 600)
        
        # Settings manager'ı başlat
        from settings_manager import SettingsManager
        settings_manager = SettingsManager()
        
        # GUI uygulamasını oluştur
        app = TradingBotGUI(root, None, settings_manager, None, None)
        
        # Ana döngüyü başlat
        root.mainloop()
        
    except Exception as e:
        print(f"GUI başlatma hatası: {e}")
        import traceback
        traceback.print_exc()