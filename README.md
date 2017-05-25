#usage: 
```shell
deploy-agent.py [-h] [-sc] [-sf] [-p PORT] [-ip HOST]

optional arguments:
  -h, --help            show this help message and exit
  -sc, --skipcollectd   skip collectd installation
  -sf, --skipfluentd    skip fluentd installation
  -p PORT, --port PORT  port on which configurator will listen
  -ip HOST, --host HOST
                        host ip on which configurator will listen
```