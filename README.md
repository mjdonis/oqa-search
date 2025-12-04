# oqa-search
UV openQA helper script created to help/automate the searching phase inside openQA for a given MU 
to test. The script searches inside all the openQA job groups related with a given MU and 
generates an output suitable to add (copy/paste) inside the update log.

[Hackweek 2024 project](https://hackweek.opensuse.org/24/projects/enhance-uv-openqa-helper-script)
[Hackweek 2025 project](https://hackweek.opensuse.org/projects/work-on-enhancements-for-oqa-search)

## Usage
The main script can be run on its own. Alternatively, if this package is installed a command for it will also be 
installed as part of the package: `oqa-search`
```bash
$ ./oqa_search.py --help
usage: oqa_search.py [-h] [--url-dashboard-qam URL_DASHBOARD_QAM]
                     [--url-openqa URL_OPENQA] [--url-qam URL_QAM]
                     [--no-aggregated] [--days DAYS]
                     [--aggregated-groups {core,containers,yast,security} [{core,containers,yast,security} ...]]
                     update_id

For a given update, search inside the Single Incidents - Core Incidents and
Aggregated updates job groups for openQA builds related to the update. It
searches by default within the last 5 days in the "Aggregated updates"
section.

positional arguments:
  update_id             Update ID, format SUSE:Maintenance:xxxxx:xxxxxx or
                        S:M:xxxxx:xxxxxx

optional arguments:
  -h, --help            show this help message and exit
  --url-dashboard-qam URL_DASHBOARD_QAM
                        QAM dashboard URL (default:
                        http://dashboard.qam.suse.de)
  --url-openqa URL_OPENQA
                        OpenQA URL (default: https://openqa.suse.de)
  --url-qam URL_QAM     QAM URL (default: https://qam.suse.de)
  --no-aggregated       Don't search for jobs in the Aggregated Updates
                        section (default: False)
  --days DAYS           How many days to search back for in the Aggregated
                        Updates section (default: 5)
  --aggregated-groups {core,containers,yast,security} [{core,containers,yast,security} ...]
                        Job groups to look into inside the Aggregated
                        Updates section (default: ['core'])
```

Example usages:
As a standalone script:
```
$ ./oqa_search.py SUSE:Maintenance:36419:353574 --no-aggregated
OpenQA:
#######
Single incidents - Core
15-SP3 -> https://openqa.suse.de/tests/overview?distri=sle&version=15-SP3&build=:36419:automake&groupid=367
PASSED
15-SP2 -> https://openqa.suse.de/tests/overview?distri=sle&version=15-SP2&build=:36419:automake&groupid=306
PASSED
15-SP4 -> https://openqa.suse.de/tests/overview?distri=sle&version=15-SP4&build=:36419:automake&groupid=439
PASSED
15-SP5 -> https://openqa.suse.de/tests/overview?distri=sle&version=15-SP5&build=:36419:automake&groupid=490
PASSED
15-SP4-TERADATA -> https://openqa.suse.de/tests/overview?distri=sle&version=15-SP4-TERADATA&build=:36419:automake&groupid=521
PASSED
15-SP6 -> https://openqa.suse.de/tests/overview?distri=sle&version=15-SP6&build=:36419:automake&groupid=546
PASSED
-------

Build checks
https://qam.suse.de/testreports/SUSE:Maintenance:36419:353574/build_checks/automake-testsuite.SUSE_SLE-15_Update.i586.log
[ 1009s] # TOTAL: 2901
[ 1009s] # PASS:  2709
[ 1009s] # SKIP:  151
[ 1009s] # XFAIL: 41
[ 1009s] # FAIL:  0
[ 1009s] # XPASS: 0
[ 1009s] # ERROR: 0 

https://qam.suse.de/testreports/SUSE:Maintenance:36419:353574/build_checks/automake-testsuite.SUSE_SLE-15_Update.ppc64le.log
[ 2098s] # TOTAL: 2901
[ 2098s] # PASS:  2709
[ 2098s] # SKIP:  151
[ 2098s] # XFAIL: 41
[ 2098s] # FAIL:  0
[ 2098s] # XPASS: 0
[ 2098s] # ERROR: 0 

https://qam.suse.de/testreports/SUSE:Maintenance:36419:353574/build_checks/automake-testsuite.SUSE_SLE-15_Update.s390x.log
[ 2726s] # TOTAL: 2901
[ 2726s] # PASS:  2709
[ 2726s] # SKIP:  151
[ 2726s] # XFAIL: 41
[ 2726s] # FAIL:  0
[ 2726s] # XPASS: 0
[ 2726s] # ERROR: 0 

https://qam.suse.de/testreports/SUSE:Maintenance:36419:353574/build_checks/automake-testsuite.SUSE_SLE-15_Update.x86_64.log
[  949s] # TOTAL: 2901
[  949s] # PASS:  2709
[  949s] # SKIP:  151
[  949s] # XFAIL: 41
[  949s] # FAIL:  0
[  949s] # XPASS: 0
[  949s] # ERROR: 0 

https://qam.suse.de/testreports/SUSE:Maintenance:36419:353574/build_checks/automake-testsuite.SUSE_SLE-15_Update.aarch64.log
[ 1038s] # TOTAL: 2901
[ 1038s] # PASS:  2708
[ 1038s] # SKIP:  152
[ 1038s] # XFAIL: 41
[ 1038s] # FAIL:  0
[ 1038s] # XPASS: 0
[ 1038s] # ERROR: 0 

```

Invoking the script with `oqa-search` after installing the package:
``` 
$ oqa-search SUSE:Maintenance:36413:353665 --aggregated-groups core containers
OpenQA:
#######
Single incidents - Core
15-SP6 -> https://openqa.suse.de/tests/overview?distri=sle&version=15-SP6&build=:36413:yast2-iscsi-client&groupid=546
PASSED
-------

Aggregated updates - Core
15-SP6 -> https://openqa.suse.de/tests/overview?distri=sle&version=15-SP6&build=20241120-1&groupid=414
FAILED (2 jobs)

Aggregated updates - Containers
15-SP6 -> https://openqa.suse.de/tests/overview?distri=sle&version=15-SP6&build=20241120-1&groupid=417
FAILED (8 jobs)
-------

Build checks
https://qam.suse.de/testreports/SUSE:Maintenance:36413:353665/build_checks/yast2-iscsi-client.SUSE_SLE-15-SP6_Update.x86_64.log
[   46s] 97 examples, 0 failures

https://qam.suse.de/testreports/SUSE:Maintenance:36413:353665/build_checks/yast2-iscsi-client.SUSE_SLE-15-SP6_Update.aarch64.log
[   47s] 97 examples, 0 failures

https://qam.suse.de/testreports/SUSE:Maintenance:36413:353665/build_checks/yast2-iscsi-client.SUSE_SLE-15-SP6_Update.ppc64le.log
[   81s] 97 examples, 0 failures

https://qam.suse.de/testreports/SUSE:Maintenance:36413:353665/build_checks/yast2-iscsi-client.SUSE_SLE-15-SP6_Update.i586.log
[   56s] 97 examples, 0 failures

https://qam.suse.de/testreports/SUSE:Maintenance:36413:353665/build_checks/yast2-iscsi-client.SUSE_SLE-15-SP6_Update.s390x.log
[   53s] 97 examples, 0 failures

```
