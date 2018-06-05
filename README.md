cmadison
========
Because I couldn't come up with a better name, its called cmadison... cmadison provides a wrapper
around rmadison which includes information regarding the packages in the Ubuntu cloud-archive in
addition to the traditional sources (e.g. debian, ubuntu, etc).

### Usage

1. Query the Ubuntu cloud-archive for package versions:

```
wolsen@chaps:~/work/cmadison/cmadison$ ./cmadison.py nova
 nova | 1:2014.2.3-0ubuntu1.2~cloud0 | juno     | source
 nova | 1:2015.1.1-0ubuntu1~cloud2   | kilo     | source
 nova | 2:12.0.0~b2-0ubuntu2~cloud0  | liberty  | source
 nova | 2012.2.4-0ubuntu3.1~cloud0   | folsom   | source
 nova | 1:2013.1.5-0ubuntu1~cloud0   | grizzly  | source
 nova | 1:2013.2.3-0ubuntu1~cloud0   | havana   | source
 nova | 1:2014.1.5-0ubuntu1.2~cloud0 | icehouse | source
```

2. Query multiple sources:

```
wolsen@chaps:~/work/cmadison/cmadison$ ./cmadison.py -u cloud-archive,ubuntu,debian nova
cloud-archive:
 nova | 1:2014.2.3-0ubuntu1.2~cloud0 | juno     | source
 nova | 1:2015.1.1-0ubuntu1~cloud2   | kilo     | source
 nova | 2:12.0.0~b2-0ubuntu2~cloud0  | liberty  | source
 nova | 2012.2.4-0ubuntu3.1~cloud0   | folsom   | source
 nova | 1:2013.1.5-0ubuntu1~cloud0   | grizzly  | source
 nova | 1:2013.2.3-0ubuntu1~cloud0   | havana   | source
 nova | 1:2014.1.5-0ubuntu1.2~cloud0 | icehouse | source
ubuntu:
 nova | 2012.1-0ubuntu2                              | precise          | source
 nova | 2012.1.3+stable-20130423-e52e6912-0ubuntu1.4 | precise-security | source
 nova | 2012.1.3+stable-20130423-e52e6912-0ubuntu1.4 | precise-updates  | source
 nova | 1:2014.1-0ubuntu1                            | trusty           | source
 nova | 1:2014.1.3-0ubuntu1.1                        | trusty-security  | source
 nova | 1:2014.1.5-0ubuntu1.2                        | trusty-updates   | source
 nova | 1:2015.1~rc1-0ubuntu1                        | vivid            | source
 nova | 1:2015.1.1-0ubuntu1                          | vivid-updates    | source
 nova | 2:12.0.0~b3-0ubuntu2                         | wily             | source
debian:
 nova | 2012.1.1-18       | wheezy           | source
 nova | 2014.1.3-11       | jessie-kfreebsd  | source
 nova | 2014.1.3-11       | jessie           | source
 nova | 2015.1.0-2~bpo8+1 | jessie-backports | source
 nova | 2015.1.0-8        | stretch          | source
 nova | 2015.1.0-8        | sid              | source
 nova | 1:12.0.0~b3-1     | experimental     | source
```

