# coding: UTF-8

import click
import os.path
import logging
import shutil
import subprocess
import toml


home = os.environ['HOME']
tempPath = os.path.join(home, '.iris')

ios = 'iOS'
android = 'Android'

xcodeproj = '.xcodeproj'
xcworkspace = '.xcworkspace'

provisioningKey = 'provisioning_profile_specifier'
codeSingIdentityKey = 'code_sign_identity'

@click.command()
@click.option('--projectPath', type=click.Path(exists=True), help='path to unity project')
@click.option('--platform', help='specify iOS or Android')
@click.option('--unityPath', default='/Applications/Unity/Unity.app', help='path to unity')
@click.option('--archive', is_flag=True, help='flag for iOS archive')
@click.option('--archivePath', type=click.Path(exists=True), help='path to .xcodeproj or .xcworkspace')
@click.option('--archiveOption', type=click.Path(exists=True), help='path to .toml')
def cmd(projectPath, platform, unityPath, archive, archivePath, archiveOption):
    if archive:
        archiveProject(archivePath, archiveOption)
    else:
        exportProject(projectPath, unityPath, platform)


def archiveProject(archivePath, archiveOption):
    absArchivePath = convertAbsPath(archivePath)
    projectName = os.path.basename(absArchivePath)
    name, ext = os.path.splitext(projectName)

    if not ext == xcodeproj and not ext == xcworkspace:
        logging.error('archivePath option must specify .xcworkspace or .xcodeproj')
        return

    absArchiveOption = convertAbsPath(archiveOption)
    optionMap = toml.load(open(absArchiveOption))

    targetOption = ''
    if ext == xcodeproj:
        targetOption = '-project' 
    else:
        targetOption = '-workspace'

    command = ['xcodebuild', 'archive']
    command.append(targetOption)
    command.append(absArchivePath)
    command.append('-sdk')
    command.append('iphoneos')
    command.append('-scheme')
    command.append('Unity-iPhone')
    command.append('-configuration')
    command.append('Release')
    command.append('-archivePath')
    dir = os.path.dirname(absArchivePath)
    xcarchivePath = os.path.join(dir, 'Build/Unity-iPhone.xcarchive') 
    command.append(xcarchivePath)
    codeSignIdentityCommand = 'CODE_SIGN_IDENTITY=' + optionMap[codeSingIdentityKey]
    command.append(codeSignIdentityCommand)
    command.append('PROVISIONING_PROFILE_SPECIFIER=' + optionMap[provisioningKey])
    subprocess.check_call(command)

    make_ipa(xcarchivePath, optionMap, dir)


def make_ipa(xcarchivePath, optionMap, base_dir):
    c = ['xcodebuild', '-exportArchive']
    c.append('-archivePath')
    c.append(xcarchivePath)
    c.append('-exportProvisioningProfile')
    c.append(optionMap[provisioningKey])
    c.append('-exportPath')
    c.append(os.path.join(base_dir, 'Build/Unity-iPhone.ipa'))
    subprocess.check_call(c)


def exportProject(projectPath, unityPath, platform):
    absProjectPath = convertAbsPath(projectPath)

    if not os.path.exists(absProjectPath):
        logging.error("--projectPath option must specify unity project path")
        return
    
    absUnityPath = convertAbsPath(unityPath)
    if not os.path.exists(absUnityPath):
        logging.error("--unityPath option is specify Unity.app path")
        return

    if not check_platform:
        logging.error('--platform option must iOS or Android')
        return

    copyUnityProject(absProjectPath)
    insertBuilderFile(absProjectPath)
    makeBuildDirIfNeeded(absProjectPath)
    doExport(unityPath, platform, absProjectPath)
    podInstallIfNeeded(absProjectPath, platform)


def copyUnityProject(path):
    try:
        shutil.copytree(path, tempPath)
    except OSError:
        shutil.rmtree(tempPath)
        isSymlink = True
        shutil.copytree(path, tempPath, isSymlink)


def check_platform(platform):
    if platform == ios:
        return True
    if platform == android:
        return True
    return False


def insertBuilderFile(projectPath):
    assets_dir = os.path.join(tempPath, 'Assets')
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
    stream.writelines(buildPath(projectPath, ios))
    stream.writelines('", BuildTarget.iOS, BuildOptions.None);\n')
    stream.writelines('}\n')
    stream.writelines('public static void BuildAndroid(){\n')
    stream.writelines('BuildPipeline.BuildPlayer(EditorBuildSettings.scenes, ')
    stream.writelines('"' + buildPath(projectPath, android) + '", BuildTarget.Android,')
    stream.writelines('BuildOptions.AcceptExternalModificationsToPlayer);\n')
    stream.writelines('}\n')
    stream.writelines('}')
    stream.close


def makeBuildDirIfNeeded(projectPath):
    build_dir = os.path.join(projectPath, 'Build')
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)

    if not os.path.exists(buildPath(projectPath, ios)):
        os.makedirs(buildPath(projectPath, ios))

    if not os.path.exists(buildPath(projectPath, android)):
        os.makedirs(buildPath(projectPath, android))


def doExport(unity, platform, projectPath):
    method = ''
    if platform == ios:
        method = 'BuildiOS'
    else:
        method = 'BuildAndroid'

    buildLogPath = os.path.join(projectPath, 'build.log')
    command = os.path.join(unity, 'Contents/MacOS/Unity')
    arg1 = ' -quit -projectPath ' + tempPath
    arg2 = ' -logFile ' + buildLogPath
    arg3 = ' -executeMethod IrisBuilder.' + method
    subprocess.check_call((command + arg1 + arg2 + arg3).split(' '))


def podInstallIfNeeded(projectPath, platform):
    if not platform == ios:
        return

    podfilePath = os.path.join(buildPath(projectPath, ios), 'Podfile')

    if not os.path.exists(podfilePath):
        return

    os.chdir(buildPath(projectPath, ios))
    podCommand = 'pod install'
    subprocess.check_call(podCommand.split(' '))


def convertAbsPath(target):
    if os.path.isabs(target):
        return target
    else:
        return os.path.abspath(target)


def buildPath(projectPath, platform):
    if platform == ios:
        return os.path.join(projectPath, 'Build/iOS')
    else:
        return os.path.join(projectPath, 'Build/Android')


if __name__ == '__main__':
    cmd()
