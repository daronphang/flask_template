import coverage
import os
import unittest


def coverage_decorator(func):
    def _coverage_decorator(*args, **kwargs):
        COV = coverage.Coverage(branch=True, include='enter_app_name/app/*')
        COV.start()
        func(*args, **kwargs)
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()
        return
    return _coverage_decorator


@coverage_decorator
def run():
    tests = unittest.TestLoader().discover('enter_app_name/utest')
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':
    import logging
    from dotenv import load_dotenv

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    f_handler = logging.FileHandler('unit-test-cov.log')
    f_handler.setLevel(logging.DEBUG)
    f_formatter = logging.Formatter(
        '%(name)s - %(levelname)s - %(message)s'
    )
    f_handler.setFormatter(f_formatter)
    logger.addHandler(f_handler)
    logger.info('-' * 30)
    load_dotenv('.env.test')
    run()