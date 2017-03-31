# coding: UTF-8

import click
import os.path
import logging
import shutil
import subprocess


home = os.environ['HOME']
temp_path = os.path.join(home, '.iris')
ios = 'iOS'
android = 'Android'

@click.command()
@click.option('--project_path', type=click.Path(exists=True))
@click.option('--platform')
@click.option('--unity_path', default='/Applications/Unity/Unity.app')
@click.option('--archive', is_flag=True)
@click.option('--archive_path', type=click.Path(exists=True))
@click.option('--archive_option', type=click.Path(exists=True))
def cmd(project_path, platform, unity_path, archive, archive_path, archive_option):
    if archive:
        archive_project(archive_path, archive_option)
    else:
        export_project(project_path, unity_path, platform)


def archive_project(archive_path, archive_option):
    print(archive_path)
    print(archive_option)


def export_project(project_path, unity_path, platform):
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

    copy_unity_project(abs_project_path)
    insert_builder_file(abs_project_path)
    make_build_dir_if_needed(abs_project_path)
    do_export(unity_path, platform, abs_project_path)
    pod_install_if_needed(abs_project_path)



def copy_unity_project(path):
    try:
        shutil.copytree(path, temp_path)
    except OSError:
        shutil.rmtree(temp_path)
        is_symlink = True
        shutil.copytree(path, temp_path, is_symlink)


def check_platform(platform):
    if platform == ios:
        return True
    if platform == android:
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
    stream.writelines(build_path(project_path, ios))
    stream.writelines('", BuildTarget.iOS, BuildOptions.None);\n')
    stream.writelines('}\n')
    stream.writelines('public static void BuildAndroid(){\n')
    stream.writelines('BuildPipeline.BuildPlayer(EditorBuildSettings.scenes, ')
    stream.writelines('"' + build_path(project_path, android) + '", BuildTarget.Android,')
    stream.writelines('BuildOptions.AcceptExternalModificationsToPlayer);\n')
    stream.writelines('}\n')
    stream.writelines('}')
    stream.close


def make_build_dir_if_needed(project_path):
    build_dir = os.path.join(project_path, 'Build')
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)

    if not os.path.exists(build_path(project_path, ios)):
        os.makedirs(build_path(project_path, ios))

    if not os.path.exists(build_path(project_path, android)):
        os.makedirs(build_path(project_path, android))


def do_export(unity, platform, project_path):
    method = ''
    if platform == ios:
        method = 'BuildiOS'
    else:
        method = 'BuildAndroid'

    build_log_path = os.path.join(project_path, 'build.log')
    command = os.path.join(unity, 'Contents/MacOS/Unity')
    arg1 = ' -quit -projectPath ' + temp_path
    arg2 = ' -logFile ' + build_log_path
    arg3 = ' -executeMethod IrisBuilder.' + method
    subprocess.check_call((command + arg1 + arg2 + arg3).split(' '))


def pod_install_if_needed(project_path):
    podfile_path = os.path.join(build_path(project_path, ios), 'Podfile')

    if not os.path.exists(podfile_path):
        return

    os.chdir(build_path(project_path, ios))
    pod_command = 'pod install'
    subprocess.check_call(pod_command.split(' '))


def convert_abs_path(target):
    if os.path.isabs(target):
        return target
    else:
        ret = os.path.abspath(target)
        print(ret)
        return ret


def build_path(project_path, platform):
    if platform == ios:
        return os.path.join(project_path, 'Build/iOS')
    else:
        return os.path.join(project_path, 'Build/Android')


if __name__ == '__main__':
    cmd()
