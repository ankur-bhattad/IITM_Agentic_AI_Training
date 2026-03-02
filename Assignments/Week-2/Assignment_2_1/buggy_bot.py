print("Welcome to BuggyBot! (type 'bye' to exit)")

while True:
    # Take input and make it case-insensitive
    user_input = input("You: ").lower().strip()

    # Greeting handling
    if user_input in ["hi", "hello"]:
        print("Bot: Hello there!")

    # Exit condition
    elif user_input == "bye":
        print("Bot: Goodbye!")
        break

    # Unknown input
    else:
        print("Bot: I don’t understand.")