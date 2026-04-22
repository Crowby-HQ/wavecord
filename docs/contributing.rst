Contributing
============

Thank you for wanting to contribute to WaveCord!

Setup
-----

.. code-block:: bash

   git clone https://github.com/Crowby-HQ/wavecord
   cd wavecord
   poetry install --with dev,lint,docs
   poetry run task pre-commit

Running Tests
-------------

.. code-block:: bash

   poetry run pytest tests/ -v

Linting & Type Checking
-----------------------

.. code-block:: bash

   poetry run task ruff       # lint
   poetry run task pyright    # type check

Building Docs Locally
---------------------

.. code-block:: bash

   poetry run task docs
   # Then open http://localhost:8069

Pull Requests
-------------

- Follow the existing code style (Ruff + Pyright strict).
- Add or update tests for any changed behaviour.
- Update the docstrings for any changed public API.
- Fill out the PR template.
