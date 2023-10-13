from setuptools import setup

setup(
    name='device_toolkit',
    python_requires='>3.8.0',
    version='0.2.4',
    description='Device control toolkit for Nvidia Jetson TX2 and Orin Nano',
    url='',
    author='wu.yushu',
    author_email='wu.yushu@',
    license='',
    packages=['device_toolkit'],
    install_requires=['sh'],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'Operating System :: POSIX :: Linux',        
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
    ],
    entry_points={
        'console_scripts': [
            'orinspec = device_toolkit:orinspec'
        ]
    }
)