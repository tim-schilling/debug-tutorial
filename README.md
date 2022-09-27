# "It doesn't work" - A Djangonaut's Debugging Toolkit

Welcome to the tutorial! I really appreciate the time you've spent so far
and the time you spend in the future on this tutorial.

The purpose of this tutorial is to expose you to some of the tools
available to you as a Djangonaut to aid you in your debugging adventures.

## Preamble to the setup

This tutorial is written to give you the experience of working on a real
project. There are tests and adjacent functionality. The tests are written
so that they all pass for each lab, which means they confirm the bugs you
will be finding.

I suggest reviewing the [Project Overview page](docs/project_overview.md)
which has high level information on the models. It should make it easier
to understand the project.

Regarding debugging methods, a very useful one is to bisect commits or
find the last known good version, then compare what doesn't work. That
is very easy to do in this environment, but I strongly suggest that you
don't do that unless you're stuck.

## Getting Setup

This section will provide you with the minimal setup for this tutorial.
If you have a preference on setting up a project differently and know that
it works, go for it! Do what you're most comfortable.

1. Have Python 3.8+ installed. My assumption is that you have your own
   setup decided upon. However, if you're unsure where to go for
   this, I'd recommend using https://www.python.org/downloads/ for today.
1. From the terminal or command prompt, clone the project.
   ```shell
   git clone git@github.com:tim-schilling/debug-tutorial.git
   ```
   If you don't have a SSH key setup, you can use:
   ```shell
   git clone https://github.com/tim-schilling/debug-tutorial.git
   ```
   If you don't have git installed, you can
   [download the zip file](https://github.com/tim-schilling/debug-tutorial/archive/refs/heads/main.zip)
   and unpack it.
1. Change into project directory
   ```shell
   cd debug-tutorial
   ```
   If you downloaded the zip file, you'll need to ``cd`` to the location where
   you unpacked the archive.


---

### Windows warning

If you are comfortable on Windows with Python and have setup multiple projects, ignore this
warning. Do what's comfortable.

If not, I highly recommend using the Windows Subsystem for Linux
([docs](https://learn.microsoft.com/en-us/windows/wsl/about)). If you do, the
rest of the instructions will work for you. If you don't have access to that
please scroll down to [Windows non-WSL Setup](#windows-non-wsl-setup).

---

1. From the terminal, create a virtual environment. ([venv docs](https://docs.python.org/3/library/venv.html#venv-def))
   ```shell
   python -m venv venv
   ```
1. Active the virtual environment.
   ```shell
   source venv/bin/activate
   ```
1. Install the project dependencies.
   ```shell
   pip install -r requirements.txt
   ```
1. Create a new .env file.
   ```shell
   cp .env.dist .env
   ```
   If you use this for literally anything but this tutorial, please
   change the ``SECRET_KEY`` value in your ``.env`` file.
1. Create the database for the project.
   ```shell
   python manage.py migrate
   ```
1. Verify the tests currently pass, if they don't and you're not sure why,
   please ask.
   ```shell
   python manage.py test
   ```
1. Create the fake data. This will take a few minutes.
   ```shell
   python manage.py fake_data
   ```
1. Create your own super user account. Follow the prompts.
   ```shell
   python manage.py createsuperuser
   ```
1. Run the development web server.
   ```shell
   python manage.py runserver
   ```
1. Verify the following pages load:
   * http://127.0.0.1:8000/
   * http://127.0.0.1:8000/p/
   * http://127.0.0.1:8000/p/skill-fight-girl-north-production-thus-a-58113/
1. Log into the admin ([link](http://127.0.0.1:8000/admin/)) with your super user.
1. Verify the following pages load:
   * http://127.0.0.1:8000/post/create/
   * http://127.0.0.1:8000/analytics/

**BOOM!** You're done with the setup. Now that we've accomplished
the boring stuff, let's get to the dopamine rushes. I mean the bugs.

Proceed to [Lab 1](docs/lab1.md).


## Windows non-WSL Setup

1. From the command prompt, create a virtual environment.
   ```shell
   python3 -m venv venv
   ```
1. Activate the project
   ```shell
   .\venv\Scripts\activate
   ```
1. Install the project dependencies.
   ```shell
   pip install -r requirements.txt
   ```
1. Create a new .env file.
   ```shell
   copy .env.dist .env
   ```
   If you use this for literally anything but this tutorial, please
   change the ``SECRET_KEY`` value in your ``.env`` file.
1. Create the database for the project.
   ```shell
   python -m manage migrate
   ```
1. Verify the tests currently pass, if they don't and you're not sure why,
   please ask.
   ```shell
   python -m manage test
   ```
1. Create the fake data. This will take a few minutes.
   ```shell
   python -m manage fake_data
   ```
1. Create your own super user account. Follow the prompts.
   ```shell
   python -m manage createsuperuser
   ```
1. Run the development web server.
   ```shell
   python -m manage runserver
   ```
1. Verify the following pages load:
   * http://127.0.0.1:8000/
   * http://127.0.0.1:8000/p/
   * http://127.0.0.1:8000/p/skill-fight-girl-north-production-thus-a-58113/
1. Log into the admin ([link](http://127.0.0.1:8000/admin/)) with your super user.
1. Verify the following pages load:
   * http://127.0.0.1:8000/post/create/
   * http://127.0.0.1:8000/analytics/

Proceed to [Lab 1](docs/lab1.md).
