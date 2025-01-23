from datetime import datetime, timedelta, date

def convert_to_monday(user_date):
    # Garantir que a data seja um objeto datetime
    if isinstance(user_date, str):
        user_date = datetime.strptime(user_date, "%d/%m/%Y")
    
    # Encontrar a segunda-feira anterior ou igual
    days_for_monday = (user_date.weekday() - 0) % 7  # 0 representa segunda-feira
    previous_monday = user_date - timedelta(days=days_for_monday)
    return previous_monday



def is_the_date_in_seven_days(user_date):
    # Garantir que a data seja um objeto datetime
    today = date.today()
    

    next_week = today + timedelta(days=7)

    if user_date <= next_week:
        return True
    
    return False



if __name__ == '__main__':
    is_the_date_in_seven_days('2025-02-03')