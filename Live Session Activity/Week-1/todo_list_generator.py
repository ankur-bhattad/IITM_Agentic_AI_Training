"""
Simple Terminal To-Do List Application

Features:
- Add new tasks
- View tasks
- Mark tasks as completed
- Delete tasks
- Runs continuously until user exits
"""

def display_menu() -> None:
    """Display application menu."""
    print("\n===== TO-DO LIST MENU =====")
    print("1. View Tasks")
    print("2. Add Task")
    print("3. Mark Task as Completed")
    print("4. Delete Task")
    print("5. Exit")


def view_tasks(tasks: list) -> None:
    """Display all tasks with status."""
    if not tasks:
        print("\nNo tasks available.")
        return

    print("\nYour Tasks:")
    for index, task in enumerate(tasks, start=1):
        status = "✅" if task["completed"] else "❌"
        print(f"{index}. [{status}] {task['title']}")


def add_task(tasks: list) -> None:
    """Add a new task."""
    title = input("Enter task description: ").strip()

    if title:
        tasks.append({"title": title, "completed": False})
        print("Task added successfully.")
    else:
        print("Task cannot be empty.")


def mark_completed(tasks: list) -> None:
    """Mark a selected task as completed."""
    view_tasks(tasks)

    if not tasks:
        return

    try:
        task_number = int(input("Enter task number to mark completed: "))
        tasks[task_number - 1]["completed"] = True
        print("Task marked as completed.")
    except (ValueError, IndexError):
        print("Invalid task number.")


def delete_task(tasks: list) -> None:
    """Delete a selected task."""
    view_tasks(tasks)

    if not tasks:
        return

    try:
        task_number = int(input("Enter task number to delete: "))
        removed = tasks.pop(task_number - 1)
        print(f"Deleted task: {removed['title']}")
    except (ValueError, IndexError):
        print("Invalid task number.")


def main() -> None:
    """Main program loop."""
    tasks = []

    while True:
        display_menu()
        choice = input("Choose an option (1-5): ").strip()

        if choice == "1":
            view_tasks(tasks)
        elif choice == "2":
            add_task(tasks)
        elif choice == "3":
            mark_completed(tasks)
        elif choice == "4":
            delete_task(tasks)
        elif choice == "5":
            print("Exiting To-Do App. Goodbye!")
            break
        else:
            print("Invalid choice. Please select 1–5.")


if __name__ == "__main__":
    main()