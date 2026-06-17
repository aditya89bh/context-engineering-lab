"""Test package.

Making ``tests`` a package lets test modules import shared, non-collected helpers
(such as ``tests.synthesis_helpers``) under a single, stable module name that both
pytest and mypy agree on.
"""
