"""
Simple To-Do List App using Gradio

This program demonstrates:
1. Menu-driven task operations
2. Task storage using Python list
3. Beginner-friendly structure
4. Interactive UI instead of terminal
"""

import gradio as gr

# ---------------------------------------------------
# GLOBAL TASK STORAGE
# ---------------------------------------------------
# Each task is stored as a dictionary:
# {"title": task_name, "completed": True/False}
tasks = []


# ---------------------------------------------------
# FUNCTION: View Tasks
# ---------------------------------------------------
def view_tasks():
    """Return formatted list of tasks."""

    # If no tasks exist
    if not tasks:
        return "📭 No tasks available."

    output = "### 📝 Your Tasks\n"

    # Loop through tasks and show status
    for i, task in enumerate(tasks, start=1):
        status = "✅ Completed" if task["completed"] else "❌ Pending"
        output += f"{i}. {task['title']} — {status}\n"

    return output


# ---------------------------------------------------
# FUNCTION: Add Task
# ---------------------------------------------------
def add_task(task_name):
    """Add a new task to the list."""

    # Remove extra spaces
    task_name = task_name.strip()

    if not task_name:
        return "⚠️ Task cannot be empty."

    # Add task dictionary into list
    tasks.append({
        "title": task_name,
        "completed": False
    })

    return f"✅ Task added: '{task_name}'"


# ---------------------------------------------------
# FUNCTION: Mark Task Completed
# ---------------------------------------------------
def complete_task(task_number):
    """Mark selected task as completed."""

    try:
        index = int(task_number) - 1
        tasks[index]["completed"] = True
        return f"🎉 Task '{tasks[index]['title']}' marked as completed."

    except:
        return "⚠️ Invalid task number."


# ---------------------------------------------------
# FUNCTION: Delete Task
# ---------------------------------------------------
def delete_task(task_number):
    """Delete selected task."""

    try:
        index = int(task_number) - 1
        removed = tasks.pop(index)
        return f"🗑️ Deleted task: '{removed['title']}'"

    except:
        return "⚠️ Invalid task number."


# ---------------------------------------------------
# GRADIO USER INTERFACE (MENU STYLE)
# ---------------------------------------------------
with gr.Blocks() as app:

    gr.Markdown("# ✅ Simple To-Do List App")
    gr.Markdown("### Choose an action below (Menu Driven Interface)")

    # ---- Add Task ----
    with gr.Row():
        task_input = gr.Textbox(label="Enter New Task")
        add_btn = gr.Button("1️⃣ Add Task")

    # ---- View Tasks ----
    view_btn = gr.Button("2️⃣ View Tasks")

    # ---- Complete Task ----
    complete_input = gr.Textbox(label="Task Number to Complete")
    complete_btn = gr.Button("3️⃣ Mark Completed")

    # ---- Delete Task ----
    delete_input = gr.Textbox(label="Task Number to Delete")
    delete_btn = gr.Button("4️⃣ Delete Task")

    # Output display area
    output = gr.Markdown()

    # ---------------------------------------------------
    # BUTTON ACTIONS (Menu Mapping)
    # ---------------------------------------------------
    add_btn.click(add_task, inputs=task_input, outputs=output)
    view_btn.click(view_tasks, outputs=output)
    complete_btn.click(complete_task,
                       inputs=complete_input,
                       outputs=output)
    delete_btn.click(delete_task,
                     inputs=delete_input,
                     outputs=output)


# ---------------------------------------------------
# RUN APPLICATION
# ---------------------------------------------------
app.launch()