#!/usr/bin/env python

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib

COLLCTD_SOURCE_URL = "https://github.com/maplelabs/collectd/releases/download/" \
                     "collectd-custom-5.6.1/collectd-custom-5.6.1.tar.bz2"
# collectd_source_url = "https://github.com/upendrasahu/collectd/releases/download/" \
#                       "collectd-custom-5.6.1/collectd-custom-5.6.1.tar.bz2"
COLLCTD_SOURCE_FILE = "collectd-custom-5.6.1"

# configurator_source_url = "http://10.81.1.134:8000/configurator.tar.gz"
CONFIGURATOR_SOURCE_REPO = "https://github.com/maplelabs/configurator-exporter"
CONFIGURATOR_DIR = "/opt/configurator-exporter"
# collectd_plugins_source_url = "http://10.81.1.134:8000/plugins.tar.gz"
COLLECTD_PLUGINS_REPO = "https://github.com/maplelabs/collectd-plugins"
COLLECTD_PLUGINS_DIR = "/opt/collectd/plugins"

# check output function for python 2.6
if "check_output" not in dir(subprocess):
    def f(*popenargs, **kwargs):
        if 'stdout' in kwargs:
            raise ValueError('stdout argument not allowed, it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd)
        return output


    subprocess.check_output = f


def run_cmd(cmd, shell, ignore_err=False, print_output=False):
    """
    return output and status after runing a shell command 
    :param cmd: 
    :param shell: 
    :param ignore_err: 
    :param print_output: 
    :return: 
    """
    try:
        output = subprocess.check_output(cmd, shell=shell)
        if print_output:
            print output
            return output
    except subprocess.CalledProcessError as error:
        print >> sys.stderr, "Error: {0}".format(error)
        if not ignore_err:
            sys.exit(1)
        print "error ignored"
        return


def run_call(cmd, shell):
    """
    run a command don't check output
    :param cmd: 
    :param shell: 
    :return: 
    """
    try:
        subprocess.call(cmd, shell=shell)
    except subprocess.CalledProcessError as error:
        print >> sys.stderr, "Error: {0}".format(error)
        print "error ignored"
        return


def download_and_extract_tar(tarfile_url, local_file_name, tarfile_type=None, extract_dir=None):
    if extract_dir is None:
        extract_dir = '/tmp'
    if tarfile_type is None:
        tarfile_type = "r:gz"
    try:
        urllib.urlretrieve(tarfile_url, local_file_name)
    except IOError as err:
        print >> sys.stderr, err

    print "untar " + local_file_name
    try:
        tar = tarfile.open(local_file_name, tarfile_type)
        tar.extractall(extract_dir)
        tar.close()
    except tarfile.TarError as err:
        print >> sys.stderr, err


def clone_git_repo(REPO_URL, LOCAL_DIR):
    command = "git clone {0} {1}".format(REPO_URL, LOCAL_DIR)
    print command
    run_call(command, shell=True)


def install_dev_tools():
    """
    install development tools and dependencies required to compile collectd
    :return: 
    """
    if platform.dist()[0].lower() == "ubuntu" or platform.dist()[0].lower() == "debian":
        print "found ubuntu installing development tools and dependencies..."
        cmd1 = "apt-get update -y"
        cmd2 = "apt-get install -y pkg-config build-essential libpthread-stubs0-dev curl " \
              "zlib1g-dev python-dev python-pip libcurl4-openssl-dev libvirt-dev sudo libmysqlclient-dev git"
        run_cmd(cmd1, shell=True)
        run_cmd(cmd2, shell=True)

    elif platform.dist()[0].lower() == "centos" or platform.dist()[0].lower() == "redhat":
        print "found centos/redhat installing developments tools and dependencies..."
        # cmd1 = "yum groupinstall -y 'Development Tools'"
        cmd1 = "yum -y install libcurl libcurl-devel rrdtool rrdtool-devel rrdtool-prel libgcrypt-devel gcc make gcc-c++"
        cmd2 = "yum install -y curl python-devel libcurl libvirt-devel perl-ExtUtils-Embed sudo mysql-devel git"
        cmd3 = "yum update -y"
        run_cmd(cmd3, shell=True)
        run_cmd(cmd1, shell=True)
        run_cmd(cmd2, shell=True)


# def install_pip():
#     """
#     install latest version of pip
#     :return:
#     """
#     output = run_cmd("pip -V", shell=True, print_output=True)
#     try:
#         if output.split(" ")[1] == "9.0.1":
#             return
#         else:
#             print "install latest version of pip"
#             pip_install_url = "https://bootstrap.pypa.io/get-pip.py"
#             try:
#                 urllib.urlretrieve(pip_install_url, "/tmp/get-pip.py")
#             except IOError as err:
#                 print >> sys.stderr, err
#             run_cmd("python /tmp/get-pip.py", shell=True)
#     except Exception as err:
#         print >> sys.stderr, err

def install_pip():
    print "install latest version of pip"
    pip_install_url = "https://bootstrap.pypa.io/get-pip.py"
    try:
        urllib.urlretrieve(pip_install_url, "/tmp/get-pip.py")
    except IOError as err:
        print >> sys.stderr, err
    run_cmd("python /tmp/get-pip.py", shell=True)


def install_python_packages():
    """
    install required python packages
    :return: 
    """
    print "install python packages using pip"
    cmd2 = "pip install --upgrade setuptools libvirt-python==2.0.0 collectd psutil argparse pyyaml mako"
    run_cmd(cmd2, shell=True)


def setup_collectd():
    """
    install a custoum collectd from source
    :return: 
    """
    # download and extract collectd
    print "downloading collectd..."
    download_and_extract_tar(COLLCTD_SOURCE_URL, "/tmp/{0}.tar.bz2".format(COLLCTD_SOURCE_FILE), tarfile_type="r:bz2")

    try:
        shutil.rmtree("/opt/collectd", ignore_errors=True)
    except shutil.Error:
        pass

    print "setup collectd..."
    if os.path.isdir("/tmp/{0}".format(COLLCTD_SOURCE_FILE)):
        cmd = "cd /tmp/{0} && ./configure && make all install".format(COLLCTD_SOURCE_FILE)
        run_cmd(cmd, shell=True)
        try:
            shutil.copyfile("/tmp/{0}/src/my_types.db".format(COLLCTD_SOURCE_FILE), "/opt/collectd/my_types.db")
        except Exception as err:
            print err


def create_collectd_service():
    """
    create a service for collectd installed 
    :return: 
    """
    if platform.dist()[0].lower() == "ubuntu":
        print "found ubuntu ..."
        version = platform.dist()[1]
        print "ubuntu version: {0}".format(version)
        if version < "16.04":
            try:
                shutil.copyfile("/tmp/{0}/init_scripts/ubuntu14.init".format(COLLCTD_SOURCE_FILE),
                                "/etc/init.d/collectd")
            except shutil.Error as err:
                print >> sys.stderr, err
            run_cmd("chmod +x /etc/init.d/collectd", shell=True)
        else:
            try:
                shutil.copyfile("/tmp/{0}/init_scripts/ubuntu16.init".format(COLLCTD_SOURCE_FILE),
                                "/etc/systemd/system/collectd.service")
            except shutil.Error as err:
                print >> sys.stderr, err
            run_cmd("systemctl daemon-reload", shell=True, ignore_err=True)

    elif platform.dist()[0].lower() == "centos":
        print "found centos ..."
        version = platform.dist()[1]
        print "centos version: {0}".format(version)
        if version < "7.0":
            try:
                shutil.copyfile("/tmp/{0}/init_scripts/centos6.init".format(COLLCTD_SOURCE_FILE),
                                "/etc/init.d/collectd")
            except shutil.Error as err:
                print >> sys.stderr, err
            run_cmd("chmod +x /etc/init.d/collectd", shell=True)
        else:
            try:
                shutil.copyfile("/tmp/{0}/init_scripts/centos7.init".format(COLLCTD_SOURCE_FILE),
                                "/etc/systemd/system/collectd.service")
            except shutil.Error as err:
                print >> sys.stderr, err
            run_cmd("systemctl daemon-reload", shell=True, ignore_err=True)

    print "terminate any old instance of collectd if available"
    run_cmd("kill $(ps aux | grep -v grep | grep 'collectd' | awk '{print $2}')", shell=True, ignore_err=True)
    print "start collectd ..."
    # run_cmd("systemctl daemon-reload", shell=True, ignore_err=True)
    run_cmd("service collectd start", shell=True, print_output=True)
    run_cmd("service collectd status", shell=True, print_output=True)


def install_fluentd():
    """
    install fluentd and start the service 
    :return: 
    """

    distro, version, name = platform.dist()

    if distro.lower() == "ubuntu":
        print "install fluentd for ubuntu {0} {1}".format(version, name)
        fluentd_install_url_ubuntu = "https://toolbelt.treasuredata.com/sh/install-ubuntu-{0}-td-agent2.sh"
        urllib.urlretrieve(fluentd_install_url_ubuntu.format(name), "/tmp/install-ubuntu-{0}-td-agent2.sh".format(name))
        run_cmd("sh /tmp/install-ubuntu-{0}-td-agent2.sh".format(name), shell=True)

    elif distro.lower() == "centos":
        print "install fluentd for centos/redhat {0} {1}".format(version, name)
        fluentd_install_url_centos = "https://toolbelt.treasuredata.com/sh/install-redhat-td-agent2.sh"
        urllib.urlretrieve(fluentd_install_url_centos, "/tmp/install-redhat-td-agent2.sh")
        run_cmd("sh /tmp/install-redhat-td-agent2.sh", shell=True)

    print "start fluentd ..."
    run_cmd("/usr/sbin/td-agent-gem install fluent-plugin-elasticsearch", shell=True)
    run_cmd("/usr/sbin/td-agent-gem install fluent-plugin-kafka", shell=True)
    run_cmd("/etc/init.d/td-agent start", shell=True)
    run_cmd("/etc/init.d/td-agent status", shell=True, print_output=True)


def add_collectd_plugins():
    """
    add plugins to collectd installed 
    :return: 
    """
    # download_and_extract_tar(collectd_plugins_source_url, "/tmp/plugins.tar.gz")
    clone_git_repo(COLLECTD_PLUGINS_REPO, COLLECTD_PLUGINS_DIR)
    # try:
    #     shutil.copytree("/tmp/plugins", "/opt/collectd/plugins")
    # except shutil.Error as err:
    #     print >> sys.stderr, err
    if os.path.isfile("{0}/requirements.txt".format(COLLECTD_PLUGINS_DIR)):
        cmd = "pip install -r {0}/requirements.txt".format(COLLECTD_PLUGINS_DIR)
        run_cmd(cmd, shell=True, ignore_err=True)
    try:
        shutil.move("{0}/collectd.conf".format(COLLECTD_PLUGINS_DIR), "/opt/collectd/etc/collectd.conf")
    except shutil.Error as err:
        print >> sys.stderr, err

    if not os.path.isfile("/opt/collectd/my_types.db"):
        try:
            shutil.move("{0}/my_types.db".format(COLLECTD_PLUGINS_DIR), "/opt/collectd/my_types.db")
        except shutil.Error as err:
            print err

    # run_cmd("service collectd restart", shell=True)


def install_configurator(host, port):
    """
    install and start configurator
    :return: 
    """
    # kill existing configurator service

    run_cmd("kill $(ps -face | grep -v grep | grep 'api_server' | awk '{print $2}')", shell=True, ignore_err=True)
    if os.path.isdir(CONFIGURATOR_DIR):
        shutil.rmtree(CONFIGURATOR_DIR, ignore_errors=True)
    print "downloading configurator..."
    # download_and_extract_tar(configurator_source_url, "/tmp/configurator.tar.gz", extract_dir="/opt")
    clone_git_repo(CONFIGURATOR_SOURCE_REPO, CONFIGURATOR_DIR)
    print "setup configurator..."
    if os.path.isdir(CONFIGURATOR_DIR):
        cmd1 = "pip install --upgrade web.py mako"
        run_cmd(cmd1, shell=True)
        print "starting configurator ..."
        # run_cmd("kill $(ps -face | grep -v grep | grep 'api_server' | awk '{print $2}')", shell=True, ignore_err=True)
        # cmd2 = "cd " + CONFIGURATOR_DIR
        # cmd2 += " && python api_server.py -i {0} -p {1} > /dev/null 2>&1 & disown".format(host, port)
        cmd2 = "sudo nohup python {0}/api_server.py -i {1} -p {2} </dev/null >/dev/null 2>&1 &".format(CONFIGURATOR_DIR, host, port)
        print cmd2
        run_call(cmd2, shell=True)


if __name__ == '__main__':
    """main function"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-sc', '--skipcollectd', action='store_false', default=True, dest='installcollectd',
                        help='skip collectd installation')
    parser.add_argument('-sf', '--skipfluentd', action='store_false', default=True, dest='installfluentd',
                        help='skip fluentd installation')
    parser.add_argument('-p', '--port', action='store', default="8000", dest='port',
                        help='port on which configurator will listen')
    parser.add_argument('-ip', '--host', action='store', default="0.0.0.0", dest='host',
                        help='host ip on which configurator will listen')
    args = parser.parse_args()

    if not args.installcollectd and not args.installfluentd:
        print >> sys.stderr, "you cannot skip both collectd and fluentd installation"
        sys.exit(128)

    install_dev_tools()
    install_pip()

    if args.installcollectd:
        print "Started installing collectd ..."
        install_python_packages()
        setup_collectd()
        add_collectd_plugins()
        create_collectd_service()
    if args.installfluentd:
        print "started installing fluentd ..."
        install_fluentd()

    print "started installing configurator ..."
    install_configurator(host=args.host, port=args.port)

    sys.exit(0)
