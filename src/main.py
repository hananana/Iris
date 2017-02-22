# coding: UTF-8

import click
import os.path
import logging
import shutil


@click.command()
@click.argument('project_path', type=click.Path(exists=True))
def cmd(project_path):
    if check_unity_project_path(project_path):
        copy_unity_project(project_path)
    else:
        logging.error("specify unity project path")


def check_unity_project_path(path):
    return os.path.exists(os.path.join(path, 'Assets'))


def copy_unity_project(path):
    home = os.environ['HOME']
    temp_dir = os.path.join(home, '.iris')
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)


if __name__ == '__main__':
    cmd()
