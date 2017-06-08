#!/usr/bin/env python

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tarfile
from time import sleep

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


def _add_proxy_for_curl_in_file(proxy, file_name):
    cmd = 'sed -i "s|curl|curl -x {0}|g" {1}'.format(proxy, file_name)
    print cmd
    run_cmd(cmd, shell=True, ignore_err=True)


def _add_proxy_for_rpm_in_file(proxy, file_name):
    proxy_url = str(proxy).replace('http://', '')
    proxy_url = str(proxy_url).replace('https://', '')
    proxy_url = proxy_url.split(':')
    if len(proxy_url) > 1:
        result = ''.join([i for i in proxy_url[1] if i.isdigit()])
        cmd = 'sed -i "s|rpm|rpm --httpproxy {0} --httpport {1}|g" {2}'.format(proxy_url[0],
                                                                               result, file_name)
        print cmd
        run_cmd(cmd, shell=True, ignore_err=True)


def set_env(**kwargs):
    for key, value in kwargs.iteritems():
        os.environ[key] = value


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
        if not ignore_err:
            print >> sys.stderr, "ERROR: {0}".format(error)
            sys.exit(1)
        print >> sys.stdout, "WARNING: {0}".format(error)
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


def download_file(url, local_path, proxy=None):
    if proxy:
        cmd = "wget -e use_proxy=on -e http_proxy={0} -O {1} {2}".format(proxy, local_path, url)
    else:
        cmd = "wget -O {0} {1}".format(local_path, url)
    print cmd
    run_call(cmd, shell=True)


def download_and_extract_tar(tarfile_url, local_file_name, tarfile_type=None, extract_dir=None, proxy=None):
    if extract_dir is None:
        extract_dir = '/tmp'
    if tarfile_type is None:
        tarfile_type = "r:gz"
    # try:
    #     urllib.urlretrieve(tarfile_url, local_file_name)
    # except IOError as err:
    #     print >> sys.stderr, err

    download_file(tarfile_url, local_file_name, proxy)

    print "untar " + local_file_name
    try:
        tar = tarfile.open(local_file_name, tarfile_type)
        tar.extractall(extract_dir)
        tar.close()
    except tarfile.TarError as err:
        print >> sys.stderr, err


def clone_git_repo(REPO_URL, LOCAL_DIR, proxy=None):
    if proxy:
        cmd = "git config --global http.proxy {0}".format(proxy)
        run_call(cmd, shell=True)
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
               "zlib1g-dev python-dev python-pip libcurl4-openssl-dev libvirt-dev sudo libmysqlclient-dev git wget"
        run_cmd(cmd1, shell=True)
        run_cmd(cmd2, shell=True)

    elif platform.dist()[0].lower() == "centos" or platform.dist()[0].lower() == "redhat":
        print "found centos/redhat installing developments tools and dependencies..."
        # cmd1 = "yum groupinstall -y 'Development Tools'"
        cmd1 = "yum -y install libcurl libcurl-devel rrdtool rrdtool-devel rrdtool-prel libgcrypt-devel gcc make gcc-c++"
        cmd2 = "yum install -y curl python-devel libcurl libvirt-devel perl-ExtUtils-Embed sudo mysql-devel git wget"
        cmd3 = "yum update -y"
        # run_cmd(cmd3, shell=True)
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

# def install_pip():
#     print "install latest version of pip"
#     pip_install_url = "https://bootstrap.pypa.io/get-pip.py"
#     try:
#         urllib.urlretrieve(pip_install_url, "/tmp/get-pip.py")
#     except IOError as err:
#         print >> sys.stderr, err
#     run_cmd("python /tmp/get-pip.py", shell=True)

