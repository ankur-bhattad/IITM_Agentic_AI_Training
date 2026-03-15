from datetime import datetime
print('Rule-Based Chatbot initialized successfully!')

def get_time_of_day() -> str:
    """Determine time of day based on system clock."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return 'morning'
    elif 12 <= hour < 17:
        return 'afternoon'
    elif 17 <= hour <= 23:
        return 'evening'
    else:
        return 'night'

def get_greeting(time_of_day: str, gender: str) -> str:
    gender = gender.lower()
    if time_of_day == 'morning':
        return 'Good morning!' if gender not in ('male','female') else (
            'Good morning, sir! Ready to conquer the day?' if gender=='male' else 'Good morning, ma’am! Hope your day starts bright!')
    elif time_of_day == 'afternoon':
        return 'Good afternoon! Stay refreshed and focused.'
    elif time_of_day == 'evening':
        return 'Good evening! Relax and unwind.'
    else:
        return 'Hello there! Burning the midnight oil?'

def get_recommendation(age: int) -> str:
    if age < 13:
        return 'Don’t forget to finish your homework before playing!'
    elif 13 <= age < 20:
        return 'Focus on your studies, and remember to have fun learning!'
    elif 20 <= age < 40:
        return 'Work-life balance is key — take some time to relax.'
    elif 40 <= age < 60:
        return 'A short walk or some meditation could refresh your mind.'
    else:
        return 'Enjoy your day with positivity and gratitude!'

def get_motivation(time_of_day: str, age: int) -> str:
    if time_of_day == 'morning':
        return 'Each morning is a new chance to achieve something great!'
    elif time_of_day == 'afternoon':
        return 'Keep your energy up — every step counts!'
    elif time_of_day == 'evening':
        return 'Reflect on your wins today and rest well for tomorrow!'
    else:
        return 'Stay positive and keep smiling — good things take time!'


def chatbot():
    print('Welcome to The Friendly Assistant!')
    print('-----------------------------------')
    while True:
        name = input('Enter your name (or type exit to quit): ').strip()
        if name.lower() == 'exit':
            print('Goodbye! Have a wonderful day!')
            break

        try:
            age = int(input('Enter your age: '))
        except ValueError:
            print('Please enter a valid number for age.')
            continue

        gender = input('Enter your gender (male/female/other): ').strip()
        time_of_day = get_time_of_day()
        print(f'\nDetected time of day: {time_of_day.title()}')

        greeting = get_greeting(time_of_day, gender)
        recommendation = get_recommendation(age)
        motivation = get_motivation(time_of_day, age)

        print('\n--- The Friendly Assistant Says ---')
        print(f'{greeting}')
        print(f'{recommendation}')
        print(f'{motivation}')
        print('-----------------------------------\n')

        again = input('Would you like to chat again? (yes/no): ').strip().lower()
        if again != 'yes':
            print('Goodbye! Thanks for chatting!')
            break

if __name__ == "__main__":
    chatbot()