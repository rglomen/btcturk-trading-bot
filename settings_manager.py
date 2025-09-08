import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from loguru import logger
import customtkinter as ctk
from tkinter import messagebox, filedialog
from cryptography.fernet import Fernet
import base64

@dataclass
class BotSettings:
    """
    Bot ayarları veri sınıfı
    """
    # API Ayarları
    api_key: str = ""
    api_secret: str = ""
    
    # Trading Ayarları
    default_coin: str = "BTCTRY"
    default_target_percentage: float = 2.0
    default_trade_amount: float = 100.0
    
    # Risk Yönetimi
    max_daily_loss: float = 5.0
    max_position_size: float = 20.0
    stop_loss_percentage: float = -3.0
    
    # Strateji Ayarları
    price_check_interval: int = 1  # saniye
    trend_analysis_minutes: int = 5
    volatility_threshold: float = 3.0
    
    # GUI Ayarları
    theme: str = "dark"
    color_theme: str = "blue"
    window_geometry: str = "1200x800"
    
    # Bildirim Ayarları
    enable_sound_alerts: bool = True
    enable_popup_alerts: bool = True
    log_level: str = "INFO"

class SettingsManager:
    """
    Ayarları yöneten sınıf
    """
    
    def __init__(self, settings_file: str = "bot_settings.json"):
        self.settings_file = settings_file
        self.encryption_key = self._get_or_create_key()
        self.settings = BotSettings()
        self.load_settings()
    
    def _get_or_create_key(self) -> bytes:
        """
        Şifreleme anahtarını alır veya oluşturur
        """
        key_file = "encryption.key"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def _encrypt_sensitive_data(self, data: str) -> str:
        """
        Hassas verileri şifreler
        """
        if not data:
            return ""
        
        fernet = Fernet(self.encryption_key)
        encrypted = fernet.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def _decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """
        Şifrelenmiş verileri çözer
        """
        if not encrypted_data:
            return ""
        
        try:
            fernet = Fernet(self.encryption_key)
            decoded = base64.b64decode(encrypted_data.encode())
            return fernet.decrypt(decoded).decode()
        except Exception as e:
            logger.error(f"Şifre çözme hatası: {e}")
            return ""
    
    def save_settings(self):
        """
        Ayarları dosyaya kaydeder
        """
        try:
            settings_dict = asdict(self.settings)
            
            # Hassas verileri şifrele
            if settings_dict['api_key']:
                settings_dict['api_key'] = self._encrypt_sensitive_data(settings_dict['api_key'])
            if settings_dict['api_secret']:
                settings_dict['api_secret'] = self._encrypt_sensitive_data(settings_dict['api_secret'])
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_dict, f, indent=4, ensure_ascii=False)
            
            logger.info("Ayarlar kaydedildi")
            
        except Exception as e:
            logger.error(f"Ayar kaydetme hatası: {e}")
            raise
    
    def load_settings(self):
        """
        Ayarları dosyadan yükler
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings_dict = json.load(f)
                
                # Hassas verileri çöz
                if settings_dict.get('api_key'):
                    settings_dict['api_key'] = self._decrypt_sensitive_data(settings_dict['api_key'])
                if settings_dict.get('api_secret'):
                    settings_dict['api_secret'] = self._decrypt_sensitive_data(settings_dict['api_secret'])
                
                # Ayarları güncelle
                for key, value in settings_dict.items():
                    if hasattr(self.settings, key):
                        setattr(self.settings, key, value)
                
                logger.info("Ayarlar yüklendi")
            else:
                logger.info("Ayar dosyası bulunamadı, varsayılan ayarlar kullanılıyor")
                
        except Exception as e:
            logger.error(f"Ayar yükleme hatası: {e}")
            self.settings = BotSettings()  # Varsayılan ayarlara dön
    
    def get_all_settings(self) -> dict:
        """
        Tüm ayarları dict olarak döndürür
        """
        return asdict(self.settings)
    
    def reset_to_defaults(self):
        """
        Ayarları varsayılana sıfırlar
        """
        self.settings = BotSettings()
        self.save_settings()
        logger.info("Ayarlar varsayılana sıfırlandı")
    
    def export_settings(self, file_path: str):
        """
        Ayarları dışa aktarır (şifrelenmemiş)
        """
        try:
            settings_dict = asdict(self.settings)
            # API bilgilerini çıkar
            settings_dict.pop('api_key', None)
            settings_dict.pop('api_secret', None)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings_dict, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Ayarlar dışa aktarıldı: {file_path}")
            
        except Exception as e:
            logger.error(f"Ayar dışa aktarma hatası: {e}")
            raise
    
    def import_settings(self, file_path: str):
        """
        Ayarları içe aktarır
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                settings_dict = json.load(f)
            
            # Mevcut API bilgilerini koru
            current_api_key = self.settings.api_key
            current_api_secret = self.settings.api_secret
            
            # Ayarları güncelle
            for key, value in settings_dict.items():
                if hasattr(self.settings, key) and key not in ['api_key', 'api_secret']:
                    setattr(self.settings, key, value)
            
            # API bilgilerini geri yükle
            self.settings.api_key = current_api_key
            self.settings.api_secret = current_api_secret
            
            self.save_settings()
            logger.info(f"Ayarlar içe aktarıldı: {file_path}")
            
        except Exception as e:
            logger.error(f"Ayar içe aktarma hatası: {e}")
            raise

