import os
import click
import unittest
from enter_app_name.app import create_app

# To change accordingly when running in dev/prod
app = create_app('testing')


@app.cli.command()
@click.option('--message', required=True)
def setup(message):
    """initial database setup"""
    pass


@app.cli.command()
def deploy():
    """Run deployment tasks."""
    pass


@app.cli.command()
def testing():
    tests = unittest.TestLoader().discover('tests')    # start directory
    unittest.TextTestRunner(verbosity=2).run(tests)