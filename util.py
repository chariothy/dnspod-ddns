from chariothy_common import AppTool
import os, sys, shutil, time


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def show_diff(src_path, dst_path):
    import difflib
    with open(src_path, mode='r') as fd:
        src_text = fd.readlines()
    
    with open(dst_path, mode='r') as fd:
        dst_text = fd.readlines()

    diff_list = list(difflib.Differ().compare(src_text, dst_text))
    for diff in diff_list:
        if diff == "\n":
            print ("\n")
        print(diff, end='', sep='')
    print()


def checkConfig():
    localConfig = './config/config_local.py'
    sampleConfig = localConfig.replace('_local', '_sample')        
    from config import CONFIG

    sys.path.append(os.path.join(os.getcwd(), 'config'))
    if not os.path.exists(sampleConfig):
        configVersion = ''
    else:
        from config_sample import CONFIG as CONFIG_SAMPLE
        configVersion = CONFIG_SAMPLE.get('version', 'NONE')
    
    if CONFIG['version'] != configVersion:
        if configVersion:
            print('#'* 20 + ' ↓ config_sample.py有版本更新，请注意其中的配置项差异 ({} <-> {}) ↓ '.format(configVersion, CONFIG['version']) + '#' * 20)
            show_diff(sampleConfig, './config.py')
            shutil.move(sampleConfig, sampleConfig.replace('_sample', f'_sample.v{configVersion}'))
            print('#'* 20 + ' ↑ config_sample.py有版本更新，请注意其中的配置项差异 ({} <-> {}) ↑ '.format(configVersion, CONFIG['version']) + '#' * 20)
            print()
            time.sleep(3)
        shutil.copyfile('./config.py', sampleConfig)
        os.chmod(sampleConfig, 0o777)

    if not os.path.exists(localConfig):
        print('\n未发现config_local.py文件，开始生成默认配置文件 ......')
        shutil.copyfile('./config.py', localConfig)
        os.chmod(localConfig, 0o777)
        print('\n默认config_local.py文件已经生成，请根据实际情况修改配置，并重新运行。')
        os.sys.exit()


checkConfig()

APP_NAME = 'dnspod'
APP = AppTool(APP_NAME, os.getcwd(), 'config')
CONFIG = APP.config
LOGGER = APP.logger