"""
Thai ID Card Reader - ไฟล์ Setup สำหรับสร้าง .exe
=================================================
"""

from setuptools import setup

setup(
    name='ThaiIDReader',
    version='1.0.0',
    description='Thai ID Card Reader Desktop Application',
    author='thanakon-film60',
    py_modules=['thai_id_reader'],
    install_requires=[
        'flask>=2.0.0',
        'flask-cors>=3.0.0',
        'pyscard>=2.0.0',
    ],
    entry_points={
        'console_scripts': [
            'thaiidreader=thai_id_reader:main',
        ],
    },
)
