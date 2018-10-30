=====================
Reality monitor
=====================

Development
-----------

Prerequisite
````````````

* Python 3.5.2 (The version of Python we have on a Flo Device currently)
* pipenv: https://github.com/pypa/pipenv

Optional
::::::::

* pyenv: https://github.com/pyenv/pyenv

Setup
`````

1. Create a virtual environment using Python 3.5

.. code:: sh

    pipenv --python 3.5

2. Install all dependencies for the project (including dev):

.. code:: sh

    pipenv install -e .


Usage
-----

Installation
```````````

.. code:: sh

    pip install git+git://github.com/rondou/reality-monitor.git

or

.. code:: sh

    pipenv install 'git+ssh://git@github.com/rondou/reality-monitor.git#egg=reality-monitor'


Execute the code
```````````

Here is script.json content the key __meta__ is a magic key.

.. code:: json

    {
        "load": {
            "__meta__": {
                "type": "shell",
                "cmd": "echo \"[$(uptime | awk '{print $10}')]\"",
                "rtype": "json",
                "concurrent": true
            }
        }
    }

Run reality-monitor and specify json file.

.. code:: sh

    reality-monitor -p etc/script.json | jq .

You will get the follow result.

.. code:: json

    {
        "load": [2.44]
    }
