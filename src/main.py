# coding: UTF-8

import click
import os.path
import logging
import shutil


home = os.environ['HOME']
temp_dir = os.path.join(home, '.iris')


@click.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.option('--unity', '-u', default='/Applications/Unity/Unity.app')
def cmd(project_path, unity):
    if os.path.exists(os.path.join(project_path, 'Assets')):
        copy_unity_project(project_path)
        insert_builder_file()
    else:
        logging.error("specify unity project path")


def copy_unity_project(path):
    try:
        shutil.copytree(path, temp_dir)
    except OSError:
        shutil.rmtree(temp_dir)
        shutil.copytree(path, temp_dir)


def insert_builder_file():
    assets_dir = os.path.join(temp_dir, 'Assets')
    os.chdir(assets_dir)
    stream = open('IrisBuilder.cs', 'w')
    stream.writelines('using System.Linq;\n')
    stream.writelines('using UnityEngine;\n')
    stream.writelines('using UnityEditor;\n')
    stream.writelines('public class IrisBuilder{\n')
    stream.writelines('public static void BuildiOS(){\n')
    stream.writelines('BuildPipeLine.BuildPlayer(EditorBuildSettings.scenes,')
    stream.writelines('"Build/iOS", BuildTarget.iOS, BuildOptions.None);\n')
    stream.writelines('public static void BuildAndroid(){\n')
    stream.writelines('BuildPipeLine.BuildPlayer(EditorBuildSettings.scenes,')
    stream.writelines('"Build/Android", BuildTarget.Android,')
    stream.writelines('BuildOptions.AcceptExternalModificationsToPlayer);\n')
    stream.writelines('}\n')
    stream.writelines('}')
    stream.close


if __name__ == '__main__':
    cmd()