def install_pip(proxy=None):
    print "install latest version of pip"
    pip_install_url = "https://bootstrap.pypa.io/get-pip.py"
    local_file = "/tmp/get-pip.py"
    download_file(pip_install_url, local_file, proxy)
    # if proxy:
    #     cmd = "curl -x {0} -o /tmp/get-pip.py {1}".format(proxy, pip_install_url)
    # else:
    #     cmd = "curl -o /tmp/get-pip.py {0}".format(pip_install_url)
    # print cmd
    # run_call(cmd, shell=True)
    run_cmd("python {0}".format(local_file), shell=True)


def install_python_packages(proxy=None):
    """
    install required python packages
    :return:
    """
    print "install python packages using pip"
    if proxy:
        cmd2 = "pip install --upgrade setuptools libvirt-python==2.0.0 collectd psutil argparse pyyaml " \
               "mako web.py --proxy {0}".format(proxy)
    else:
        cmd2 = "pip install --upgrade setuptools libvirt-python==2.0.0 collectd psutil argparse pyyaml mako web.py"
    run_cmd(cmd2, shell=True)


def setup_collectd(proxy=None):
    """
    install a custoum collectd from source
    :return:
    """
    # download and extract collectd
    print "downloading collectd..."
    download_and_extract_tar(COLLCTD_SOURCE_URL, "/tmp/{0}.tar.bz2".format(COLLCTD_SOURCE_FILE), tarfile_type="r:bz2",
                             proxy=proxy)

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


def install_fluentd(proxy=None):
    """
    install fluentd and start the service
    :return:
    """

    distro, version, name = platform.dist()
    fluentd_file_name = "/tmp/install-fluentd.sh"
    if distro.lower() == "ubuntu":
        print "install fluentd for ubuntu {0} {1}".format(version, name)
        fluentd_install_url_ubuntu = "https://toolbelt.treasuredata.com/sh/install-ubuntu-{0}-td-agent2.sh".format(name)
        # urllib.urlretrieve(fluentd_install_url_ubuntu.format(name), "/tmp/install-ubuntu-{0}-td-agent2.sh".format(name))
        # run_cmd("sh /tmp/install-ubuntu-{0}-td-agent2.sh".format(name), shell=True)
        download_file(fluentd_install_url_ubuntu, fluentd_file_name, proxy)
        if proxy:
            # cmd = 'sed -i "s|curl|curl -x {0}|g" {1}'.format(proxy, fluentd_file_name)
            # print cmd
            # run_cmd(cmd, shell=True, ignore_err=True)
            _add_proxy_for_curl_in_file(proxy, fluentd_file_name)
        run_cmd("sh {0}".format(fluentd_file_name), shell=True)

    elif distro.lower() == "centos":
        print "install fluentd for centos/redhat {0} {1}".format(version, name)
        fluentd_install_url_centos = "https://toolbelt.treasuredata.com/sh/install-redhat-td-agent2.sh"
        # urllib.urlretrieve(fluentd_install_url_centos, "/tmp/install-redhat-td-agent2.sh")
        #
        download_file(fluentd_install_url_centos, fluentd_file_name, proxy)
        if proxy:
            # cmd = 'sed -i "s|curl|curl -x {0}|g" {1}'.format(proxy, fluentd_file_name)
            # print cmd
            # run_cmd(cmd, shell=True, ignore_err=True)
            _add_proxy_for_rpm_in_file(proxy, fluentd_file_name)
            _add_proxy_for_curl_in_file(proxy, fluentd_file_name)
        run_cmd("sh {0}".format(fluentd_file_name), shell=True)

    print "start fluentd ..."
    run_cmd("/usr/sbin/td-agent-gem install fluent-plugin-elasticsearch", shell=True)
    run_cmd("/usr/sbin/td-agent-gem install fluent-plugin-kafka", shell=True)
    run_cmd("/etc/init.d/td-agent start", shell=True)
    run_cmd("/etc/init.d/td-agent status", shell=True, print_output=True)


