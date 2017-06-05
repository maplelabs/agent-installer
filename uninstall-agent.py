import os
import shutil
import subprocess
import sys
import platform
import argparse

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


def run_call(cmd, shell, ignore_err=False):
    """
    run a command don't check output
    :param ignore_err
    :param cmd:
    :param shell:
    :return:
    """
    try:
        subprocess.call(cmd, shell=shell)
    except subprocess.CalledProcessError as error:
        print >> sys.stderr, "Error: {0}".format(error)
        if not ignore_err:
            sys.exit(1)
        print "error ignored"
        return


def uninstall_collecd():
    run_cmd("service collectd stop", shell=True, ignore_err=True)
    if os.path.exists("/opt/collectd"):
        shutil.rmtree("/opt/collectd")
    if os.path.exists("/etc/init.d/collectd"):
        os.remove("/etc/init.d/collectd")
    if os.path.exists("/etc/systemd/system/collectd.service"):
        os.remove("/etc/systemd/system/collectd.service")
    run_cmd("kill $(ps aux | grep -v grep | grep 'collectd' | awk '{print $2}')", shell=True, ignore_err=True)


def uninstall_fluentd():
    run_cmd("/etc/init.d/td-agent stop", shell=True, ignore_err=True)
    if platform.dist()[0].lower() == "ubuntu" or platform.dist()[0].lower() == "debian":
        run_cmd("apt-get remove td-agent", shell=True)
        run_cmd("apt-get purge td-agent", shell=True)
    elif platform.dist()[0].lower() == "centos" or platform.dist()[0].lower() == "redhat":
        run_cmd("yum remove td-agent", shell=True)
    if os.path.exists("/opt/td-agent"):
        shutil.rmtree("/opt/td-agent")
    if os.path.exists("/var/log/td-agent"):
        shutil.rmtree("/var/log/td-agent")
    if os.path.exists("/etc/td-agent"):
        shutil.rmtree("/etc/td-agent")


def uninstall_configurator():
    run_cmd("kill $(ps aux | grep -v grep | grep 'api_server' | awk '{print $2}')", shell=True, ignore_err=True)
    if os.path.exists("/opt/configurator-exporter"):
        shutil.rmtree("/opt/configurator-exporter")


def uninstall(removecollectd=True, removefluentd=True, removeconfigurator=True):
    if removecollectd:
        print "removing collectd ..."
        uninstall_collecd()

    if removefluentd:
        print "removing fluentd ..."
        uninstall_fluentd()

    if removeconfigurator:
        print "removing configurator ..."
        uninstall_configurator()


if __name__ == '__main__':
    """main function"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-sc', '--removecollectd', action='store_false', default=True, dest='removecollectd',
                        help='remove collectd installation')
    parser.add_argument('-sf', '--removefluentd', action='store_false', default=True, dest='removefluentd',
                        help='remove fluentd installation')
    parser.add_argument('-sce', '--removeconfigurator', action='store_false', default=True, dest='removeconfigurator',
                        help='remove configurator installation')
    args = parser.parse_args()

    uninstall(removecollectd=args.removecollectd,
              removefluentd=args.removefluentd,
              removeconfigurator=args.removeconfigurator)
