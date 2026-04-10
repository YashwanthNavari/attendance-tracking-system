import add_user

students = [
    ("student2", "pass", "student", "Alice Smith"),
    ("student3", "pass", "student", "Bob Jones"),
    ("student4", "pass", "student", "Carol White"),
    ("student5", "pass", "student", "David Brown"),
    ("student6", "pass", "student", "Eve Davis")
]

print("Adding dummy students...")
for username, password, role, full_name in students:
    add_user.add_user(username, password, role, full_name)

print("Done.")
