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

- Flask
- Flask-WTF
- Tailwind CSS CLI (for styling)

### Installing Tailwind CLI (v4.2.4)

Tailwind CLI v4.2.4 can be used without Node.js. Follow these steps:

1. **Follow the official documentations**:
   Visit [https://tailwindcss.com/docs/installation/tailwind-cli](https://tailwindcss.com/docs/installation/tailwind-cli) for detailed installation instructions.

2. **Verify installation**:
   ```bash
   tailwindcss --version
   ```

3. **Build CSS using provided scripts**:
   - For development (with watch mode): `./dev_build_tailwind.sh`
   - For production (minified): `./prod_build_tailwind.sh`

For detailed installation instructions, visit: [https://tailwindcss.com/docs/installation/tailwind-cli](https://tailwindcss.com/docs/installation/tailwind-cli)

## How to Run
 
```bash
# 1. Clone the repository
git clone https://github.com/yahya-sh/clarity_check
cd clarity_check
 
# 2. Install requirements
pip install -r requirements.txt

# 3. Or Run in (debug mode)
python main.py
 
# 4. Open in your browser
http://127.0.0.1:5000
```
 
---

## Project Checklist

- [x] It is available on GitHub.
- [x] It uses the Flask web framework.
- [x] It uses at least one module from the Python Standard
Library other than the random module.
Please provide the name of the module you are using in your
app.
- Module name: 
  - json
  - datetime
  - pathlib
  - hashlib
  - os
- [x] It contains at least one class written by you that has
both properties and methods. It uses `__init__()` to let the
class initialize the object's attributes (note that
`__init__()` doesn't count as a method). This includes
instantiating the class and using the methods in your app.
Please provide below the file name and the line number(s) of
at least one example of a class definition in your code as
well as the names of two properties and two methods.
- File name for the class definition: [models/user.py](models/user.py)
- Line number(s) for the class definition: [10](models/user.py#10)
- Name of two properties: 
  - [username](models/user.py#20)
  - [password_hash](models/user.py#21)
- Name of two methods: 
  - [check_password](models/user.py#29)
  - [to_dict](models/user.py#32)
- File name and line numbers where the methods are used: 
  - [services/auth_service.py:46](services/auth_service.py#46)
  - [repositories/users.py:32](repositories/users.py#32)
- [x] It makes use of JavaScript in the front end and uses the
localStorage of the web browser.
- [x] It uses modern JavaScript (for example, let and const
rather than var).
Examples:
  - const usage: [templates/session.html:65](templates/session.html#65) - `const metaTag = document.querySelector('meta[name=csrf-token]')`
  - let usage: [templates/join.html:75](templates/join.html#75) - `let debounceTimer = null`
  - Modern features: Arrow functions, template literals, async/await throughout templates
- [x] It makes use of the reading and writing to the same file
feature.
- [x] It contains conditional statements. Please provide below
the file name and the line number(s) of at least
one example of a conditional statement in your code.
  - File name: [routes/participant.py](routes/participant.py)
  - Line number(s): 
    - [25](routes/participant.py#25) - `if pin:`
    - [29](routes/participant.py#29) - `if not is_valid:`
    - [43](routes/participant.py#43) - `if not form.validate():`
- [x] It contains loops. Please provide below the file name
and the line number(s) of at least
one example of a loop in your code.
  - File name: [templates/base.html](templates/base.html)
  - Line number(s): 
    - [25](templates/base.html#25) - `{% for category, message in messages %}`
- [x] It lets the user enter a value in a text box at some
point.
This value is received and processed by your back end
Python code.
- [x] It doesn't generate any error message even if the user
enters a wrong input.
- [x] It is styled using your own CSS.
- [x] The code follows the code and style conventions as
introduced in the course, is fully documented using comments
and doesn't contain unused or experimental code.
In particular, the code should not use `print()` or
`console.log()` for any information the app user should see.
Instead, all user feedback needs to be visible in the
browser.
- [x] All exercises have been completed as per the
requirements and pushed to the respective GitHub repository.