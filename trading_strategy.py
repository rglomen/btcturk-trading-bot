import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
import statistics

class TradingStrategy:
    """
    Alım-satım stratejilerini yöneten sınıf
    """
    
    def __init__(self):
        self.price_history = []
        self.trade_history = []
        self.min_price_points = 10  # Minimum fiyat noktası sayısı
        
    def add_price_point(self, price: float, timestamp: datetime = None):
        """
        Yeni fiyat noktası ekler
        
        Args:
            price: Fiyat değeri
            timestamp: Zaman damgası
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        self.price_history.append({
            'price': price,
            'timestamp': timestamp
        })
        
        # Son 1000 kayıdı tut
        if len(self.price_history) > 1000:
            self.price_history = self.price_history[-1000:]
    
    def get_price_trend(self, minutes: int = 5) -> str:
        """
        Belirtilen dakika içindeki fiyat trendini analiz eder
        
        Args:
            minutes: Analiz edilecek dakika sayısı
            
        Returns:
            str: 'rising', 'falling', 'stable'
        """
        if len(self.price_history) < self.min_price_points:
            return 'stable'
        
        # Son X dakikadaki fiyatları al
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_prices = [
            point['price'] for point in self.price_history 
            if point['timestamp'] >= cutoff_time
        ]
        
        if len(recent_prices) < 3:
            return 'stable'
        
        # Trend analizi
        first_half = recent_prices[:len(recent_prices)//2]
        second_half = recent_prices[len(recent_prices)//2:]
        
        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)
        
        change_percentage = ((avg_second - avg_first) / avg_first) * 100
        
        if change_percentage > 0.5:
            return 'rising'
        elif change_percentage < -0.5:
            return 'falling'
        else:
            return 'stable'
    
    def calculate_moving_average(self, periods: int = 20) -> float:
        """
        Hareketli ortalama hesaplar
        
        Args:
            periods: Periyot sayısı
            
        Returns:
            float: Hareketli ortalama
        """
        if len(self.price_history) < periods:
            return 0.0
        
        recent_prices = [point['price'] for point in self.price_history[-periods:]]
        return statistics.mean(recent_prices)
    
    def get_volatility(self, minutes: int = 10) -> float:
        """
        Fiyat volatilitesini hesaplar
        
        Args:
            minutes: Analiz edilecek dakika sayısı
            
        Returns:
            float: Volatilite yüzdesi
        """
        if len(self.price_history) < self.min_price_points:
            return 0.0
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_prices = [
            point['price'] for point in self.price_history 
            if point['timestamp'] >= cutoff_time
        ]
        
        if len(recent_prices) < 2:
            return 0.0
        
        max_price = max(recent_prices)
        min_price = min(recent_prices)
        avg_price = statistics.mean(recent_prices)
        
        if avg_price > 0:
            return ((max_price - min_price) / avg_price) * 100
        return 0.0
    
    def should_buy(self, current_price: float, balance: float) -> bool:
        """
        Alım yapılıp yapılmayacağını analiz eder
        
        Args:
            current_price: Güncel fiyat
            balance: Mevcut bakiye
            
        Returns:
            bool: Alım yapılacaksa True
        """
        # Temel kontroller
        if balance <= 0 or current_price <= 0:
            return False
        
        # Yeterli fiyat verisi var mı?
        if len(self.price_history) < self.min_price_points:
            return True  # İlk alım için
        
        # Trend analizi
        trend = self.get_price_trend()
        volatility = self.get_volatility()
        
        # Düşük volatilite ve stabil/yükselen trend
        if volatility < 2.0 and trend in ['stable', 'rising']:
            return True
        
        # Fiyat son 5 dakikada %1'den fazla düştüyse
        if len(self.price_history) >= 5:
            price_5min_ago = self.price_history[-5]['price']
            price_drop = ((price_5min_ago - current_price) / price_5min_ago) * 100
            if price_drop > 1.0:
                return True
        
        return False
    
    def should_sell(self, current_price: float, buy_price: float, target_percentage: float, 
                   stop_loss_percentage: float = -5.0) -> tuple:
        """
        Satım yapılıp yapılmayacağını analiz eder
        
        Args:
            current_price: Güncel fiyat
            buy_price: Alım fiyatı
            target_percentage: Hedef kar yüzdesi
            stop_loss_percentage: Stop loss yüzdesi
            
        Returns:
            tuple: (should_sell: bool, reason: str)
        """
        if buy_price <= 0 or current_price <= 0:
            return False, "Geçersiz fiyat"
        
        # Kar/zarar hesapla
        profit_percentage = ((current_price - buy_price) / buy_price) * 100
        
        # Hedef kara ulaşıldı mı?
        if profit_percentage >= target_percentage:
            return True, f"Hedef kar ulaşıldı: %{profit_percentage:.2f}"
        
        # Stop loss kontrolü
        if profit_percentage <= stop_loss_percentage:
            return True, f"Stop loss tetiklendi: %{profit_percentage:.2f}"
        
        # Trend analizi ile erken satış
        trend = self.get_price_trend(2)  # Son 2 dakika
        volatility = self.get_volatility(5)  # Son 5 dakika
        
        # Yüksek kar varken düşüş trendi başladıysa
        if profit_percentage > target_percentage * 0.8 and trend == 'falling' and volatility > 3.0:
            return True, f"Trend değişimi: %{profit_percentage:.2f} karda satış"
        
        return False, f"Bekleniyor: %{profit_percentage:.2f}"
    
    def get_recommended_amount(self, balance: float, risk_percentage: float = 10.0) -> float:
        """
        Önerilen işlem miktarını hesaplar
        
        Args:
            balance: Mevcut bakiye
            risk_percentage: Risk yüzdesi
            
        Returns:
            float: Önerilen işlem miktarı
        """
        if balance <= 0:
            return 0.0
        
        # Volatiliteye göre risk ayarla
        volatility = self.get_volatility()
        
        if volatility > 5.0:
            # Yüksek volatilite - riski azalt
            adjusted_risk = risk_percentage * 0.5
        elif volatility > 3.0:
            # Orta volatilite - riski biraz azalt
            adjusted_risk = risk_percentage * 0.7
        else:
            # Düşük volatilite - normal risk
            adjusted_risk = risk_percentage
        
        return balance * (adjusted_risk / 100.0)
    
    def add_trade_record(self, trade_type: str, price: float, amount: float, 
                        profit_percentage: float = 0.0):
        """
        İşlem kaydı ekler
        
        Args:
            trade_type: 'buy' veya 'sell'
            price: İşlem fiyatı
            amount: İşlem miktarı
            profit_percentage: Kar yüzdesi (satış için)
        """
        trade_record = {
            'type': trade_type,
            'price': price,
            'amount': amount,
            'profit_percentage': profit_percentage,
            'timestamp': datetime.now()
        }
        
        self.trade_history.append(trade_record)
        logger.info(f"İşlem kaydı eklendi: {trade_type.upper()} - {price} - %{profit_percentage:.2f}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Performans istatistiklerini döndürür
        
        Returns:
            dict: Performans verileri
        """
        if not self.trade_history:
            return {
                'total_trades': 0,
                'profitable_trades': 0,
                'loss_trades': 0,
                'average_profit': 0.0,
                'total_profit': 0.0,
                'win_rate': 0.0
            }
        
        sell_trades = [t for t in self.trade_history if t['type'] == 'sell']
        
        if not sell_trades:
            return {
                'total_trades': len(self.trade_history),
                'profitable_trades': 0,
                'loss_trades': 0,
                'average_profit': 0.0,
                'total_profit': 0.0,
                'win_rate': 0.0
            }
        
        profitable_trades = [t for t in sell_trades if t['profit_percentage'] > 0]
        loss_trades = [t for t in sell_trades if t['profit_percentage'] <= 0]
        
        total_profit = sum(t['profit_percentage'] for t in sell_trades)
        average_profit = total_profit / len(sell_trades) if sell_trades else 0.0
        win_rate = (len(profitable_trades) / len(sell_trades)) * 100 if sell_trades else 0.0
        
        return {
            'total_trades': len(sell_trades),
            'profitable_trades': len(profitable_trades),
            'loss_trades': len(loss_trades),
            'average_profit': average_profit,
            'total_profit': total_profit,
            'win_rate': win_rate
        }
    
    def reset_history(self):
        """
        Geçmiş verilerini temizler
        """
        self.price_history.clear()
        self.trade_history.clear()
        logger.info("Strateji geçmişi temizlendi")