def add_collectd_plugins(proxy=None):
    """
    add plugins to collectd installed
    :return:
    """
    # download_and_extract_tar(collectd_plugins_source_url, "/tmp/plugins.tar.gz")
    clone_git_repo(COLLECTD_PLUGINS_REPO, COLLECTD_PLUGINS_DIR, proxy=proxy)
    # try:
    #     shutil.copytree("/tmp/plugins", "/opt/collectd/plugins")
    # except shutil.Error as err:
    #     print >> sys.stderr, err
    if os.path.isfile("{0}/requirements.txt".format(COLLECTD_PLUGINS_DIR)):
        if proxy:
            cmd = "pip install -r {0}/requirements.txt --proxy {1}".format(COLLECTD_PLUGINS_DIR, proxy)
        else:
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


def install_configurator(host, port, proxy=None):
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
    clone_git_repo(CONFIGURATOR_SOURCE_REPO, CONFIGURATOR_DIR, proxy=proxy)
    print "setup configurator..."
    if os.path.isdir(CONFIGURATOR_DIR):
        print "starting configurator ..."

        if platform.dist()[0].lower() == "ubuntu":
            cmd2 = "cd {0}; nohup python api_server.py -i {1} -p {2} &".format(CONFIGURATOR_DIR, host, port)
            print cmd2
            run_call(cmd2, shell=True)
            sleep(5)
        elif platform.dist()[0].lower() == "centos":
            cmd2 = "cd {0}; nohup python api_server.py -i {1} -p {2} &> /dev/null &".format(CONFIGURATOR_DIR, host,
                                                                                            port)
            print cmd2
            run_call(cmd2, shell=True)
            sleep(5)


def create_configurator_service():
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
                shutil.copyfile("/opt/configurator-exporter/init_scripts/configurator.conf",
                                "/etc/init/configurator.conf")
            except shutil.Error as err:
                print >> sys.stderr, err
                # run_cmd("chmod +x /etc/init/configurator.conf", shell=True)
        else:
            try:
                shutil.copyfile("/opt/configurator-exporter/init_scripts/configurator.service",
                                "/etc/systemd/system/configurator.service")
            except shutil.Error as err:
                print >> sys.stderr, err
            run_cmd("systemctl daemon-reload", shell=True, ignore_err=True)

    elif platform.dist()[0].lower() == "centos":
        print "found centos ..."
        version = platform.dist()[1]
        print "centos version: {0}".format(version)
        if version < "7.0":
            try:
                shutil.copyfile("/opt/configurator-exporter/init_scripts/configurator_centos6",
                                "/etc/init.d/configurator")
            except shutil.Error as err:
                print >> sys.stderr, err
            run_cmd("chmod +x /etc/init.d/configurator", shell=True)
        else:
            try:
                shutil.copyfile("/opt/configurator-exporter/init_scripts/configurator.service",
                                "/etc/systemd/system/configurator.service")
            except shutil.Error as err:
                print >> sys.stderr, err
            run_cmd("systemctl daemon-reload", shell=True, ignore_err=True)

    print "terminate any old instance of configurator if available"
    run_cmd("kill $(ps aux | grep -v grep | grep 'api_server' | awk '{print $2}')", shell=True, ignore_err=True)
    print "start configurator ..."
    # run_cmd("systemctl daemon-reload", shell=True, ignore_err=True)
    run_cmd("sudo service configurator start", shell=True, print_output=True)
    run_cmd("service configurator status", shell=True, print_output=True)


def install(collectd=True, fluentd=True, configurator=True, configurator_host="0.0.0.0", configurator_port=8000,
            http_proxy=None, https_proxy=None):
    """
    use this function to controll installation process
    :param collectd:
    :param fluentd:
    :param configurator:
    :param configurator_host:
    :param configurator_port:
    :param http_proxy:
    :param https_proxy:
    :return:
    """
    if not collectd and not fluentd:
        print >> sys.stderr, "you cannot skip both collectd and fluentd installation"
        sys.exit(128)

    if http_proxy:
        set_env(http_proxy=http_proxy)
    if https_proxy:
        set_env(http_proxy=https_proxy)
    proxy = https_proxy
    if not proxy:
        proxy = http_proxy
    update_hostfile()
    install_dev_tools()
    install_pip(proxy)

    if configurator:
        print "started installing configurator ..."
        install_configurator(host=configurator_host, port=configurator_port, proxy=proxy)
        configure_iptables(port_number=args.port)
    # create_configurator_service()

    if collectd:
        print "Started installing collectd ..."
        install_python_packages(proxy)
        setup_collectd(proxy)
        add_collectd_plugins(proxy)
        create_collectd_service()

    if fluentd:
        print "started installing fluentd ..."
        install_fluentd(proxy)

    sys.exit(0)


