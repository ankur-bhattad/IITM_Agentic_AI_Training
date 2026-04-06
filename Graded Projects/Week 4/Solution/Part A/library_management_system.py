from collections import Counter
from typing import Dict, List


class Book:
    """
    Represents a book in the library.
    """

    def __init__(self, book_id: int, title: str, author: str, genre: str):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.genre = genre
        self.is_available = True  # True = Available, False = Issued

    def __repr__(self):
        status = "Available" if self.is_available else "Issued"
        return f"[{self.book_id}] {self.title} by {self.author} ({self.genre}) - {status}"


class Member:
    """
    Represents a library member.
    """

    def __init__(self, member_id: int, name: str, age: int, contact: str):
        self.member_id = member_id
        self.name = name
        self.age = age
        self.contact = contact
        self.borrowed_books: List[int] = []  # List of book IDs

    def __repr__(self):
        return f"[{self.member_id}] {self.name}, Age: {self.age}, Contact: {self.contact}"


class Library:
    """
    Main Library Management System.
    Handles books, members, borrowing, returning, and reporting.
    """

    def __init__(self):
        self.books: Dict[int, Book] = {}
        self.members: Dict[int, Member] = {}
        self.borrow_log: List[Dict] = []
        self.genre_counter = Counter()

    # ------------------ Book Management ------------------

    def add_book(self, book_id: int, title: str, author: str, genre: str):
        """Add a new book to the library."""
        print(f"Adding book ID {book_id}...")
        if book_id in self.books:
            print("❌ Book ID already exists.")
            return

        self.books[book_id] = Book(book_id, title, author, genre)
        print("✅ Book added successfully.")

    def search_books(self, keyword: str):
        """Search books by title or author."""
        print(f"Searching for books with keyword '{keyword}'...")
        return [
            book for book in self.books.values()
            if keyword.lower() in book.title.lower()
            or keyword.lower() in book.author.lower()
        ]

    def get_available_books_by_genre(self, genre: str):
        """Return all available books in a given genre."""
        print(f"Fetching available books in genre '{genre}'...")
        return [
            book for book in self.books.values()
            if book.genre.lower() == genre.lower() and book.is_available
        ]

    # ------------------ Member Management ------------------

    def add_member(self, member_id: int, name: str, age: int, contact: str):
        """Add a new member to the library."""
        print(f"Adding member ID {member_id}...")
        if member_id in self.members:
            print("❌ Member ID already exists.")
            return

        self.members[member_id] = Member(member_id, name, age, contact)
        print("✅ Member added successfully.")

    def get_members_with_borrowed_books(self):
        """Return list of members who have borrowed books."""
        print("Fetching members with borrowed books...")
        return [
            member for member in self.members.values()
            if member.borrowed_books
        ]

    # ------------------ Borrow & Return System ------------------

    def issue_book(self, member_id: int, book_id: int):
        """Issue a book to a member."""
        print(f"Issuing Book ID {book_id} to Member ID {member_id}...")

        if member_id not in self.members:
            print("❌ Invalid member ID.")
            return

        if book_id not in self.books:
            print("❌ Invalid book ID.")
            return

        book = self.books[book_id]
        member = self.members[member_id]

        if not book.is_available:
            print("❌ Book is already issued.")
            return

        print("Before Issue:", book, member.borrowed_books)

        book.is_available = False
        member.borrowed_books.append(book_id)

        self.borrow_log.append({
            "member_id": member_id,
            "book_id": book_id,
            "action": "borrow"
        })

        self.genre_counter[book.genre] += 1

        print("After Issue:", book, member.borrowed_books)
        print("✅ Book issued successfully.")

    def return_book(self, member_id: int, book_id: int):
        """Return a book from a member."""
        print(f"Returning Book ID {book_id} from Member ID {member_id}...")

        if member_id not in self.members:
            print("❌ Invalid member ID.")
            return

        if book_id not in self.books:
            print("❌ Invalid book ID.")
            return

        book = self.books[book_id]
        member = self.members[member_id]

        if book_id not in member.borrowed_books:
            print("❌ This member did not borrow this book.")
            return

        print("Before Return:", book, member.borrowed_books)

        book.is_available = True
        member.borrowed_books.remove(book_id)

        self.borrow_log.append({
            "member_id": member_id,
            "book_id": book_id,
            "action": "return"
        })

        print("After Return:", book, member.borrowed_books)
        print("✅ Book returned successfully.")

    # ------------------ Reports ------------------

    def get_most_popular_genre(self):
        """Return the most popular genre."""
        print("Calculating most popular genre...")
        if not self.genre_counter:
            return None
        return self.genre_counter.most_common(1)[0][0]


# ================== TEST FUNCTIONS ==================

def test_add_book():
    print("\n--- TEST: Add Book ---")
    library = Library()
    library.add_book(1, "Python Basics", "John Doe", "Programming")
    print(library.books)


def test_add_member():
    print("\n--- TEST: Add Member ---")
    library = Library()
    library.add_member(101, "Alice", 25, "email")
    print(library.members)


def test_issue_book():
    print("\n--- TEST: Issue Book ---")
    library = Library()

    library.add_book(1, "Python Basics", "John Doe", "Programming")
    library.add_member(101, "Alice", 25, "email")

    library.issue_book(101, 1)


def test_return_book():
    print("\n--- TEST: Return Book ---")
    library = Library()

    library.add_book(1, "Python Basics", "John Doe", "Programming")
    library.add_member(101, "Alice", 25, "email")
    library.issue_book(101, 1)

    library.return_book(101, 1)


def test_search_books():
    print("\n--- TEST: Search Books ---")
    library = Library()

    library.add_book(1, "Python Basics", "John Doe", "Programming")
    library.add_book(2, "Advanced Python", "Jane Smith", "Programming")

    results = library.search_books("Python")
    print(results)


def test_available_books_by_genre():
    print("\n--- TEST: Available Books by Genre ---")
    library = Library()

    library.add_book(1, "Python Basics", "John Doe", "Programming")
    library.add_book(2, "AI Book", "Jane", "AI")

    library.add_member(101, "Alice", 25, "email")
    library.issue_book(101, 1)

    print(library.get_available_books_by_genre("Programming"))


def test_members_with_borrowed_books():
    print("\n--- TEST: Members with Borrowed Books ---")
    library = Library()

    library.add_book(1, "Python", "John", "Programming")
    library.add_member(101, "Alice", 25, "email")

    library.issue_book(101, 1)

    print(library.get_members_with_borrowed_books())


def test_most_popular_genre():
    print("\n--- TEST: Most Popular Genre ---")
    library = Library()

    library.add_book(1, "Python", "John", "Programming")
    library.add_book(2, "AI", "Jane", "AI")

    library.add_member(101, "Alice", 25, "email")

    library.issue_book(101, 1)
    library.issue_book(101, 2)

    print(library.get_most_popular_genre())


# ================== RUN ALL TESTS ==================

if __name__ == "__main__":
    test_add_book()
    test_add_member()
    test_issue_book()
    test_return_book()
    test_search_books()
    test_available_books_by_genre()
    test_members_with_borrowed_books()
    test_most_popular_genre()