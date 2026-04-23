# Clarity Check

## Turn every presentation into proof of understanding.

Most presentations end with smiles, nods, and polite applause.
But the real question is:

**Did the audience actually understand the message?**

That is where **Clarity Check** comes in.

**Clarity Check** helps presenters verify whether their audience truly understood the key objectives of the presentation.
At the end of the session, the audience answers a quick quiz through a link or QR code, and the presenter gets instant clarity on what landed — and what did not.

No guessing.
No assuming.
Just clear, measurable understanding.

Clarity Check transforms presentations from one-way delivery into real learning validation.

Don’t just present your message — prove it was understood.

## Prerequisites

Install Flask before running the app:
 
```bash
pip install flask
```
 
No other third-party packages are required. The following Python Standard Library modules are used and need no installation:
 
- `json` — reading and writing all data files
- `datetime` — timestamping quiz creation and session runs
- `uuid` — generating unique IDs for presentations, questions, sessions, and runs
- `hashlib` — hashing instructor passwords before storing
- `secrets` — generating cryptographically safe session tokens
- `os` — file path handling and directory creation
- `random` — generating 6-digit session PINs
---
 
## How to Run
 
```bash
# 1. Clone the repository
git clone https://github.com/yahya-sh/clarity_check
cd clarity_check
 
# 2. Install requirements
pip install -r requirements.txt
 
# 3. Run the app
flask run

# 4. Or Run in (debug mode)
python app.py
 
# 5. Open in your browser
http://127.0.0.1:5000
```
 
---

## Project Checklist

- [x] It is available on GitHub.
- [x] It uses the Flask web framework.
- [ ] It uses at least one module from the Python Standard
Library other than the random module.
Please provide the name of the module you are using in your
app.
- Module name:
- [ ] It contains at least one class written by you that has
both properties and methods. It uses `__init__()` to let the
class initialize the object's attributes (note that
`__init__()` doesn't count as a method). This includes
instantiating the class and using the methods in your app.
Please provide below the file name and the line number(s) of
at least one example of a class definition in your code as
well as the names of two properties and two methods.
- File name for the class definition:
- Line number(s) for the class definition:
- Name of two properties:
- Name of two methods:
- File name and line numbers where the methods are used:
- [ ] It makes use of JavaScript in the front end and uses the
localStorage of the web browser.
- [ ] It uses modern JavaScript (for example, let and const
rather than var).
- [ ] It makes use of the reading and writing to the same file
feature.
- [ ] It contains conditional statements. Please provide below
the file name and the line number(s) of at least
one example of a conditional statement in your code.
- File name:
- Line number(s):
- [ ] It contains loops. Please provide below the file name
and the line number(s) of at least
one example of a loop in your code.
- File name:
- Line number(s):
- [ ] It lets the user enter a value in a text box at some
point.
This value is received and processed by your back end
Python code.
- [ ] It doesn't generate any error message even if the user
enters a wrong input.
- [ ] It is styled using your own CSS.
- [ ] The code follows the code and style conventions as
introduced in the course, is fully documented using comments
and doesn't contain unused or experimental code.
In particular, the code should not use `print()` or
`console.log()` for any information the app user should see.
Instead, all user feedback needs to be visible in the
browser.
- [ ] All exercises have been completed as per the
requirements and pushed to the respective GitHub repository.