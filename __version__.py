"""Version information for BTCTurk Trading Bot."""

__version__ = "1.0.0"
__version_info__ = (1, 0, 0)

# Version history
VERSION_HISTORY = {
    "1.0.0": {
        "date": "2025-01-08",
        "changes": [
            "İlk stabil sürüm",
            "GUI tabanlı trading bot",
            "Çoklu API anahtarı desteği",
            "Otomatik alış/satış sistemi",
            "Gerçek zamanlı bakiye takibi",
            "Kar/zarar hesaplama",
            "Detaylı loglama sistemi",
            "Hızlı alış emri algılama",
            "Thread-safe GUI güncellemeleri"
        ],
        "features": [
            "BTCTurk API entegrasyonu",
            "Demo ve gerçek mod desteği",
            "Dinamik fiyat takibi",
            "Otomatik stop-loss",
            "Çoklu coin desteği",
            "Güvenli API anahtar saklama",
            "Hata yönetimi ve recovery"
        ]
    }
}

def get_version():
    """Get current version string."""
    return __version__

def get_version_info():
    """Get version info tuple."""
    return __version_info__

def get_version_history():
    """Get complete version history."""
    return VERSION_HISTORY

def print_version_info():
    """Print detailed version information."""
    print(f"BTCTurk Trading Bot v{__version__}")
    print(f"Version Info: {__version_info__}")
    
    current_version = VERSION_HISTORY.get(__version__, {})
    if current_version:
        print(f"Release Date: {current_version.get('date', 'Unknown')}")
        print("\nFeatures:")
        for feature in current_version.get('features', []):
            print(f"  • {feature}")
        print("\nChanges:")
        for change in current_version.get('changes', []):
            print(f"  • {change}")

if __name__ == "__main__":
    print_version_info()