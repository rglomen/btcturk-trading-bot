import os
import sys
import traceback
import functools
from datetime import datetime
from typing import Optional, Callable, Any, Dict
from enum import Enum
from loguru import logger
import customtkinter as ctk
from tkinter import messagebox
import json
import threading
from pathlib import Path

class ErrorType(Enum):
    """
    Hata türleri
    """
    API_ERROR = "API_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    TRADING_ERROR = "TRADING_ERROR"
    GUI_ERROR = "GUI_ERROR"
    CONFIG_ERROR = "CONFIG_ERROR"
    DATA_ERROR = "DATA_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

class ErrorSeverity(Enum):
    """
    Hata önem seviyeleri
    """
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class BotError(Exception):
    """
    Bot özel hata sınıfı
    """
    
    def __init__(self, message: str, error_type: ErrorType = ErrorType.UNKNOWN_ERROR, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, details: Dict = None):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.severity = severity
        self.details = details or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        """
        Hata bilgilerini dictionary'ye çevirir
        """
        return {
            "message": self.message,
            "error_type": self.error_type.value,
            "severity": self.severity.value,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "traceback": traceback.format_exc()
        }

class LogManager:
    """
    Log yönetim sınıfı
    """
    
    def __init__(self, log_dir: str = "logs", max_file_size: str = "10 MB", 
                 retention: str = "30 days", log_level: str = "INFO"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Loguru yapılandırması
        logger.remove()  # Varsayılan handler'ı kaldır
        
        # Konsol log
        logger.add(
            sys.stdout,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True
        )
        
        # Genel log dosyası
        logger.add(
            self.log_dir / "bot_{time:YYYY-MM-DD}.log",
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="1 day",
            retention=retention,
            compression="zip"
        )
        
        # Hata log dosyası
        logger.add(
            self.log_dir / "errors_{time:YYYY-MM-DD}.log",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
            rotation=max_file_size,
            retention=retention,
            compression="zip"
        )
        
        # Trading log dosyası
        logger.add(
            self.log_dir / "trading_{time:YYYY-MM-DD}.log",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
            filter=lambda record: "TRADE" in record["extra"],
            rotation="1 day",
            retention=retention
        )
        
        # API log dosyası
        logger.add(
            self.log_dir / "api_{time:YYYY-MM-DD}.log",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            filter=lambda record: "API" in record["extra"],
            rotation=max_file_size,
            retention=retention
        )
        
        logger.info("Log sistemi başlatıldı")
    
    def log_trade(self, message: str, **kwargs):
        """
        Trading işlemlerini loglar
        """
        logger.bind(TRADE=True).info(message, **kwargs)
    
    def log_api(self, message: str, level: str = "DEBUG", **kwargs):
        """
        API işlemlerini loglar
        """
        log_func = getattr(logger.bind(API=True), level.lower())
        log_func(message, **kwargs)
    
    def get_log_files(self) -> list:
        """
        Log dosyalarının listesini döner
        """
        return list(self.log_dir.glob("*.log"))
    
    def clear_old_logs(self, days: int = 30):
        """
        Eski log dosyalarını temizler
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for log_file in self.log_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_date:
                log_file.unlink()
                logger.info(f"Eski log dosyası silindi: {log_file}")

class ErrorHandler:
    """
    Hata yönetim sınıfı
    """
    
    def __init__(self, log_manager: LogManager, gui_parent=None):
        self.log_manager = log_manager
        self.gui_parent = gui_parent
        self.error_history = []
        self.error_callbacks = {}
        self.max_history = 1000
        
        # Sistem hata yakalayıcısını ayarla
        sys.excepthook = self.handle_exception
        
        logger.info("Hata yöneticisi başlatıldı")
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        Yakalanmamış hataları işler
        """
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = f"Yakalanmamış hata: {exc_type.__name__}: {exc_value}"
        tb_str = ''.join(traceback.format_tb(exc_traceback))
        
        logger.error(f"{error_msg}\n{tb_str}")
        
        # GUI'de hata göster
        if self.gui_parent:
            self.show_error_dialog(
                "Kritik Hata",
                f"{error_msg}\n\nUygulama kapatılabilir.",
                ErrorSeverity.CRITICAL
            )
    
    def handle_error(self, error: Exception, context: str = "", 
                    error_type: ErrorType = ErrorType.UNKNOWN_ERROR,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    show_dialog: bool = True) -> bool:
        """
        Hataları işler ve loglar
        """
        try:
            # BotError ise bilgileri al
            if isinstance(error, BotError):
                error_type = error.error_type
                severity = error.severity
                error_msg = error.message
                details = error.details
            else:
                error_msg = str(error)
                details = {"exception_type": type(error).__name__}
            
            # Hata bilgilerini oluştur
            error_info = {
                "timestamp": datetime.now().isoformat(),
                "message": error_msg,
                "context": context,
                "error_type": error_type.value,
                "severity": severity.value,
                "details": details,
                "traceback": traceback.format_exc()
            }
            
            # Hata geçmişine ekle
            self.error_history.append(error_info)
            if len(self.error_history) > self.max_history:
                self.error_history.pop(0)
            
            # Log'a yaz
            log_msg = f"[{error_type.value}] {context}: {error_msg}"
            
            if severity == ErrorSeverity.CRITICAL:
                logger.critical(log_msg)
            elif severity == ErrorSeverity.HIGH:
                logger.error(log_msg)
            elif severity == ErrorSeverity.MEDIUM:
                logger.warning(log_msg)
            else:
                logger.info(log_msg)
            
            # Callback'leri çağır
            if error_type in self.error_callbacks:
                for callback in self.error_callbacks[error_type]:
                    try:
                        callback(error_info)
                    except Exception as cb_error:
                        logger.error(f"Error callback hatası: {cb_error}")
            
            # GUI dialog göster
            if show_dialog and self.gui_parent and severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                self.show_error_dialog(
                    f"{error_type.value} Hatası",
                    f"{context}\n\n{error_msg}",
                    severity
                )
            
            return True
            
        except Exception as handler_error:
            logger.critical(f"Hata işleyicisinde hata: {handler_error}")
            return False
    
    def show_error_dialog(self, title: str, message: str, severity: ErrorSeverity):
        """
        Hata dialog'u gösterir
        """
        def show_dialog():
            if severity == ErrorSeverity.CRITICAL:
                messagebox.showerror(title, message)
            elif severity == ErrorSeverity.HIGH:
                messagebox.showerror(title, message)
            elif severity == ErrorSeverity.MEDIUM:
                messagebox.showwarning(title, message)
            else:
                messagebox.showinfo(title, message)
        
        # Ana thread'de çalıştır
        if threading.current_thread() == threading.main_thread():
            show_dialog()
        else:
            self.gui_parent.after(0, show_dialog)
    
    def register_error_callback(self, error_type: ErrorType, callback: Callable):
        """
        Hata türü için callback kaydeder
        """
        if error_type not in self.error_callbacks:
            self.error_callbacks[error_type] = []
        self.error_callbacks[error_type].append(callback)
    
    def get_error_statistics(self) -> Dict:
        """
        Hata istatistiklerini döner
        """
        stats = {
            "total_errors": len(self.error_history),
            "by_type": {},
            "by_severity": {},
            "recent_errors": self.error_history[-10:] if self.error_history else []
        }
        
        for error in self.error_history:
            error_type = error["error_type"]
            severity = error["severity"]
            
            stats["by_type"][error_type] = stats["by_type"].get(error_type, 0) + 1
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
        
        return stats
    
    def export_error_log(self, file_path: str):
        """
        Hata geçmişini dosyaya aktarır
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "export_date": datetime.now().isoformat(),
                    "error_history": self.error_history,
                    "statistics": self.get_error_statistics()
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Hata geçmişi dışa aktarıldı: {file_path}")
            
        except Exception as e:
            logger.error(f"Hata geçmişi dışa aktarma hatası: {e}")
            raise

def error_handler_decorator(error_type: ErrorType = ErrorType.UNKNOWN_ERROR,
                          severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                          context: str = "",
                          show_dialog: bool = False,
                          return_on_error: Any = None):
    """
    Fonksiyonları hata yakalama ile sarar
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Global error handler varsa kullan
                if hasattr(wrapper, '_error_handler'):
                    wrapper._error_handler.handle_error(
                        e, 
                        context or f"{func.__name__}",
                        error_type,
                        severity,
                        show_dialog
                    )
                else:
                    logger.error(f"Hata yakalandı {func.__name__}: {e}")
                
                return return_on_error
        
        return wrapper
    return decorator

def retry_on_error(max_retries: int = 3, delay: float = 1.0, 
                  backoff_factor: float = 2.0,
                  exceptions: tuple = (Exception,)):
    """
    Hata durumunda yeniden deneme decorator'u
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(f"{func.__name__} başarısız (deneme {attempt + 1}/{max_retries + 1}): {e}")
                        logger.info(f"{current_delay} saniye bekleniyor...")
                        
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(f"{func.__name__} {max_retries + 1} denemeden sonra başarısız: {e}")
                        raise
            
            raise last_exception
        
        return wrapper
    return decorator

class ErrorLogViewer:
    """
    Hata log görüntüleyici GUI
    """
    
    def __init__(self, parent, error_handler: ErrorHandler):
        self.parent = parent
        self.error_handler = error_handler
        
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Hata Geçmişi")
        self.window.geometry("800x600")
        
        self.create_widgets()
        self.load_error_history()
    
    def create_widgets(self):
        """
        Widget'ları oluşturur
        """
        # Ana frame
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Başlık
        title = ctk.CTkLabel(main_frame, text="Hata Geçmişi", 
                           font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=(10, 20))
        
        # İstatistikler frame
        stats_frame = ctk.CTkFrame(main_frame)
        stats_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.stats_label = ctk.CTkLabel(stats_frame, text="")
        self.stats_label.pack(pady=10)
        
        # Hata listesi
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.error_textbox = ctk.CTkTextbox(list_frame)
        self.error_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Butonlar
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkButton(button_frame, text="Yenile", 
                     command=self.load_error_history).pack(side="left", padx=5)
        
        ctk.CTkButton(button_frame, text="Temizle", 
                     command=self.clear_history).pack(side="left", padx=5)
        
        ctk.CTkButton(button_frame, text="Dışa Aktar", 
                     command=self.export_history).pack(side="left", padx=5)
    
    def load_error_history(self):
        """
        Hata geçmişini yükler
        """
        stats = self.error_handler.get_error_statistics()
        
        # İstatistikleri göster
        stats_text = f"Toplam Hata: {stats['total_errors']}\n"
        stats_text += "Türe Göre: " + ", ".join([f"{k}: {v}" for k, v in stats['by_type'].items()]) + "\n"
        stats_text += "Önem Seviyesine Göre: " + ", ".join([f"{k}: {v}" for k, v in stats['by_severity'].items()])
        
        self.stats_label.configure(text=stats_text)
        
        # Hata listesini göster
        self.error_textbox.delete("1.0", "end")
        
        for error in reversed(self.error_handler.error_history[-50:]):  # Son 50 hata
            error_text = f"[{error['timestamp']}] {error['severity']} - {error['error_type']}\n"
            error_text += f"Bağlam: {error['context']}\n"
            error_text += f"Mesaj: {error['message']}\n"
            if error['details']:
                error_text += f"Detaylar: {error['details']}\n"
            error_text += "-" * 80 + "\n\n"
            
            self.error_textbox.insert("end", error_text)
    
    def clear_history(self):
        """
        Hata geçmişini temizler
        """
        if messagebox.askyesno("Onay", "Hata geçmişini temizlemek istediğinizden emin misiniz?"):
            self.error_handler.error_history.clear()
            self.load_error_history()
            messagebox.showinfo("Başarılı", "Hata geçmişi temizlendi!")
    
    def export_history(self):
        """
        Hata geçmişini dışa aktarır
        """
        from tkinter import filedialog
        
        file_path = filedialog.asksaveasfilename(
            title="Hata Geçmişini Dışa Aktar",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.error_handler.export_error_log(file_path)
                messagebox.showinfo("Başarılı", "Hata geçmişi dışa aktarıldı!")
            except Exception as e:
                messagebox.showerror("Hata", f"Dışa aktarma hatası: {str(e)}")

# Global değişkenler
_log_manager = None
_error_handler = None

def initialize_error_system(log_dir: str = "logs", log_level: str = "INFO", gui_parent=None):
    """
    Hata sistemini başlatır
    """
    global _log_manager, _error_handler
    
    _log_manager = LogManager(log_dir=log_dir, log_level=log_level)
    _error_handler = ErrorHandler(_log_manager, gui_parent)
    
    logger.info("Hata yönetim sistemi başlatıldı")
    
    return _log_manager, _error_handler

def get_error_handler() -> Optional[ErrorHandler]:
    """
    Global error handler'ı döner
    """
    return _error_handler

def get_log_manager() -> Optional[LogManager]:
    """
    Global log manager'ı döner
    """
    return _log_manager

if __name__ == "__main__":
    # Test için
    log_manager, error_handler = initialize_error_system()
    
    # Test hataları
    try:
        raise BotError("Test hatası", ErrorType.API_ERROR, ErrorSeverity.HIGH)
    except Exception as e:
        error_handler.handle_error(e, "Test bağlamı")
    
    print("Hata istatistikleri:", error_handler.get_error_statistics())