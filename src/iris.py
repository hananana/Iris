# coding: UTF-8

import click
import os.path
import logging
import shutil
import subprocess


home = os.environ['HOME']
temp_path = os.path.join(home, '.iris')

@click.command()
@click.option('--project_path', type=click.Path(exists=True))
@click.option('--platform')
@click.option('--unity_path', default='/Applications/Unity/Unity.app')
@click.option('--archive', type=click.Path(exists=True))
@click.option('--archive_option')
def cmd(project_path, platform, unity_path, archive, archive_option):
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
    insert_builder_file(project_path, platform)
    make_build_dir_if_needed(project_path)
    export(unity_path, platform, abs_project_path)
    pod_install_if_needed(project_path)


def copy_unity_project(path):
    try:
        shutil.copytree(path, temp_path)
    except OSError:
        shutil.rmtree(temp_path)
        is_symlink = True
        shutil.copytree(path, temp_path, is_symlink)


def check_platform(platform):
    if platform == 'iOS':
        return True
    if platform == 'Android':
        return True
    return False


def insert_builder_file(project_path):
    assets_dir = os.path.join(temp_path, 'Assets')
    editor_dir = os.path.join(assets_dir, 'Editor')
    os.makedirs(editor_dir)
    os.chdir(editor_dir)
    stream = open('IrisBuilder.cs', 'w')
    stream.writelines('using System.Linq;\n')
    stream.writelines('using UnityEngine;\n')
    stream.writelines('using UnityEditor;\n')
    stream.writelines('public class IrisBuilder{\n')
    stream.writelines('public static void BuildiOS(){\n')
    stream.writelines('BuildPipeline.BuildPlayer(EditorBuildSettings.scenes,"')
    stream.writelines(build_path(project_path, 'iOS'))
    stream.writelines('", BuildTarget.iOS, BuildOptions.None);\n')
    stream.writelines('}\n')
    stream.writelines('public static void BuildAndroid(){\n')
    stream.writelines('BuildPipeline.BuildPlayer(EditorBuildSettings.scenes, ')
    stream.writelines('"' + build_path(project_path, 'Android') + '", BuildTarget.Android,')
    stream.writelines('BuildOptions.AcceptExternalModificationsToPlayer);\n')
    stream.writelines('}\n')
    stream.writelines('}')
    stream.close


def make_build_dir_if_needed(project_path):
    build_dir = os.path.join(project_path, 'Build')
    if not os.path.exists(build_dir):
        os.mkdirs(build_dir)

    if not os.path.exists(build_path(project_path, 'iOS')):
        os.makedirs(build_path(project_path, 'iOS'))

    if not os.path.exists(build_path(project_path, 'Android')):
        os.makedirs(build_path(project_path, 'Android'))


def export(unity, platform, project_path):
    method = ''
    if platform == 'iOS':
        method = 'BuildiOS'
    else:
        method = 'BuildAndroid'

    command = os.path.join(unity, 'Contents/MacOS/Unity')
    arg1 = ' -quit -projectPath ' + temp_path
    arg2 = ' -logFile ' + os.path.join(project_path, 'build.log')
    arg3 = ' -executeMethod IrisBuilder.' + method
    subprocess.check_call((command + arg1 + arg2 + arg2).split(' '))


def pod_install_if_needed(project_path):
    podfile_path = os.path.join(build_path(project_path, 'iOS'), 'Podfile')

    if not os.path.exists(podfile_path):
        return

    os.chdir(build_path(project_path, 'iOS'))
    pod_command = 'pod install'
    subprocess.check_call(pod_command.split(' '))


def convert_abs_path(target):
    if os.path.isabs(target):
        return target
    else:
        return os.path.abspath(target)


def build_path(project_path, platform):
    pass


if __name__ == '__main__':
    cmd()
