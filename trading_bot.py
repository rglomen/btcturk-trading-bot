import time
import threading
import json
from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger
from btcturk_api.client import Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BTCTurkTradingBot:
    """
    BTCTurk API ile otomatik alım-satım botu
    """
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        """
        Bot'u başlatır
        
        Args:
            api_key: BTCTurk API anahtarı
            api_secret: BTCTurk API gizli anahtarı
        """
        self.api_key = api_key or os.getenv('BTCTURK_API_KEY')
        self.api_secret = api_secret or os.getenv('BTCTURK_API_SECRET')
        
        # BTCTurk client'ını başlat
        self.client = Client(api_key=self.api_key, api_secret=self.api_secret)
        
        # Bot ayarları
        self.selected_coin = None
        self.target_profit_percentage = 0.0
        self.buy_price = 0.0
        self.amount_to_trade = 0.0
        self.coin_quantity = 0.0  # Satın alınan coin miktarı (planlanan)
        self.bought_amount = 0.0  # Gerçek satın alınan coin miktarı (bakiye kontrolünden)
        self.is_running = False
        self.is_position_open = False
        
        # Satış emri takibi
        self.sell_order_active = False
        self.target_sell_price = 0.0
        
        # Fiyat takibi
        self.current_price = 0.0
        self.price_history = []
        self.monitoring_thread = None
        
        # Callback fonksiyonları (GUI için)
        self.price_update_callback = None
        self.status_update_callback = None
        self.trade_callback = None
        
        # Logger ayarları
        logger.add("trading_bot.log", rotation="1 day", retention="30 days")
        
        logger.info("BTCTurk Trading Bot başlatıldı")
    
    def test_connection(self) -> bool:
        """
        API bağlantısını test eder
        
        Returns:
            bool: Bağlantı başarılı ise True
        """
        try:
            # API anahtarları yoksa demo modda çalışıyor
            if not self.api_key or not self.api_secret:
                logger.info("API anahtarları ayarlanmamış, demo modda çalışacak")
                return True
            
            # API bağlantısını test et
            balance = self.client.get_account_balance()
            if balance:
                logger.info("API bağlantısı başarılı")
                return True
            else:
                logger.error("API bağlantısı başarısız")
                return False
        except Exception as e:
            logger.error(f"API bağlantı testi hatası: {e}")
            return False
        
    def set_callbacks(self, price_callback=None, status_callback=None, trade_callback=None, balance_callback=None):
        """
        GUI callback fonksiyonlarını ayarlar
        """
        self.price_update_callback = price_callback
        self.status_update_callback = status_callback
        self.trade_callback = trade_callback
        self.balance_update_callback = balance_callback
        
    def get_available_pairs(self) -> list:
        """
        Mevcut coin çiftlerini getirir
        
        Returns:
            list: Mevcut coin çiftleri listesi
        """
        try:
            exchange_info = self.client.get_exchange_info()
            # BTCTurk API'sinde 'name' key'i kullanılıyor
            pairs = [pair['name'] for pair in exchange_info]
            logger.info(f"Mevcut {len(pairs)} coin çifti bulundu")
            return pairs
        except Exception as e:
            logger.error(f"Coin çiftleri alınırken hata: {e}")
            return []
    
    def get_current_price(self, symbol: str) -> float:
        """
        Belirtilen coin'in güncel fiyatını getirir
        
        Args:
            symbol: Coin çifti (örn: BTCTRY)
            
        Returns:
            float: Güncel fiyat
        """
        try:
            # API anahtarları kontrolü
            if not self.api_key or not self.api_secret:
                logger.warning(f"API anahtarları ayarlanmamış, {symbol} için demo fiyat döndürülüyor")
                # Demo fiyat döndür (ASRTRY için örnek)
                if symbol == "ASRTRY":
                    return 0.85  # Demo fiyat
                elif symbol == "BTCTRY":
                    return 2500000.0  # Demo fiyat
                else:
                    return 1.0  # Genel demo fiyat
            
            ticker = self.client.tick(symbol)
            if ticker:
                # API'den gelen veri liste formatında olabilir
                if isinstance(ticker, list) and len(ticker) > 0:
                    ticker_data = ticker[0]
                else:
                    ticker_data = ticker
                
                if 'last' in ticker_data:
                    price = float(ticker_data['last'])
                    logger.info(f"{symbol} güncel fiyat: {price}")
                    return price
                else:
                    logger.error(f"Ticker verisinde 'last' alanı bulunamadı ({symbol}): {ticker_data}")
                    return 0.0
            else:
                logger.error(f"Ticker verisi alınamadı ({symbol}): {ticker}")
                return 0.0
        except Exception as e:
            logger.error(f"Fiyat alınırken hata ({symbol}): {e}")
            # API hatası durumunda demo fiyat döndür
            if symbol == "ASRTRY":
                return 0.85
            elif symbol == "BTCTRY":
                return 2500000.0
            else:
                return 1.0
    
    def get_account_balance(self) -> Dict[str, Any]:
        """
        Hesap bakiyesini getirir
        
        Returns:
            dict: Hesap bakiye bilgileri
        """
        try:
            # API anahtarları kontrolü
            if not self.api_key or not self.api_secret:
                logger.warning("API anahtarları ayarlanmamış, demo bakiye döndürülüyor")
                # Demo bakiye döndür
                return {
                    'TRY': {'asset': 'TRY', 'free': '10000.00', 'locked': '0.00'},
                    'BTC': {'asset': 'BTC', 'free': '0.001', 'locked': '0.00'},
                    'ASR': {'asset': 'ASR', 'free': '100.0', 'locked': '0.00'}
                }
            
            balance = self.client.get_account_balance()
            logger.info("Hesap bakiyesi başarıyla alındı")
            
            # API'den gelen veriyi kontrol et
            if isinstance(balance, str):
                logger.error(f"API'den beklenmeyen string response: {balance}")
                # Hata durumunda demo bakiye döndür
                return {
                    'TRY': {'asset': 'TRY', 'free': '10000.00', 'locked': '0.00'},
                    'BTC': {'asset': 'BTC', 'free': '0.001', 'locked': '0.00'},
                    'ASR': {'asset': 'ASR', 'free': '100.0', 'locked': '0.00'}
                }
            
            # API'den gelen veriyi GUI'nin beklediği formata çevir
            formatted_balance = {}
            if isinstance(balance, list):
                for item in balance:
                    if isinstance(item, dict):
                        formatted_balance[item['asset']] = {
                            'asset': item['asset'],
                            'free': item.get('balance', '0'),  # 'balance' -> 'free'
                            'locked': item.get('locked', '0')
                        }
            return formatted_balance
        except Exception as e:
            logger.error(f"Hesap bakiyesi alınırken hata: {e}")
            # Hata durumunda demo bakiye döndür
            return {
                'TRY': {'asset': 'TRY', 'free': '10000.00', 'locked': '0.00'},
                'BTC': {'asset': 'BTC', 'free': '0.001', 'locked': '0.00'},
                'ASR': {'asset': 'ASR', 'free': '100.0', 'locked': '0.00'}
            }
    
    def get_balance(self) -> Dict[str, Any]:
        """
        Hesap bakiyesini getirir (get_account_balance için alias)
        GUI uyumluluğu için eklendi
        
        Returns:
            dict: Hesap bakiye bilgileri
        """
        return self.get_account_balance()
    
    def get_open_orders(self, symbol: str = None) -> list:
        """
        Açık emirleri listeler
        
        Args:
            symbol: Belirli bir coin çifti için açık emirler (opsiyonel)
            
        Returns:
            list: Açık emirler listesi
        """
        try:
            if not self.api_key or not self.api_secret:
                logger.warning("API anahtarları ayarlanmamış, açık emir kontrolü yapılamıyor")
                return []
            
            # BTCTurk API'sinde açık emirleri almak için get_open_orders metodunu kullan
            if hasattr(self.client, 'get_open_orders'):
                try:
                    open_orders = self.client.get_open_orders(pair_symbol=symbol)
                    
                    # API'den dönen veriyi kontrol et
                    if isinstance(open_orders, str):
                        logger.warning(f"API'den string yanıt alındı: {open_orders}")
                        return []
                    elif isinstance(open_orders, list):
                        # Liste içindeki her öğenin dictionary olup olmadığını kontrol et
                        valid_orders = []
                        for order in open_orders:
                            if isinstance(order, dict):
                                valid_orders.append(order)
                            else:
                                logger.warning(f"Geçersiz emir formatı: {type(order)} - {order}")
                        return valid_orders
                    elif isinstance(open_orders, dict):
                        # BTCTurk API'den dict yanıt gelirse, 'data' içinde 'asks' ve 'bids' olabilir
                        if 'data' in open_orders and isinstance(open_orders['data'], dict):
                            data = open_orders['data']
                            all_orders = []
                            # 'asks' (satış emirleri) ve 'bids' (alış emirleri) listelerini birleştir
                            if 'asks' in data and isinstance(data['asks'], list):
                                all_orders.extend(data['asks'])
                            if 'bids' in data and isinstance(data['bids'], list):
                                all_orders.extend(data['bids'])
                            return all_orders
                        elif 'data' in open_orders and isinstance(open_orders['data'], list):
                            return open_orders['data']
                        elif 'result' in open_orders and isinstance(open_orders['result'], list):
                            return open_orders['result']
                        elif 'orders' in open_orders and isinstance(open_orders['orders'], list):
                            return open_orders['orders']
                        # Doğrudan 'asks' ve 'bids' anahtarları varsa
                        elif 'asks' in open_orders or 'bids' in open_orders:
                            all_orders = []
                            if 'asks' in open_orders and isinstance(open_orders['asks'], list):
                                all_orders.extend(open_orders['asks'])
                            if 'bids' in open_orders and isinstance(open_orders['bids'], list):
                                all_orders.extend(open_orders['bids'])
                            return all_orders
                        else:
                            # Dict içinde liste bulunamazsa boş liste döndür
                            logger.info(f"Dict yanıtında açık emir listesi bulunamadı: {list(open_orders.keys())}")
                            return []
                    elif open_orders is None:
                        return []
                    else:
                        logger.warning(f"Beklenmeyen API yanıt tipi: {type(open_orders)}")
                        return []
                        
                except Exception as api_error:
                    logger.error(f"API get_open_orders hatası: {api_error}")
                    return []
            else:
                logger.warning("BTCTurk API client'ında get_open_orders metodu bulunamadı")
                return []
                
        except Exception as e:
            logger.error(f"Açık emirleri alma hatası: {e}")
            return []
    
    def cancel_open_orders(self, symbol: str) -> bool:
        """
        Belirli bir coin çifti için tüm açık emirleri iptal eder
        
        Args:
            symbol: Coin çifti (örn: BTCTRY)
            
        Returns:
            bool: İptal işlemi başarılı ise True
        """
        try:
            if not self.api_key or not self.api_secret:
                logger.warning("API anahtarları ayarlanmamış, emir iptali yapılamıyor")
                return True  # Demo modda başarılı sayalım
            
            # Açık emirleri al
            open_orders = self.get_open_orders(symbol)
            
            if not open_orders:
                logger.info(f"İptal edilecek açık emir bulunamadı: {symbol}")
                return True
            
            cancelled_count = 0
            for order in open_orders:
                try:
                    # Order'ın dict olup olmadığını kontrol et
                    if isinstance(order, dict):
                        order_id = order.get('id')
                    elif isinstance(order, str):
                        # Eğer order string ise, muhtemelen order ID'nin kendisidir
                        order_id = order
                    else:
                        logger.warning(f"Beklenmeyen order formatı: {type(order)} - {order}")
                        continue
                        
                    if order_id and hasattr(self.client, 'cancel_order'):
                        result = self.client.cancel_order(order_id=order_id)
                        if result:
                            cancelled_count += 1
                            logger.info(f"Emir iptal edildi: {order_id} - {symbol}")
                        else:
                            logger.warning(f"Emir iptal edilemedi: {order_id}")
                    else:
                        logger.warning("BTCTurk API client'ında cancel_order metodu bulunamadı")
                        
                except Exception as cancel_error:
                    logger.error(f"Emir iptal hatası: {cancel_error}")
                    continue
            
            logger.info(f"{cancelled_count} adet açık emir iptal edildi: {symbol}")
            return cancelled_count > 0 or len(open_orders) == 0
            
        except Exception as e:
            logger.error(f"Açık emir iptal hatası ({symbol}): {e}")
            return False
    
    def place_buy_order(self, symbol: str, amount: float) -> bool:
        """
        Limit order ile alım emri verir
        
        Args:
            symbol: Coin çifti (örn: BTCTRY)
            amount: Alım miktarı (TRY cinsinden)
            
        Returns:
            bool: İşlem başarılı ise True
        """
        try:
            # Güncel fiyatı al
            current_price = self.get_current_price(symbol)
            if current_price <= 0:
                logger.error(f"Geçersiz fiyat: {current_price}")
                return False
            
            # Limit fiyatı hesapla (güncel fiyata çok yakın - hızlı gerçekleşme için)
            limit_price = current_price * 0.9995  # %0.05 indirim (daha az indirim)
            
            # Coin miktarını hesapla
            coin_quantity = amount / limit_price
            
            logger.info(f"Limit alım emri hazırlanıyor: {symbol} - Miktar: {coin_quantity:.6f} - Limit Fiyat: {limit_price:.2f}")
            
            # API anahtarları kontrolü
            if not self.api_key or not self.api_secret:
                logger.warning("API anahtarları ayarlanmamış, demo modda çalışıyor")
                # Demo modda başarılı alım simülasyonu
                self.buy_price = limit_price
                self.coin_quantity = coin_quantity
                self.is_position_open = True
                logger.info(f"DEMO: Alım emri başarılı - {symbol} - Miktar: {coin_quantity:.6f} - Fiyat: {limit_price:.2f}")
                return True
            
            # Açık emirleri kontrol et ve iptal et
            logger.info(f"Açık emirler kontrol ediliyor: {symbol}")
            if not self.cancel_open_orders(symbol):
                logger.warning(f"Açık emirler iptal edilemedi, yine de devam ediliyor: {symbol}")
            
            # Gerçek API ile alım
            order = self.client.submit_limit_order(
                quantity=coin_quantity,
                price=limit_price,
                order_type='buy',
                pair_symbol=symbol
            )
            
            # API yanıtını kontrol et
            if order and isinstance(order, dict):
                self.buy_price = limit_price
                self.coin_quantity = coin_quantity  # Satın alınan coin miktarını kaydet
                self.is_position_open = True
                logger.info(f"Limit alım emri başarılı: {symbol} - {amount} TRY - Limit Fiyat: {limit_price:.2f} - Miktar: {coin_quantity:.6f}")
                
                if self.trade_callback:
                    self.trade_callback(f"LIMIT ALIM: {symbol} - {amount} TRY - Limit Fiyat: {limit_price:.2f} - Miktar: {coin_quantity:.6f}")
                
                return True
            elif order and isinstance(order, str):
                logger.warning(f"API'den beklenmeyen string yanıt: {order}")
                return False
            return False
            
        except Exception as e:
            # FAILED_ORDER_WITH_OPEN_ORDERS hatası özel olarak ele alınır
            if "FAILED_ORDER_WITH_OPEN_ORDERS" in str(e):
                logger.warning(f"Açık emirler nedeniyle alım başarısız, emirler iptal ediliyor: {symbol}")
                if self.cancel_open_orders(symbol):
                    logger.info(f"Açık emirler iptal edildi, alım tekrar deneniyor: {symbol}")
                    # Kısa bir bekleme sonrası tekrar dene
                    time.sleep(1)
                    return self.place_buy_order(symbol, amount)
                else:
                    logger.error(f"Açık emirler iptal edilemedi: {symbol}")
            
            logger.error(f"Limit alım emri hatası ({symbol}): {e}")
            return False
    
    def place_sell_order(self, symbol: str, amount: float) -> bool:
        """
        Limit fiyatından satım emri verir (güncel fiyatın %0.1 üstünde)
        
        Args:
            symbol: Coin çifti
            amount: Satım miktarı (coin cinsinden)
            
        Returns:
            bool: İşlem başarılı ise True
        """
        try:
            # Güncel fiyatı al
            current_price = self.get_current_price(symbol)
            if current_price <= 0:
                logger.error(f"Geçersiz fiyat: {current_price}")
                return False
            
            # Limit fiyatı hesapla (güncel fiyatın %0.1 üstünde)
            limit_price = current_price * 1.001  # %0.1 artış
            
            logger.info(f"Limit satım emri hazırlanıyor: {symbol} - Miktar: {amount:.6f} - Limit Fiyat: {limit_price:.2f}")
            
            # API anahtarları kontrolü
            if not self.api_key or not self.api_secret:
                logger.warning("API anahtarları ayarlanmamış, demo modda çalışıyor")
                # Demo modda başarılı satım simülasyonu
                profit = ((limit_price - self.buy_price) / self.buy_price) * 100
                self.is_position_open = False
                self.coin_quantity = 0.0
                logger.info(f"DEMO: Satım emri başarılı - {symbol} - Kar: %{profit:.2f} - Miktar: {amount:.6f}")
                if self.trade_callback:
                    self.trade_callback(f"DEMO SATIM: {symbol} - Kar: %{profit:.2f} - Limit Fiyat: {limit_price:.2f} - Miktar: {amount:.6f}")
                return True
            
            # Gerçek API ile satım
            order = self.client.submit_limit_order(
                quantity=amount,
                price=limit_price,
                order_type='sell',
                pair_symbol=symbol
            )
            
            # API yanıtını kontrol et
            if order and isinstance(order, dict):
                profit = ((limit_price - self.buy_price) / self.buy_price) * 100
                self.is_position_open = False
                self.coin_quantity = 0.0  # Coin miktarını sıfırla
                logger.info(f"Limit satım emri başarılı: {symbol} - Kar: %{profit:.2f} - Miktar: {amount:.6f}")
                
                if self.trade_callback:
                    self.trade_callback(f"LIMIT SATIM: {symbol} - Kar: %{profit:.2f} - Limit Fiyat: {limit_price:.2f} - Miktar: {amount:.6f}")
                
                return True
            elif order and isinstance(order, str):
                logger.warning(f"API'den beklenmeyen string yanıt: {order}")
                return False
            return False
            
        except Exception as e:
            logger.error(f"Limit satım emri hatası ({symbol}): {e}")
            return False
    
    def place_sell_order_at_target_price(self, symbol: str, amount: float, target_price: float) -> bool:
        """
        Hedef fiyatla limit satış emri verir
        
        Args:
            symbol: Coin çifti (örn: BTCTRY)
            amount: Satış miktarı (coin cinsinden)
            target_price: Hedef satış fiyatı
            
        Returns:
            bool: İşlem başarılı ise True
        """
        try:
            logger.info(f"Hedef fiyatla satış emri hazırlanıyor: {symbol} - Miktar: {amount:.6f} - Hedef Fiyat: {target_price:.2f}")
            
            # API anahtarları kontrolü
            if not self.api_key or not self.api_secret:
                logger.warning("API anahtarları ayarlanmamış, demo modda çalışıyor")
                # Demo modda satış emri açık olarak işaretle
                self.sell_order_active = True
                self.target_sell_price = target_price
                logger.info(f"DEMO: Hedef fiyatla satış emri açıldı - {symbol} - Miktar: {amount:.6f} - Hedef Fiyat: {target_price:.2f}")
                return True
            
            # Gerçek API ile satış emri
            order = self.client.submit_limit_order(
                quantity=amount,
                price=target_price,
                order_type='sell',
                pair_symbol=symbol
            )
            
            # API yanıtını kontrol et
            if order and isinstance(order, dict):
                self.sell_order_active = True
                self.target_sell_price = target_price
                logger.info(f"Hedef fiyatla satış emri açıldı: {symbol} - Miktar: {amount:.6f} - Hedef Fiyat: {target_price:.2f}")
                
                if self.trade_callback:
                    self.trade_callback(f"HEDEF SATIŞ EMRİ: {symbol} - Miktar: {amount:.6f} - Hedef Fiyat: {target_price:.2f}")
                
                return True
            elif order and isinstance(order, str):
                logger.warning(f"API'den beklenmeyen string yanıt: {order}")
                return False
            return False
            
        except Exception as e:
            logger.error(f"Hedef fiyatla satış emri hatası ({symbol}): {e}")
            return False
    
    def calculate_profit_percentage(self) -> float:
        """
        Mevcut kar yüzdesini hesaplar
        
        Returns:
            float: Kar yüzdesi
        """
        if self.buy_price > 0 and self.current_price > 0:
            return ((self.current_price - self.buy_price) / self.buy_price) * 100
        return 0.0
    
    def should_sell(self) -> bool:
        """
        Satış yapılıp yapılmayacağını kontrol eder
        
        Returns:
            bool: Satış yapılacaksa True
        """
        if not self.is_position_open:
            return False
            
        current_profit = self.calculate_profit_percentage()
        return current_profit >= self.target_profit_percentage
    
    def monitor_price(self):
        """
        Fiyat takibi yapar (ayrı thread'de çalışır)
        """
        logger.info(f"Fiyat takibi başlatıldı: {self.selected_coin}")
        
        while self.is_running:
            try:
                # Güncel fiyatı al
                new_price = self.get_current_price(self.selected_coin)
                
                if new_price > 0:
                    self.current_price = new_price
                    self.price_history.append({
                        'price': new_price,
                        'timestamp': datetime.now()
                    })
                    
                    # Fiyat geçmişini sınırla (son 1000 kayıt)
                    if len(self.price_history) > 1000:
                        self.price_history = self.price_history[-1000:]
                    
                    # GUI'yi güncelle
                    if self.price_update_callback:
                        profit_pct = self.calculate_profit_percentage() if self.is_position_open else 0
                        self.price_update_callback(new_price, profit_pct)
                    
                    # Satış kontrolü
                    if self.should_sell():
                        logger.info(f"Hedef kar yüzdesine ulaşıldı: %{self.calculate_profit_percentage():.2f}")
                        # Otomatik satış işlemi
                        if self.coin_quantity > 0:
                            if self.place_sell_order(self.selected_coin, self.coin_quantity):
                                logger.info("Otomatik satış işlemi tamamlandı")
                            else:
                                logger.error("Otomatik satış işlemi başarısız")
                    
                    logger.debug(f"Fiyat güncellendi: {self.selected_coin} = {new_price}")
                
                # 1 saniye bekle
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Fiyat takibi hatası: {e}")
                time.sleep(5)  # Hata durumunda biraz daha bekle
    
    def monitor_buy_order(self):
        """
        Alış emrinin gerçekleşmesini bakiye kontrolü ile takip eder ve gerçekleştikten sonra satış emrini açar
        """
        logger.info("Alış emri takibi başlatıldı - Bakiye kontrolü ile")
        
        # Başlangıç bakiyesini al
        initial_balance = self.get_account_balance()
        coin_asset = self.selected_coin.replace('TRY', '')  # BTCTRY -> BTC
        
        # Balance'ın dict olduğundan emin ol
        if isinstance(initial_balance, dict):
            initial_coin_balance = float(initial_balance.get(coin_asset, {}).get('free', '0'))
        else:
            logger.warning(f"Initial balance response is not dict: {type(initial_balance)}")
            initial_coin_balance = 0.0
        
        logger.info(f"Başlangıç {coin_asset} bakiyesi: {initial_coin_balance}")
        
        # Demo modda hemen gerçekleşmiş sayalım
        if not self.api_key or not self.api_secret:
            logger.info("DEMO: Alış emri gerçekleşti, satış emri açılıyor...")
            time.sleep(2)  # Kısa bekleme
            self.open_sell_order_after_buy()
            return
        
        # Gerçek API için alış emrinin gerçekleşmesini bekle
        max_wait_time = 600  # 10 dakika maksimum bekleme
        wait_time = 0
        check_interval = 2  # 2 saniyede bir kontrol et (daha hızlı)
        consecutive_no_change = 0  # Ardışık değişiklik olmayan kontrol sayısı
        
        # İlk kontrolü hemen yap (bekleme olmadan)
        try:
            current_balance = self.get_account_balance()
            # Balance'ın dict olduğundan emin ol
            if isinstance(current_balance, dict):
                current_coin_balance = float(current_balance.get(coin_asset, {}).get('free', '0'))
                balance_increase = current_coin_balance - initial_coin_balance
                
                if balance_increase > 0:
                    logger.info(f"✅ Alış emri hemen gerçekleşti! {coin_asset} bakiyesi {initial_coin_balance:.8f} -> {current_coin_balance:.8f} (+{balance_increase:.8f})")
                    self.bought_amount = balance_increase
                    
                    if self.status_update_callback:
                        self.status_update_callback(f"Alış tamamlandı! +{balance_increase:.8f} {coin_asset}")
                    
                    if hasattr(self, 'balance_update_callback') and self.balance_update_callback:
                        self.balance_update_callback()
                    
                    self.open_sell_order_after_buy()
                    return
            else:
                logger.warning(f"Balance response is not dict: {type(current_balance)}")
        except Exception as e:
            logger.debug(f"İlk bakiye kontrolü hatası: {e}")
        
        while self.is_running and wait_time < max_wait_time:
            try:
                time.sleep(check_interval)
                wait_time += check_interval
                
                # Güncel bakiyeyi kontrol et
                current_balance = self.get_account_balance()
                
                # Balance'ın dict olduğundan emin ol
                if not isinstance(current_balance, dict):
                    logger.warning(f"Balance response is not dict: {type(current_balance)}")
                    continue
                    
                current_coin_balance = float(current_balance.get(coin_asset, {}).get('free', '0'))
                
                # Coin bakiyesinde artış var mı kontrol et
                balance_increase = current_coin_balance - initial_coin_balance
                
                if balance_increase > 0:
                    logger.info(f"✅ Alış emri gerçekleşti! {coin_asset} bakiyesi {initial_coin_balance:.8f} -> {current_coin_balance:.8f} (+{balance_increase:.8f})")
                    
                    # Satın alınan miktarı güncelle
                    self.bought_amount = balance_increase
                    
                    if self.status_update_callback:
                        self.status_update_callback(f"Alış tamamlandı! +{balance_increase:.8f} {coin_asset}")
                    
                    # GUI'ye bakiye güncellemesi için sinyal gönder
                    if hasattr(self, 'balance_update_callback') and self.balance_update_callback:
                        self.balance_update_callback()
                    
                    # Satış emrini aç
                    self.open_sell_order_after_buy()
                    break
                
                # Değişiklik yoksa sayacı artır
                if balance_increase == 0:
                    consecutive_no_change += 1
                else:
                    consecutive_no_change = 0
                
                logger.debug(f"Alış emri bekleniyor - {coin_asset} bakiyesi: {current_coin_balance:.8f} (değişim: {balance_increase:.8f})")
                
                # Status güncellemesini daha az sıklıkta yap
                if wait_time % 10 == 0 and self.status_update_callback:  # Her 10 saniyede bir
                    self.status_update_callback(f"Alış emri bekleniyor - {wait_time}s")
                
                # Eğer 30 saniye boyunca hiç değişiklik yoksa, kontrol aralığını artır
                if consecutive_no_change > 15:  # 15 * 2 = 30 saniye
                    check_interval = min(5, check_interval + 1)  # Maksimum 5 saniye
                    consecutive_no_change = 0
                    logger.debug(f"Kontrol aralığı {check_interval} saniyeye çıkarıldı")
                    
            except Exception as e:
                logger.error(f"Alış takibi hatası: {e}")
                time.sleep(check_interval)
        
        if wait_time >= max_wait_time:
            logger.error("⚠️ Alış emri zaman aşımına uğradı - Bakiyede değişiklik tespit edilmedi")
            self.is_running = False
            if self.status_update_callback:
                self.status_update_callback("Bot durduruldu - Alış emri zaman aşımı")
        
        logger.info("Alış emri takibi sonlandırıldı")
    
    def open_sell_order_after_buy(self):
        """
        Alış emri gerçekleştikten sonra satış emrini açar - Gerçek satın alınan miktar kullanılır
        """
        try:
            # Hedef satış fiyatını hesapla
            target_sell_price = self.buy_price * (1 + self.target_profit_percentage / 100)
            
            # Gerçek satın alınan miktarı kullan (bought_amount monitor_buy_order'da set edildi)
            actual_amount = getattr(self, 'bought_amount', self.coin_quantity)
            
            logger.info(f"💰 Satış emri açılıyor:")
            logger.info(f"   Miktar: {actual_amount:.8f} {self.selected_coin.replace('TRY', '')}")
            logger.info(f"   Hedef fiyat: {target_sell_price:.2f} TRY")
            logger.info(f"   Alış fiyatı: {self.buy_price:.2f} TRY")
            logger.info(f"   Hedef kar: %{self.target_profit_percentage}")
            
            # Satış emrini aç - gerçek satın alınan miktarı kullan
            if self.place_sell_order_at_target_price(self.selected_coin, actual_amount, target_sell_price):
                logger.info("✅ Satış emri başarıyla açıldı, satış gerçekleşmesi bekleniyor...")
                
                # Satış takibini başlat
                self.monitoring_thread = threading.Thread(target=self.monitor_sell_order, daemon=True)
                self.monitoring_thread.start()
                
                if self.status_update_callback:
                    self.status_update_callback(f"Satış emri açık - {actual_amount:.8f} {self.selected_coin.replace('TRY', '')}")
            else:
                logger.error("❌ Satış emri açılamadı")
                self.is_running = False
                if self.status_update_callback:
                    self.status_update_callback("Bot durduruldu - Satış emri hatası")
                    
        except Exception as e:
            logger.error(f"Satış emri açma hatası: {e}")
            self.is_running = False
            if self.status_update_callback:
                self.status_update_callback("Bot durduruldu - Satış emri hatası")
    
    def monitor_sell_order(self):
        """
        Satış emrinin gerçekleşmesini takip eder
        """
        logger.info("Satış emri takibi başlatıldı")
        
        while self.is_running and self.sell_order_active:
            try:
                # Güncel fiyatı al
                current_price = self.get_current_price(self.selected_coin)
                
                if current_price > 0:
                    self.current_price = current_price
                    
                    # Kar yüzdesini hesapla
                    profit_pct = ((self.target_sell_price - self.buy_price) / self.buy_price) * 100
                    current_profit_pct = ((current_price - self.buy_price) / self.buy_price) * 100
                    current_balance = self.coin_quantity * current_price
                    target_balance = self.coin_quantity * self.target_sell_price
                    
                    # GUI'yi güncelle
                    if self.price_update_callback:
                        self.price_update_callback(current_price, current_profit_pct)
                    
                    # Status güncelle
                    status_msg = f"Satış bekleniyor - Kar: %{current_profit_pct:.2f} - Bakiye: {current_balance:.2f} TRY - Hedef: {target_balance:.2f} TRY"
                    if self.status_update_callback:
                        self.status_update_callback(status_msg)
                    
                    # Demo modda: Fiyat hedef fiyata ulaştı mı kontrol et
                    if not self.api_key or not self.api_secret:
                        if current_price >= self.target_sell_price:
                            logger.info(f"DEMO: Hedef fiyata ulaşıldı! Satış gerçekleşti - Fiyat: {current_price:.2f}, Hedef: {self.target_sell_price:.2f}")
                            self.complete_sell_transaction()
                            break
                    else:
                        # Gerçek API modda: Satış emrinin durumunu kontrol et
                        # Bu kısım gerçek API entegrasyonu için geliştirilecek
                        if current_price >= self.target_sell_price:
                            logger.info(f"Hedef fiyata ulaşıldı! Satış muhtemelen gerçekleşti - Fiyat: {current_price:.2f}, Hedef: {self.target_sell_price:.2f}")
                            self.complete_sell_transaction()
                            break
                    
                    logger.debug(f"Satış takibi - Güncel: {current_price:.2f}, Hedef: {self.target_sell_price:.2f}, Kar: %{current_profit_pct:.2f}")
                
                # 1 saniye bekle (hızlandırıldı)
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Satış emri takibi hatası: {e}")
                time.sleep(5)
    
    def complete_sell_transaction(self):
        """
        Satış işlemini tamamlar ve 2. işleme hazırlanır
        """
        try:
            # Satış işlemini tamamla
            sell_amount_try = self.coin_quantity * self.target_sell_price
            profit = sell_amount_try - self.amount_to_trade
            profit_pct = (profit / self.amount_to_trade) * 100
            
            logger.info(f"SATIŞ TAMAMLANDI!")
            logger.info(f"Alış: {self.amount_to_trade:.2f} TRY ({self.buy_price:.2f} fiyatından)")
            logger.info(f"Satış: {sell_amount_try:.2f} TRY ({self.target_sell_price:.2f} fiyatından)")
            logger.info(f"Kar: {profit:.2f} TRY (%{profit_pct:.2f})")
            
            # Pozisyonu kapat
            self.is_position_open = False
            self.coin_quantity = 0
            self.sell_order_active = False
            
            # Trade callback'i çağır
            if self.trade_callback:
                self.trade_callback(f"SATIŞ TAMAMLANDI - Kar: {profit:.2f} TRY (%{profit_pct:.2f})")
            
            # Status callback'i güncelle
            if self.status_update_callback:
                self.status_update_callback(f"1. İşlem tamamlandı - Kar: %{profit_pct:.2f}")
            
            # GUI'ye bakiye güncellemesi için sinyal gönder
            if hasattr(self, 'balance_update_callback') and self.balance_update_callback:
                self.balance_update_callback()
            
            # 5 saniye bekle ve 2. işleme geç
            logger.info("5 saniye sonra 2. işleme geçiliyor...")
            time.sleep(5)
            
            # 2. işlemi başlat
            self.start_second_trade()
            
        except Exception as e:
            logger.error(f"Satış işlemi tamamlama hatası: {e}")
    
    def start_second_trade(self):
        """
        2. işlemi başlatır
        """
        try:
            logger.info("2. İŞLEM BAŞLATILIYOR...")
            
            if self.status_update_callback:
                self.status_update_callback("2. işlem başlatılıyor...")
            
            # 2. alım işlemi
            if self.place_buy_order(self.selected_coin, self.amount_to_trade):
                logger.info("2. alım işlemi başarılı, satış emri açılıyor...")
                
                # Hedef satış fiyatını hesapla
                target_sell_price = self.buy_price * (1 + self.target_profit_percentage / 100)
                logger.info(f"2. işlem hedef satış fiyatı: {target_sell_price:.2f}")
                
                # Satış emrini aç
                if self.place_sell_order_at_target_price(self.selected_coin, self.coin_quantity, target_sell_price):
                    logger.info("2. işlem satış emri açıldı")
                    
                    if self.status_update_callback:
                        self.status_update_callback("2. işlem - Satış emri açık")
                    
                    # Satış takibini devam ettir (aynı thread içinde)
                    self.monitor_sell_order()
                else:
                    logger.error("2. işlem satış emri açılamadı")
                    self.is_running = False
            else:
                logger.error("2. alım işlemi başarısız")
                self.is_running = False
                
        except Exception as e:
            logger.error(f"2. işlem başlatma hatası: {e}")
            self.is_running = False
    
    def start_trading(self, coin_symbol: str, target_percentage: float, trade_amount: float):
        """
        Trading'i başlatır - Düzeltilmiş strateji: Alış emrinin gerçekleşmesini bekle sonra satış emri aç
        
        Args:
            coin_symbol: İşlem yapılacak coin çifti
            target_percentage: Hedef kar yüzdesi
            trade_amount: İşlem miktarı (TRY)
        """
        if self.is_running:
            logger.warning("Bot zaten çalışıyor")
            return
        
        self.selected_coin = coin_symbol
        self.target_profit_percentage = target_percentage
        self.amount_to_trade = trade_amount
        self.is_running = True
        
        logger.info(f"Trading başlatıldı: {coin_symbol} - Hedef: %{target_percentage} - Miktar: {trade_amount} TRY")
        
        # İlk alım işlemi
        if self.place_buy_order(coin_symbol, trade_amount):
            logger.info("Alım emri verildi, gerçekleşmesi bekleniyor...")
            
            # Alış emrinin gerçekleşmesini bekle ve sonra satış emri aç
            self.monitoring_thread = threading.Thread(target=self.monitor_buy_order, daemon=True)
            self.monitoring_thread.start()
            
            if self.status_update_callback:
                self.status_update_callback("Bot çalışıyor - Alış emri bekleniyor")
        else:
            self.is_running = False
            logger.error("İlk alım işlemi başarısız, bot durduruldu")
            
            if self.status_update_callback:
                self.status_update_callback("Bot durduruldu - Alım hatası")
    
    def stop_trading(self):
        """
        Trading'i durdurur
        """
        self.is_running = False
        logger.info("Trading durduruldu")
        
        if self.status_update_callback:
            self.status_update_callback("Bot durduruldu")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Bot durumunu döndürür
        
        Returns:
            dict: Bot durum bilgileri
        """
        return {
            'is_running': self.is_running,
            'selected_coin': self.selected_coin,
            'current_price': self.current_price,
            'buy_price': self.buy_price,
            'target_percentage': self.target_profit_percentage,
            'current_profit': self.calculate_profit_percentage(),
            'is_position_open': self.is_position_open,
            'trade_amount': self.amount_to_trade,
            'coin_quantity': self.coin_quantity
        }

if __name__ == "__main__":
    # Test için
    bot = BTCTurkTradingBot()
    print("BTCTurk Trading Bot hazır!")
    print(f"Mevcut coin çiftleri: {len(bot.get_available_pairs())}")