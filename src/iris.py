# coding: UTF-8

import click
import os.path
import logging
import shutil
import subprocess


home = os.environ['HOME']
temp_dir = os.path.join(home, '.iris')


@click.command()
@click.option('--project_path', type=click.Path(exists=True))
@click.option('--platform', type=click.Path(exists=True))
@click.option('--unity_path', default='/Applications/Unity/Unity.app')
@click.option('--archive', type=click.Path(exists=True))
@click.option('--archive_option', type=click.Path(exists=True))
def cmd(project_path, platform, unity_path, archive):
    abs_project_path = convert_abs_path(project_path)

    if not os.path.exists(abs_project_path):
        logging.error("--project_path option must specify unity project path")
        return
    
    abs_unity_path = convert_abs_path(unity_path)
    if not os.path.exists(abs_unity_path):
        logging.error("--unity_path option is specify Unity.app path")
        return

    if not check_platform:
        logging.error('--platform option must iOS or Android')
        return

    copy_unity_project(project_path)
    insert_builder_file(project_path)
    export(unity, platform, abs_project_path)
    pod_install_if_needed(project_path)


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


def export(unity, platform, project_path):
    method = ''
    if platform == 'iOS':
        method = 'BuildiOS'
    else:
        method = 'BuildAndroid'

    command = os.path.join(unity, 'Contents/MacOS/Unity')
    arg1 = ' -quit -projectPath ' + temp_dir
    arg2 = ' -logFile ' + os.path.join(project_path, 'build.log')
    arg3 = ' -executeMethod IrisBuilder.' + method
    subprocess.check_call((command + arg1 + arg2 + arg2).split(' '))


def pod_install_if_needed(project_path):
    exported_path = os.path.join(project_path, 'Build/iOS')
    podfile_path = os.path.join(exported_path, 'Podfile')

    if not os.path.exists(podfile_path):
        return

    os.chdir(exported_path)
    pod_command = 'pod install'
    subprocess.check_call(pod_command.split(' '))


def convert_abs_path(target):
    if os.path.isabs(target):
        return target
    else:
        return os.path.abspath(target)


if __name__ == '__main__':
    cmd()
