class UIManager:
    BANNER = " *ExpertNet SLH System - Active*"
    
    @staticmethod
    def welcome_msg(user_name):
        return f"ברוך הבא {user_name} ל-ExpertNet!\n\nבחר פעולה מהתפריט למטה:"

    @staticmethod
    def stats_msg(name, symbol, supply, balance):
        return (f" *נתוני חוזה:*\n"
                f"שם: {name}\n"
                f"סימול: {symbol}\n"
                f"סך היצע: {supply:,.2f}\n\n"
                f" *היתרה שלך:* {balance:,.2f} {symbol}")