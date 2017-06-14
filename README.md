# using scripts  
```shell
usage: install-agent.py [-h] [-sc] [-sf] [-sce] [-p PORT] [-ip HOST]
                       [--http_proxy HTTP_PROXY] [--https_proxy HTTPS_PROXY]

optional arguments:
  -h, --help            show this help message and exit
  -sc, --skipcollectd   skip collectd installation
  -sf, --skipfluentd    skip fluentd installation
  -sce, --skipconfigurator
                        skip configurator installation
  -p PORT, --port PORT  port on which configurator will listen
  -ip HOST, --host HOST
                        host ip on which configurator will listen
  --http_proxy HTTP_PROXY
                        http proxy for connecting to internet
  --https_proxy HTTPS_PROXY
                        https proxy for connecting to internet
```

```shell
usage: uninstall-agent.py [-h] [-sc] [-sf] [-sce]

optional arguments:
  -h, --help            show this help message and exit
  -sc, --removecollectd
                        remove collectd installation
  -sf, --removefluentd  remove fluentd installation
  -sce, --removeconfigurator
                        remove configurator installation
```
