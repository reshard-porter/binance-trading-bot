from datetime import datetime

def format_currency(value: float) -> str:
    """Formats float into a USD currency string"""
    return f"${value:,.2f}"

def format_percentage(value: float) -> str:
    """Formats float into a percentage string"""
    return f"{value:.2f}%"

def get_time_elapsed(start_time: datetime) -> str:
    """Calculates time elapsed since a given timestamp"""
    diff = datetime.utcnow() - start_time
    hours, remainder = divmod(diff.total_seconds(), 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{int(hours)}h {int(minutes)}m"