class SettingsWindow:
    """
    Ayarlar penceresi GUI sınıfı
    """
    
    def __init__(self, parent, settings_manager: SettingsManager, callback=None):
        self.parent = parent
        self.settings_manager = settings_manager
        self.callback = callback
        
        # Pencere oluştur
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Bot Ayarları")
        self.window.geometry("600x700")
        self.window.resizable(False, False)
        
        # Modal yap
        self.window.transient(parent)
        self.window.grab_set()
        
        # Değişkenler
        self.create_variables()
        self.create_widgets()
        self.load_current_settings()
        
        # Pencereyi ortala
        self.center_window()
    
    def create_variables(self):
        """
        Tkinter değişkenlerini oluşturur
        """
        # API Ayarları
        self.api_key_var = ctk.StringVar()
        self.api_secret_var = ctk.StringVar()
        
        # Trading Ayarları
        self.default_coin_var = ctk.StringVar()
        self.default_target_var = ctk.DoubleVar()
        self.default_amount_var = ctk.DoubleVar()
        
        # Risk Yönetimi
        self.max_daily_loss_var = ctk.DoubleVar()
        self.max_position_size_var = ctk.DoubleVar()
        self.stop_loss_var = ctk.DoubleVar()
        
        # Strateji Ayarları
        self.price_interval_var = ctk.IntVar()
        self.trend_minutes_var = ctk.IntVar()
        self.volatility_threshold_var = ctk.DoubleVar()
        
        # GUI Ayarları
        self.theme_var = ctk.StringVar()
        self.color_theme_var = ctk.StringVar()
        
        # Bildirim Ayarları
        self.sound_alerts_var = ctk.BooleanVar()
        self.popup_alerts_var = ctk.BooleanVar()
        self.log_level_var = ctk.StringVar()
    
    def create_widgets(self):
        """
        Widget'ları oluşturur
        """
        # Ana frame
        main_frame = ctk.CTkScrollableFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlık
        title = ctk.CTkLabel(main_frame, text="Bot Ayarları", 
                           font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=(0, 20))
        
        # API Ayarları
        self.create_api_section(main_frame)
        
        # Trading Ayarları
        self.create_trading_section(main_frame)
        
        # Risk Yönetimi
        self.create_risk_section(main_frame)
        
        # Strateji Ayarları
        self.create_strategy_section(main_frame)
        
        # GUI Ayarları
        self.create_gui_section(main_frame)
        
        # Bildirim Ayarları
        self.create_notification_section(main_frame)
        
        # Butonlar
        self.create_buttons(main_frame)
    
    def create_api_section(self, parent):
        """
        API ayarları bölümü
        """
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(frame, text="API Ayarları", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        ctk.CTkLabel(frame, text="API Key:").pack(anchor="w", padx=10)
        ctk.CTkEntry(frame, textvariable=self.api_key_var, show="*").pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(frame, text="API Secret:").pack(anchor="w", padx=10)
        ctk.CTkEntry(frame, textvariable=self.api_secret_var, show="*").pack(fill="x", padx=10, pady=(2, 15))
    
    def create_trading_section(self, parent):
        """
        Trading ayarları bölümü
        """
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(frame, text="Trading Ayarları", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        ctk.CTkLabel(frame, text="Varsayılan Coin:").pack(anchor="w", padx=10)
        ctk.CTkComboBox(frame, values=["BTCTRY", "ETHTRY", "ADATRY", "DOGETRY"], 
                       variable=self.default_coin_var).pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(frame, text="Varsayılan Hedef Kar (%):").pack(anchor="w", padx=10)
        ctk.CTkEntry(frame, textvariable=self.default_target_var).pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(frame, text="Varsayılan İşlem Miktarı (TRY):").pack(anchor="w", padx=10)
        ctk.CTkEntry(frame, textvariable=self.default_amount_var).pack(fill="x", padx=10, pady=(2, 15))
    
    def create_risk_section(self, parent):
        """
        Risk yönetimi bölümü
        """
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(frame, text="Risk Yönetimi", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        ctk.CTkLabel(frame, text="Maksimum Günlük Kayıp (%):").pack(anchor="w", padx=10)
        ctk.CTkEntry(frame, textvariable=self.max_daily_loss_var).pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(frame, text="Maksimum Pozisyon Büyüklüğü (%):").pack(anchor="w", padx=10)
        ctk.CTkEntry(frame, textvariable=self.max_position_size_var).pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(frame, text="Stop Loss (%):").pack(anchor="w", padx=10)
        ctk.CTkEntry(frame, textvariable=self.stop_loss_var).pack(fill="x", padx=10, pady=(2, 15))
    
    def create_strategy_section(self, parent):
        """
        Strateji ayarları bölümü
        """
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(frame, text="Strateji Ayarları", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        ctk.CTkLabel(frame, text="Fiyat Kontrol Aralığı (saniye):").pack(anchor="w", padx=10)
        ctk.CTkEntry(frame, textvariable=self.price_interval_var).pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(frame, text="Trend Analiz Süresi (dakika):").pack(anchor="w", padx=10)
        ctk.CTkEntry(frame, textvariable=self.trend_minutes_var).pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(frame, text="Volatilite Eşiği (%):").pack(anchor="w", padx=10)
        ctk.CTkEntry(frame, textvariable=self.volatility_threshold_var).pack(fill="x", padx=10, pady=(2, 15))
    
    def create_gui_section(self, parent):
        """
        GUI ayarları bölümü
        """
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(frame, text="Arayüz Ayarları", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        ctk.CTkLabel(frame, text="Tema:").pack(anchor="w", padx=10)
        theme_combo = ctk.CTkComboBox(frame, values=["dark", "light"], 
                                     variable=self.theme_var, command=self.on_theme_change)
        theme_combo.pack(fill="x", padx=10, pady=2)
        
        ctk.CTkLabel(frame, text="Renk Teması:").pack(anchor="w", padx=10)
        color_combo = ctk.CTkComboBox(frame, values=["blue", "green", "dark-blue"],
                                      variable=self.color_theme_var, command=self.on_color_theme_change)
        color_combo.pack(fill="x", padx=10, pady=(2, 15))
    
    def create_notification_section(self, parent):
        """
        Bildirim ayarları bölümü
        """
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(frame, text="Bildirim Ayarları", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        ctk.CTkCheckBox(frame, text="Ses Uyarıları", 
                       variable=self.sound_alerts_var).pack(anchor="w", padx=10, pady=2)
        
        ctk.CTkCheckBox(frame, text="Popup Uyarıları", 
                       variable=self.popup_alerts_var).pack(anchor="w", padx=10, pady=2)
        
        ctk.CTkLabel(frame, text="Log Seviyesi:").pack(anchor="w", padx=10)
        ctk.CTkComboBox(frame, values=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       variable=self.log_level_var).pack(fill="x", padx=10, pady=(2, 15))
    
    def create_buttons(self, parent):
        """
        Butonları oluşturur
        """
        button_frame = ctk.CTkFrame(parent)
        button_frame.pack(fill="x", pady=20)
        
        # İlk satır butonları
        row1 = ctk.CTkFrame(button_frame)
        row1.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(row1, text="Kaydet", command=self.save_settings,
                     fg_color="green", hover_color="darkgreen").pack(side="left", padx=5)
        
        ctk.CTkButton(row1, text="İptal", command=self.cancel,
                     fg_color="red", hover_color="darkred").pack(side="left", padx=5)
        
        ctk.CTkButton(row1, text="Varsayılana Sıfırla", 
                     command=self.reset_to_defaults).pack(side="left", padx=5)
        
        # İkinci satır butonları
        row2 = ctk.CTkFrame(button_frame)
        row2.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(row2, text="Dışa Aktar", 
                     command=self.export_settings).pack(side="left", padx=5)
        
        ctk.CTkButton(row2, text="İçe Aktar", 
                     command=self.import_settings).pack(side="left", padx=5)
    
    def load_current_settings(self):
        """
        Mevcut ayarları form'a yükler
        """
        settings = self.settings_manager.settings
        
        self.api_key_var.set(settings.api_key)
        self.api_secret_var.set(settings.api_secret)
        self.default_coin_var.set(settings.default_coin)
        self.default_target_var.set(settings.default_target_percentage)
        self.default_amount_var.set(settings.default_trade_amount)
        self.max_daily_loss_var.set(settings.max_daily_loss)
        self.max_position_size_var.set(settings.max_position_size)
        self.stop_loss_var.set(settings.stop_loss_percentage)
        self.price_interval_var.set(settings.price_check_interval)
        self.trend_minutes_var.set(settings.trend_analysis_minutes)
        self.volatility_threshold_var.set(settings.volatility_threshold)
        self.theme_var.set(settings.theme)
        self.color_theme_var.set(settings.color_theme)
        self.sound_alerts_var.set(settings.enable_sound_alerts)
        self.popup_alerts_var.set(settings.enable_popup_alerts)
        self.log_level_var.set(settings.log_level)
    
    def save_settings(self):
        """
        Ayarları kaydeder
        """
        try:
            settings = self.settings_manager.settings
            
            settings.api_key = self.api_key_var.get()
            settings.api_secret = self.api_secret_var.get()
            settings.default_coin = self.default_coin_var.get()
            settings.default_target_percentage = self.default_target_var.get()
            settings.default_trade_amount = self.default_amount_var.get()
            settings.max_daily_loss = self.max_daily_loss_var.get()
            settings.max_position_size = self.max_position_size_var.get()
            settings.stop_loss_percentage = self.stop_loss_var.get()
            settings.price_check_interval = self.price_interval_var.get()
            settings.trend_analysis_minutes = self.trend_minutes_var.get()
            settings.volatility_threshold = self.volatility_threshold_var.get()
            settings.theme = self.theme_var.get()
            settings.color_theme = self.color_theme_var.get()
            settings.enable_sound_alerts = self.sound_alerts_var.get()
            settings.enable_popup_alerts = self.popup_alerts_var.get()
            settings.log_level = self.log_level_var.get()
            
            self.settings_manager.save_settings()
            
            if self.callback:
                self.callback()
            
            messagebox.showinfo("Başarılı", "Ayarlar kaydedildi!")
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Hata", f"Ayar kaydetme hatası: {str(e)}")
    
    def cancel(self):
        """
        Pencereyi kapatır
        """
        self.window.destroy()
    
    def reset_to_defaults(self):
        """
        Varsayılan ayarlara sıfırlar
        """
        if messagebox.askyesno("Onay", "Tüm ayarları varsayılana sıfırlamak istediğinizden emin misiniz?"):
            self.settings_manager.reset_to_defaults()
            self.load_current_settings()
            messagebox.showinfo("Başarılı", "Ayarlar varsayılana sıfırlandı!")
    
    def export_settings(self):
        """
        Ayarları dışa aktarır
        """
        file_path = filedialog.asksaveasfilename(
            title="Ayarları Dışa Aktar",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.settings_manager.export_settings(file_path)
                messagebox.showinfo("Başarılı", "Ayarlar dışa aktarıldı!")
            except Exception as e:
                messagebox.showerror("Hata", f"Dışa aktarma hatası: {str(e)}")
    
    def import_settings(self):
        """
        Ayarları içe aktarır
        """
        file_path = filedialog.askopenfilename(
            title="Ayarları İçe Aktar",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.settings_manager.import_settings(file_path)
                self.load_current_settings()
                messagebox.showinfo("Başarılı", "Ayarlar içe aktarıldı!")
            except Exception as e:
                messagebox.showerror("Hata", f"İçe aktarma hatası: {str(e)}")
    
    def on_theme_change(self, value):
        """
        Tema değişikliğini anında uygular
        """
        try:
            ctk.set_appearance_mode(value)
            logger.info(f"Tema değiştirildi: {value}")
        except Exception as e:
            logger.error(f"Tema değiştirme hatası: {e}")
    
    def on_color_theme_change(self, value):
        """
        Renk teması değişikliğini anında uygular
        """
        try:
            # Geçerli renk temalarını kontrol et
            valid_themes = ["blue", "green", "dark-blue"]
            if value in valid_themes:
                ctk.set_default_color_theme(value)
                logger.info(f"Renk teması değiştirildi: {value}")
                # Pencereyi yeniden başlatmak için kullanıcıyı bilgilendir
                messagebox.showinfo("Bilgi", "Renk teması değişikliği için uygulamayı yeniden başlatmanız önerilir.")
            else:
                logger.warning(f"Geçersiz renk teması: {value}")
                messagebox.showwarning("Uyarı", f"'{value}' geçersiz bir renk teması. Varsayılan tema kullanılacak.")
                ctk.set_default_color_theme("blue")
        except Exception as e:
            logger.error(f"Renk teması değiştirme hatası: {e}")
            # Hata durumunda varsayılan temayı kullan
            try:
                ctk.set_default_color_theme("blue")
            except:
                pass
    
    def center_window(self):
        """
        Pencereyi ekranın ortasına yerleştirir
        """
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

if __name__ == "__main__":
    # Test için
    root = ctk.CTk()
    settings_manager = SettingsManager()
    
    def test_callback():
        print("Ayarlar güncellendi!")
    
    settings_window = SettingsWindow(root, settings_manager, test_callback)
    root.mainloop()