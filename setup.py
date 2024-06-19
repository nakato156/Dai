from setuptools import setup, find_packages

with open('README.md', encoding='utf-8') as f:
    readme = f.read()

setup(
    name='WDai',
    version='0.2',
    license='MIT',
    description='Herramienta para procesamiento distribuido de modelos de machine learning',
    long_description_content_type="text/markdown",
    long_description=readme,
    author='Nakato',
    author_email='christianvelasces@gmail.com',
    url='https://github.com/nakato156/dai',
    keywords=['distribution', 'ia', 'server', "workers", "package", "machine", "learning", "parallel"],
    packages=find_packages(),
)