class RiskManager:
    """
    Risk yönetimi sınıfı
    """
    
    def __init__(self, max_daily_loss: float = 5.0, max_position_size: float = 20.0):
        self.max_daily_loss = max_daily_loss  # Günlük maksimum kayıp yüzdesi
        self.max_position_size = max_position_size  # Maksimum pozisyon büyüklüğü yüzdesi
        self.daily_trades = []
        self.daily_profit_loss = 0.0
    
    def can_trade(self, proposed_amount: float, total_balance: float) -> tuple:
        """
        İşlem yapılıp yapılamayacağını kontrol eder
        
        Args:
            proposed_amount: Önerilen işlem miktarı
            total_balance: Toplam bakiye
            
        Returns:
            tuple: (can_trade: bool, reason: str)
        """
        # Günlük kayıp kontrolü
        if self.daily_profit_loss <= -self.max_daily_loss:
            return False, f"Günlük kayıp limiti aşıldı: %{self.daily_profit_loss:.2f}"
        
        # Pozisyon büyüklüğü kontrolü
        position_percentage = (proposed_amount / total_balance) * 100
        if position_percentage > self.max_position_size:
            return False, f"Pozisyon çok büyük: %{position_percentage:.2f} > %{self.max_position_size}"
        
        # Günlük işlem sayısı kontrolü (maksimum 10 işlem)
        today_trades = [t for t in self.daily_trades 
                       if t['timestamp'].date() == datetime.now().date()]
        if len(today_trades) >= 10:
            return False, "Günlük işlem limiti aşıldı (10)"
        
        return True, "İşlem onaylandı"
    
    def can_open_position(self, proposed_amount: float, total_balance: float = 10000.0) -> bool:
        """
        Pozisyon açılıp açılamayacağını kontrol eder
        
        Args:
            proposed_amount: Önerilen işlem miktarı
            total_balance: Toplam bakiye (varsayılan 10000 TRY)
            
        Returns:
            bool: Pozisyon açılabilir mi?
        """
        can_trade, reason = self.can_trade(proposed_amount, total_balance)
        if not can_trade:
            logger.warning(f"Pozisyon açılamıyor: {reason}")
        return can_trade
    
    def record_trade(self, profit_loss: float):
        """
        İşlem sonucunu kaydeder
        
        Args:
            profit_loss: Kar/zarar yüzdesi
        """
        trade_record = {
            'profit_loss': profit_loss,
            'timestamp': datetime.now()
        }
        
        self.daily_trades.append(trade_record)
        
        # Günlük kar/zarar güncelle
        today_trades = [t for t in self.daily_trades 
                       if t['timestamp'].date() == datetime.now().date()]
        self.daily_profit_loss = sum(t['profit_loss'] for t in today_trades)
    
    def reset_daily_stats(self):
        """
        Günlük istatistikleri sıfırlar
        """
        self.daily_profit_loss = 0.0
        # Sadece bugünkü işlemleri temizle
        self.daily_trades = [t for t in self.daily_trades 
                           if t['timestamp'].date() != datetime.now().date()]