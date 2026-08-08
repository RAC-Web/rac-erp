import datetime
from .models import Holiday

def is_working_day(target_date):
    """
    Returns True if target_date is not a Friday, Saturday, or a designated Holiday.
    """
    # 4 = Friday, 5 = Saturday in Python datetime (0 = Monday)
    if target_date.weekday() in [4, 5]:
        return False
        
    if Holiday.objects.filter(date=target_date).exists():
        return False
        
    return True

def get_working_days(start_date, end_date):
    """
    Returns a list of working dates between start_date and end_date (inclusive).
    """
    current_date = start_date
    working_days = []
    
    # Cache holidays in range to avoid multiple queries
    holidays = set(Holiday.objects.filter(date__range=[start_date, end_date]).values_list('date', flat=True))
    
    while current_date <= end_date:
        if current_date.weekday() not in [4, 5] and current_date not in holidays:
            working_days.append(current_date)
        current_date += datetime.timedelta(days=1)
        
    return working_days
