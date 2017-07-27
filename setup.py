from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='courseraprogramming',
      version='0.20.0',
      description='A toolkit to help develop asynchronous graders for Coursera\
          based on docker images.',
      long_description=readme(),
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python :: 2.7',
      ],
      keywords='grading programming coursera sdk docker cli tool',
      url='https://github.com/coursera/courseraprogramming',
      author='Brennan Saeta',
      author_email='saeta@coursera.org',
      license='Apache',
      entry_points={
          'console_scripts': [
              'courseraprogramming = courseraprogramming.main:main',
          ],
      },
      packages=['courseraprogramming', 'courseraprogramming.commands'],
      install_requires=[
          'dockerfile-parse==0.0.6',
          'docker-py==1.10.4',
          'requests==2.9.2',
          'requests-toolbelt==0.7.1',
          'semver==2.7.5',
      ],
      test_suite='nose.collector',
      tests_require=['nose', 'nose-cover3'],
      include_package_data=True,
      zip_safe=False)
