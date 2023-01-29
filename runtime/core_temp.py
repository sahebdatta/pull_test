import glob
import os
import collections
import re

def cat(fname, fallback=object()):
    try:
        with open(fname) as f:
            return f.read()
    except (IOError, OSError):
        return fallback

def bcat(fname, fallback=object()):
    return cat(fname, fallback=object())

def sensors_temperatures():
    """Return hardware (CPU and others) temperatures as a dict
    including hardware name, label, current, max and critical
    temperatures.
    Implementation notes:
    - /sys/class/hwmon looks like the most recent interface to
      retrieve this info, and this implementation relies on it
      only (old distros will probably use something else)
    - lm-sensors on Ubuntu 16.04 relies on /sys/class/hwmon
    - /sys/class/thermal/thermal_zone* is another one but it's more
      difficult to parse
    """
    ret = collections.defaultdict(list)
    basenames = glob.glob('/sys/class/hwmon/hwmon*/temp*_*')
    basenames.extend(glob.glob('/sys/class/hwmon/hwmon*/device/temp*_*'))
    basenames = sorted(set([x.split('_')[0] for x in basenames]))

    basenames2 = glob.glob(
        '/sys/devices/platform/coretemp.*/hwmon/hwmon*/temp*_*')
    repl = re.compile('/sys/devices/platform/coretemp.*/hwmon/')
    for name in basenames2:
        altname = repl.sub('/sys/class/hwmon/', name)
        if altname not in basenames:
            basenames.append(name)

    for base in basenames:
        try:
            path = base + '_input'
            f = open(path)
            current = float(f.read()) / 1000.0
            path = os.path.join(os.path.dirname(base), 'name')
        except (IOError, OSError, ValueError):
            continue

    # Indication that no sensors were detected in /sys/class/hwmon/
    if not basenames:
        basenames = glob.glob('/sys/class/thermal/thermal_zone*')
        basenames = sorted(set(basenames))

        for base in basenames:
            try:
                path = os.path.join(base, 'temp')
                f = open(path)
                current = float(f.read()) / 1000.0
                path = os.path.join(base, 'type')
            except (IOError, OSError, ValueError) as err:
                print(err)
                continue

    return current