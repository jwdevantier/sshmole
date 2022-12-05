from setuptools import setup


def get_requirements():
    # intentionally naive, does not support include files etc
    with open("./requirements.txt") as fp:
        return fp.read().split()


setup(
    name="sshmole",
    packages=["sshmole", "sshmole.utils"],
    version="0.1.0",
    description="manager for sshuttle tunnelling tool",
    author="Jesper Wendel Devantier",
    url="https://github.com/jwdevantier/sshmole",
    license="MIT",
    install_requires=get_requirements(),
    options={"bdist_wheel": {"universal": True}},
    entry_points = {
        "console_scripts": [
            "sshmole=sshmole.__main__:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python",
    ]
)
