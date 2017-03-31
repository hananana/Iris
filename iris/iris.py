# coding: UTF-8

import click
import os.path
import logging
import shutil
import subprocess


home = os.environ['HOME']
temp_dir = os.path.join(home, '.iris')


@click.command()
@click.argument('project_path', type=click.Path(exists=True))
@click.argument('platform')
@click.option('--unity', '-u', default='/Applications/Unity/Unity.app')
@click.option('--output', '-o', default='Build/iOS/')
@click.option('--pod/--no-pod', default=False)
def cmd(project_path, platform, unity, output, pod):
    if not check_platform:
        logging.error('platform must iOS or Android')
        return

    if os.path.exists(os.path.join(project_path, 'Assets')):
        copy_unity_project(project_path)
        insert_builder_file(project_path)
        export(unity, platform, pod)
        if pod:
            pod_install(project_path)
    else:
        logging.error("specify unity project path")


def copy_unity_project(path):
    try:
        shutil.copytree(path, temp_dir)
    except OSError:
        shutil.rmtree(temp_dir)
        isSymlink = True
        shutil.copytree(path, temp_dir, isSymlink)


def check_platform(platform):
    if platform == 'iOS':
        return True
    if platform == 'Android':
        return True
    return False


def insert_builder_file(project_path):
    assets_dir = os.path.join(temp_dir, 'Assets')
    editor_dir = os.path.join(assets_dir, 'Editor')
    os.makedirs(editor_dir)
    os.chdir(editor_dir)
    ios_build_path = os.path.join(project_path, 'Build/iOS')
    android_build_path = os.path.join(project_path, 'Build/Android')
    stream = open('IrisBuilder.cs', 'w')
    stream.writelines('using System.Linq;\n')
    stream.writelines('using UnityEngine;\n')
    stream.writelines('using UnityEditor;\n')
    stream.writelines('public class IrisBuilder{\n')
    stream.writelines('public static void BuildiOS(){\n')
    stream.writelines('BuildPipeline.BuildPlayer(EditorBuildSettings.scenes,"')
    stream.writelines(ios_build_path)
    stream.writelines('", BuildTarget.iOS, BuildOptions.None);\n')
    stream.writelines('}\n')
    stream.writelines('public static void BuildAndroid(){\n')
    stream.writelines('BuildPipeline.BuildPlayer(EditorBuildSettings.scenes, ')
    stream.writelines('"' + android_build_path + '", BuildTarget.Android,')
    stream.writelines('BuildOptions.AcceptExternalModificationsToPlayer);\n')
    stream.writelines('}\n')
    stream.writelines('}')
    stream.close


def export(unity, platform, pod):
    method = ''
    if platform == 'iOS':
        method = 'BuildiOS'
    else:
        method = 'BuildAndroid'

    command = os.path.join(unity, 'Contents/MacOS/Unity')
    arg1 = ' -quit -projectPath ' + temp_dir
    arg2 = ' -executeMethod IrisBuilder.' + method
    subprocess.check_call((command + arg1 + arg2).split(' '))


def pod_install(project_path):
    os.chdir(os.path.join(project_path, 'Build/iOS'))
    pod_command = 'pod install'
    subprocess.check_call(pod_command.split(' '))


if __name__ == '__main__':
    cmd()
