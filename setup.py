from setuptools import setup, find_packages

setup(
    name = "django-dynamicforms",
    version = "1.0",
    url = 'http://github.com/gauravtech4u/django-dynamicforms',
    license = 'BSD',
    description = "An app that generates customizable dynamic forms",
    author = 'Gaurav Kapoor',
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    install_requires = ['setuptools'],

    classifiers = [
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
