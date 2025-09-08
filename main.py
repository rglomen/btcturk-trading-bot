#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BTCTurk Trading Bot - Ana Uygulama

Bu bot BTCTurk API'sini kullanarak otomatik alım-satım yapar.
Seçilen coin'i alır ve belirlenen kar yüzdesine ulaştığında satar.

Özellikler:
- Real-time fiyat takibi
- Otomatik alım-satım
- Modern GUI arayüzü
- Risk yönetimi
- Hata yönetimi ve loglama
- Güvenli ayar saklama

Geliştirici: AI Assistant
Tarih: 2024
"""

import sys
import os
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

# Proje kök dizinini sys.path'e ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import customtkinter as ctk
    from loguru import logger
    import tkinter as tk
    from tkinter import messagebox
except ImportError as e:
    print(f"Gerekli kütüphaneler yüklü değil: {e}")
    print("Lütfen 'pip install -r requirements.txt' komutunu çalıştırın")
    sys.exit(1)

# Proje modüllerini import et
try:
    from trading_bot import BTCTurkTradingBot
    from gui_main import TradingBotGUI
    from settings_manager import SettingsManager, SettingsWindow
    from error_handler import (
        initialize_error_system, get_error_handler, get_log_manager,
        ErrorType, ErrorSeverity, BotError, ErrorLogViewer
    )
    from trading_strategy import TradingStrategy, RiskManager
except ImportError as e:
    print(f"Proje modülleri yüklenemedi: {e}")
    print("Lütfen tüm dosyaların doğru konumda olduğundan emin olun")
    sys.exit(1)

class TradingBotApplication:
    """
    Ana uygulama sınıfı - Tüm bileşenleri yönetir
    """
    
    def __init__(self):
        self.root = None
        self.gui = None
        self.bot = None
        self.settings_manager = None
        self.log_manager = None
        self.error_handler = None
        self.trading_strategy = None
        self.risk_manager = None
        
        # Uygulama durumu
        self.is_running = False
        self.is_trading_active = False
        self.shutdown_event = threading.Event()
        
        # Thread'ler
        self.price_monitor_thread = None
        self.trading_thread = None
        
        self.initialize_application()
    
    def initialize_application(self):
        """
        Uygulamayı başlatır
        """
        try:
            # Çalışma dizinini ayarla
            os.chdir(project_root)
            
            # CustomTkinter ayarları
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            
            # Ana pencereyi oluştur
            self.root = ctk.CTk()
            self.root.title("BTCTurk Trading Bot v1.0")
            self.root.geometry("1400x900")
            self.root.minsize(1200, 800)
            self.root.state('zoomed')  # Tam ekran başlat
            
            # Pencere kapatma olayını yakala
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # Hata yönetim sistemini başlat
            self.log_manager, self.error_handler = initialize_error_system(
                log_dir="logs",
                log_level="INFO",
                gui_parent=self.root
            )
            
            # Ayar yöneticisini başlat
            self.settings_manager = SettingsManager("bot_settings.json")
            
            # Bot bileşenlerini başlat (API hatası durumunda devam et)
            try:
                self.initialize_bot_components()
            except Exception as e:
                self.error_handler.handle_error(e, "Bot Bileşenleri")
                # Bot bileşenleri başlatılamazsa None olarak ayarla
                self.bot = None
                self.trading_strategy = None
                self.risk_manager = None
            
            # GUI'yi başlat
            self.gui = TradingBotGUI(
                self.root,
                self.bot,
                self.settings_manager,
                self.error_handler,
                self,
                app_instance=self
            )
            
            # GUI güncellemelerini başlat
            self.gui.update_gui()
            
            # Hata callback'lerini kaydet
            self.register_error_callbacks()
            
            # Başlangıç kontrollerini yap
            self.perform_startup_checks()
            
            self.is_running = True
            logger.info("BTCTurk Trading Bot başlatıldı")
            
        except Exception as e:
            error_msg = f"Uygulama başlatma hatası: {e}"
            print(error_msg)
            if self.error_handler:
                self.error_handler.handle_error(
                    BotError(error_msg, ErrorType.SYSTEM_ERROR, ErrorSeverity.CRITICAL),
                    "Uygulama Başlatma"
                )
            sys.exit(1)
    
    def initialize_bot_components(self):
        """
        Bot bileşenlerini başlatır
        """
        try:
            # Trading bot'u başlat
            self.bot = BTCTurkTradingBot(
                api_key=self.settings_manager.settings.api_key,
                api_secret=self.settings_manager.settings.api_secret
            )
            
            # Trading stratejisini başlat
            self.trading_strategy = TradingStrategy()
            
            # Risk yöneticisini başlat
            self.risk_manager = RiskManager(
                max_daily_loss=self.settings_manager.settings.max_daily_loss,
                max_position_size=self.settings_manager.settings.max_position_size
            )
            
            logger.info("Bot bileşenleri başlatıldı")
            
        except Exception as e:
            raise BotError(
                f"Bot bileşenleri başlatılamadı: {e}",
                ErrorType.SYSTEM_ERROR,
                ErrorSeverity.CRITICAL
            )
    
    def register_error_callbacks(self):
        """
        Hata callback'lerini kaydeder
        """
        if not self.error_handler:
            return
        
        # API hataları için callback
        self.error_handler.register_error_callback(
            ErrorType.API_ERROR,
            self.handle_api_error
        )
        
        # Network hataları için callback
        self.error_handler.register_error_callback(
            ErrorType.NETWORK_ERROR,
            self.handle_network_error
        )
        
        # Trading hataları için callback
        self.error_handler.register_error_callback(
            ErrorType.TRADING_ERROR,
            self.handle_trading_error
        )
    
    def handle_api_error(self, error_info: dict):
        """
        API hatalarını işler
        """
        logger.warning("API hatası tespit edildi, bağlantı kontrol ediliyor...")
        
        # Bot'u geçici olarak durdur
        if self.is_trading_active:
            self.pause_trading()
        
        # GUI'de durumu güncelle
        if self.gui:
            self.gui.update_status("API Hatası - Bağlantı Kontrol Ediliyor", "error")
    
    def handle_network_error(self, error_info: dict):
        """
        Network hatalarını işler
        """
        logger.warning("Network hatası tespit edildi, yeniden bağlanmaya çalışılıyor...")
        
        # Otomatik yeniden bağlanma
        threading.Thread(target=self.retry_connection, daemon=True).start()
    
    def handle_trading_error(self, error_info: dict):
        """
        Trading hatalarını işler
        """
        logger.error("Trading hatası tespit edildi, güvenlik önlemleri alınıyor...")
        
        # Acil durum protokolü
        if self.is_trading_active:
            self.emergency_stop()
    
    def retry_connection(self):
        """
        Bağlantıyı yeniden kurmaya çalışır
        """
        max_retries = 5
        retry_delay = 10  # saniye
        
        for attempt in range(max_retries):
            try:
                if self.bot and self.bot.test_connection():
                    logger.info("Bağlantı yeniden kuruldu")
                    if self.gui:
                        self.gui.update_status("Bağlantı Yeniden Kuruldu", "success")
                    return True
                
            except Exception as e:
                logger.warning(f"Bağlantı denemesi {attempt + 1} başarısız: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
        
        logger.error("Bağlantı yeniden kurulamadı")
        if self.gui:
            self.gui.update_status("Bağlantı Başarısız", "error")
        
        return False
    
    def perform_startup_checks(self):
        """
        Başlangıç kontrollerini yapar
        """
        try:
            # API bağlantısını test et
            if self.bot and self.settings_manager.settings.api_key:
                if not self.bot.test_connection():
                    logger.warning("API bağlantısı kurulamadı")
                    if self.gui:
                        self.gui.update_status("API Bağlantısı Yok", "warning")
                else:
                    logger.info("API bağlantısı başarılı")
                    if self.gui:
                        self.gui.update_status("Hazır", "success")
            else:
                logger.info("API anahtarları ayarlanmamış")
                if self.gui:
                    self.gui.update_status("API Anahtarları Gerekli", "warning")
            
            # Log dizinini kontrol et
            log_dir = Path("logs")
            if not log_dir.exists():
                log_dir.mkdir(exist_ok=True)
                logger.info("Log dizini oluşturuldu")
            
            # Eski log dosyalarını temizle
            if self.log_manager:
                self.log_manager.clear_old_logs(30)
            
        except Exception as e:
            self.error_handler.handle_error(
                BotError(f"Başlangıç kontrolü hatası: {e}", ErrorType.SYSTEM_ERROR),
                "Başlangıç Kontrolü"
            )
    
    def start_trading(self, coin_pair: str, target_percentage: float, trade_amount: float):
        """
        Trading'i başlatır
        """
        try:
            if self.is_trading_active:
                logger.warning("Trading zaten aktif")
                return False
            
            if not self.bot or not self.bot.test_connection():
                raise BotError("API bağlantısı yok", ErrorType.API_ERROR, ErrorSeverity.HIGH)
            
            # Risk kontrolü
            if self.risk_manager:
                # Bakiye bilgisini al
                balance_info = self.bot.get_account_balance()
                try_balance = float(balance_info.get('TRY', {}).get('free', 0)) if balance_info else 10000.0
                
                if not self.risk_manager.can_open_position(trade_amount, try_balance):
                    raise BotError("Risk limitleri aşıldı", ErrorType.TRADING_ERROR, ErrorSeverity.HIGH)
            
            # Trading parametrelerini ayarla
            self.bot.set_trading_params(coin_pair, target_percentage, trade_amount)
            
            # Trading thread'ini başlat
            self.trading_thread = threading.Thread(
                target=self._trading_loop,
                args=(coin_pair, target_percentage, trade_amount),
                daemon=True
            )
            
            self.is_trading_active = True
            self.trading_thread.start()
            
            logger.info(f"Trading başlatıldı: {coin_pair}, Hedef: %{target_percentage}, Miktar: {trade_amount}")
            
            if self.gui:
                self.gui.update_status(f"Trading Aktif - {coin_pair}", "trading")
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Trading Başlatma")
            return False
    
    def _trading_loop(self, coin_pair: str, target_percentage: float, trade_amount: float):
        """
        Ana trading döngüsü
        """
        try:
            check_interval = self.settings_manager.settings.price_check_interval
            
            while self.is_trading_active and not self.shutdown_event.is_set():
                try:
                    # Fiyat bilgisini al
                    current_price = self.bot.get_current_price(coin_pair)
                    
                    if current_price is None:
                        logger.warning("Fiyat bilgisi alınamadı")
                        time.sleep(check_interval)
                        continue
                    
                    # GUI'yi güncelle
                    if self.gui:
                        self.gui.update_price_display(coin_pair, current_price)
                    
                    # Trading stratejisini kontrol et
                    if self.trading_strategy:
                        self.trading_strategy.add_price_data(current_price)
                        
                        # Alım sinyali kontrolü
                        if not self.bot.has_position and self.trading_strategy.should_buy():
                            if self.bot.place_buy_order(coin_pair, trade_amount):
                                logger.info(f"Alım emri verildi: {coin_pair} - {trade_amount} TRY")
                                
                                if self.risk_manager:
                                    self.risk_manager.record_trade('buy', trade_amount, current_price)
                        
                        # Satım sinyali kontrolü
                        elif self.bot.has_position:
                            profit_percentage = self.bot.calculate_profit_percentage(current_price)
                            
                            # Hedef kar veya stop loss kontrolü
                            should_sell = (
                                profit_percentage >= target_percentage or
                                profit_percentage <= self.settings_manager.settings.stop_loss_percentage or
                                (self.trading_strategy and self.trading_strategy.should_sell())
                            )
                            
                            if should_sell:
                                if self.bot.place_sell_order(coin_pair):
                                    logger.info(f"Satım emri verildi: {coin_pair} - Kar: %{profit_percentage:.2f}")
                                    
                                    if self.risk_manager:
                                        self.risk_manager.record_trade('sell', 0, current_price)
                                    
                                    # Trading'i durdur (tek işlem modu)
                                    self.stop_trading()
                                    break
                    
                    time.sleep(check_interval)
                    
                except Exception as e:
                    self.error_handler.handle_error(
                        BotError(f"Trading döngüsü hatası: {e}", ErrorType.TRADING_ERROR),
                        "Trading Döngüsü"
                    )
                    time.sleep(check_interval * 2)  # Hata durumunda daha uzun bekle
            
        except Exception as e:
            self.error_handler.handle_error(
                BotError(f"Trading döngüsü kritik hatası: {e}", ErrorType.TRADING_ERROR, ErrorSeverity.CRITICAL),
                "Trading Döngüsü"
            )
        finally:
            self.is_trading_active = False
            if self.gui:
                self.gui.update_status("Trading Durduruldu", "stopped")
    
    def stop_trading(self):
        """
        Trading'i durdurur
        """
        try:
            self.is_trading_active = False
            
            if self.trading_thread and self.trading_thread.is_alive():
                self.trading_thread.join(timeout=5)
            
            logger.info("Trading durduruldu")
            
            if self.gui:
                self.gui.update_status("Trading Durduruldu", "stopped")
            
        except Exception as e:
            self.error_handler.handle_error(e, "Trading Durdurma")
    
    def pause_trading(self):
        """
        Trading'i geçici olarak duraklatır
        """
        self.is_trading_active = False
        logger.info("Trading duraklatıldı")
        
        if self.gui:
            self.gui.update_status("Trading Duraklatıldı", "paused")
    
    def emergency_stop(self):
        """
        Acil durum durdurması
        """
        try:
            logger.critical("ACİL DURUM DURDURMA AKTİF!")
            
            # Tüm açık pozisyonları kapat
            if self.bot and self.bot.has_position:
                self.bot.emergency_sell_all()
            
            # Trading'i durdur
            self.stop_trading()
            
            # GUI'de uyarı göster
            if self.gui:
                self.gui.update_status("ACİL DURUM DURDURMA", "emergency")
                messagebox.showerror(
                    "Acil Durum",
                    "Acil durum protokolü aktif edildi!\nTüm işlemler durduruldu."
                )
            
        except Exception as e:
            logger.critical(f"Acil durum durdurma hatası: {e}")
    
    def show_settings(self):
        """
        Ayarlar penceresini gösterir
        """
        try:
            def settings_callback():
                # Ayarlar değiştiğinde bot'u yeniden yapılandır
                self.reconfigure_bot()
            
            SettingsWindow(self.root, self.settings_manager, settings_callback)
            
        except Exception as e:
            self.error_handler.handle_error(e, "Ayarlar Penceresi")
    
    def show_error_log(self):
        """
        Hata log penceresini gösterir
        """
        try:
            ErrorLogViewer(self.root, self.error_handler)
        except Exception as e:
            self.error_handler.handle_error(e, "Hata Log Penceresi")
    
    def reconfigure_bot(self):
        """
        Bot'u yeni ayarlara göre yeniden yapılandırır
        """
        try:
            # Trading aktifse durdur
            if self.is_trading_active:
                self.stop_trading()
            
            # Bot'u yeniden yapılandır
            if self.bot:
                self.bot.update_credentials(
                    self.settings_manager.settings.api_key,
                    self.settings_manager.settings.api_secret
                )
            
            # Stratejiyi güncelle
            if self.trading_strategy:
                self.trading_strategy.update_parameters(
                    trend_minutes=self.settings_manager.settings.trend_analysis_minutes,
                    volatility_threshold=self.settings_manager.settings.volatility_threshold
                )
            
            # Risk yöneticisini güncelle
            if self.risk_manager:
                self.risk_manager.update_limits(
                    max_daily_loss=self.settings_manager.settings.max_daily_loss,
                    max_position_size=self.settings_manager.settings.max_position_size,
                    stop_loss_percentage=self.settings_manager.settings.stop_loss_percentage
                )
            
            # GUI temasını güncelle
            if self.gui:
                ctk.set_appearance_mode(self.settings_manager.settings.theme)
                ctk.set_default_color_theme(self.settings_manager.settings.color_theme)
            
            logger.info("Bot yeniden yapılandırıldı")
            
        except Exception as e:
            self.error_handler.handle_error(e, "Bot Yeniden Yapılandırma")
    
    def on_closing(self):
        """
        Uygulama kapatılırken çağrılır
        """
        try:
            logger.info("Uygulama kapatılıyor...")
            
            # Trading'i durdur
            if self.is_trading_active:
                self.stop_trading()
            
            # Shutdown event'ini set et
            self.shutdown_event.set()
            
            # Thread'lerin bitmesini bekle
            if self.trading_thread and self.trading_thread.is_alive():
                self.trading_thread.join(timeout=3)
            
            # Ayarları kaydet
            if self.settings_manager:
                self.settings_manager.save_settings()
            
            # Pencereyi kapat
            self.root.quit()
            self.root.destroy()
            
            logger.info("Uygulama kapatıldı")
            
        except Exception as e:
            print(f"Kapatma hatası: {e}")
        finally:
            sys.exit(0)
    
    def run(self):
        """
        Uygulamayı çalıştırır
        """
        try:
            logger.info("GUI başlatılıyor...")
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Kullanıcı tarafından durduruldu")
            self.on_closing()
        except Exception as e:
            logger.critical(f"Uygulama çalıştırma hatası: {e}")
            self.on_closing()

def main():
    """
    Ana fonksiyon
    """
    try:
        # Splash screen göster (isteğe bağlı)
        print("="*60)
        print("          BTCTurk Trading Bot v1.0")
        print("          Otomatik Alım-Satım Botu")
        print("="*60)
        print("Başlatılıyor...")
        
        # Uygulamayı başlat
        app = TradingBotApplication()
        app.run()
        
    except KeyboardInterrupt:
        print("\nUygulama kullanıcı tarafından durduruldu")
    except Exception as e:
        print(f"Kritik hata: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Uygulama sonlandırıldı")

if __name__ == "__main__":
    main()