def get_os():
    """
    return os name
    :return:
    """
    return platform.dist()[0].lower()


def remove_iptables_rule(port_number=8000):
    """
    clear any previously added iptable rule on port_number
    :param port_number:
    :return:
    """
    clean_rule = "iptables -D INPUT -p tcp -m tcp --dport {0} -j ACCEPT".format(port_number)
    run_cmd(clean_rule, shell=True, ignore_err=True)


def configure_iptables(port_number=8000):
    """
    add rule to accept traffic on configurator port
    :param port_number
    :return:
    """
    add_rule = "iptables -I INPUT 1 -p tcp -m tcp --dport {0} -j ACCEPT".format(port_number)
    save_rule = "iptables-save"
    if get_os() == "ubuntu":
        restart_iptables = "service ufw restart"
    elif get_os() == "centos":
        save_rule = "iptables-save | sudo tee /etc/sysconfig/iptables"
        restart_iptables = "service iptables restart"
    else:
        restart_iptables = "service iptables restart"

    remove_iptables_rule(port_number)
    run_cmd(add_rule, shell=True, ignore_err=True)
    run_cmd(save_rule, shell=True, ignore_err=True)
    run_cmd(restart_iptables, shell=True, ignore_err=True)

def update_hostfile():
    hosts_file = "/etc/hosts"
    hostname = platform.node()
    hostname = hostname.strip()
    IP = "127.0.1.1"
    try:
        f = open(hosts_file, "r")
        data = f.readlines()
        new_data = []
        found = False
        for line in data:
            if IP in line and not line.startswith("#"):
                if hostname not in line:
                    line = "{0} {1}".format(line, hostname)
                    new_data.append(line)
                else:
                    new_data.append(line)
                found = True
            else:
                new_data.append(line)
        if not found:
            hostname = hostname + '\n'
            line = "{0} {1}".format(IP, hostname)
            new_data.append(line)
        f.close()

        f = open(hosts_file, 'w')
        f.write(''.join(new_data))
        f.close()
    except:
        print "FAILED to update hostname"

if __name__ == '__main__':
    """main function"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-sc', '--skipcollectd', action='store_false', default=True, dest='installcollectd',
                        help='skip collectd installation')
    parser.add_argument('-sf', '--skipfluentd', action='store_false', default=True, dest='installfluentd',
                        help='skip fluentd installation')
    parser.add_argument('-sce', '--skipconfigurator', action='store_false', default=True, dest='installconfigurator',
                        help='skip configurator installation')
    parser.add_argument('-p', '--port', action='store', default="8000", dest='port',
                        help='port on which configurator will listen')
    parser.add_argument('-ip', '--host', action='store', default="0.0.0.0", dest='host',
                        help='host ip on which configurator will listen')
    parser.add_argument('--http_proxy', action='store', default="", dest='http_proxy',
                        help='http proxy for connecting to internet')
    parser.add_argument('--https_proxy', action='store', default="", dest='https_proxy',
                        help='https proxy for connecting to internet')
    args = parser.parse_args()

    install(collectd=args.installcollectd,
            fluentd=args.installfluentd,
            configurator=args.installconfigurator,
            configurator_host=args.host,
            configurator_port=args.port,
            http_proxy=args.http_proxy,
            https_proxy=args.https_proxy)
