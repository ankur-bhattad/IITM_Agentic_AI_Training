def get_ticket_price(age):
    # Check if age is less than 12
    if age < 12:
        price = 100
    
    # Check if age is between 12 and 59
    elif age <= 59:
        price = 200
    
    # Age 60 and above
    else:
        price = 150
    
    # Return the calculated ticket price
    return price


# Example usage
age = int(input("Enter person's age: "))
ticket_price = get_ticket_price(age)

print("Ticket Price: ₹", ticket_price)