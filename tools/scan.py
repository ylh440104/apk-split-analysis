#!/usr/bin/env python3
# Keyword scanner for decompiled APK (jadx java + apktool smali/res)
import os, re, sys, json, collections

ROOT_JADX = sys.argv[1] if len(sys.argv) > 1 else 'out_jadx'
ROOT_APK  = sys.argv[2] if len(sys.argv) > 2 else 'out_apktool'
OUT       = 'report'
FOCUS     = os.path.join(OUT, 'focus')
os.makedirs(FOCUS, exist_ok=True)

PATTERNS = collections.OrderedDict([
 ('fastboot', r'fastboot'),
 ('adb_usb', r'adb|usb_debug|usb_config|ADB_ENABLED|persist\.sys\.usb|sys\.usb\.config|functionfs|vold\.adb'),
 ('developer', r'developer[_ ]?option|DEVELOPMENT_SETTINGS|development_settings|开发者'),
 ('settings_write', r'Settings\.(Global|Secure|System)|settings put|WRITE_SECURE_SETTINGS|writeSecureSettings'),
 ('pm_disable', r'setComponentEnabledSetting|setApplicationEnabledSetting|pm \\?disable|disable-user|pm clear|attemptToApply|setState\(\s*COMPONENT'),
 ('shell_exec', r'Runtime\.getRuntime|ProcessBuilder|exec\(|/system/bin/sh|/system/xbin/su|\\\\bsu\\\\b|which su|libsuperuser|Shell\.run'),
 ('device_admin', r'DevicePolicyManager|DeviceAdminReceiver|addUserRestriction|setStatusBarDisabled|setCameraDisabled|lockNow|wipeData|DISALLOW_'),
 ('accessibility', r'AccessibilityService|AccessibilityManager|TYPE_ACCESSIBILITY_OVERLAY|performGlobalAction'),
 ('kiosk_lock', r'kiosk|lockTask|LockTaskController|startLockTask|setLockTaskPackages|DEFAULT_HOME|CATEGORY_HOME|HOME_CHANGED'),
 ('install_pm', r'INSTALL_PACKAGES|installPackage|PackageInstaller|InstallResultReceiver|pm install'),
 ('root_check', r'isRoot|RootCheck|magisk|Magisk|superuser|Superuser|busybox'),
 ('boot_power', r'REBOOT|reboot|shutdown|SHUTDOWN|PowerManager|goToSleep|deviceidle'),
 ('network_block', r'VpnService|setBlocking|BlockingMode|iptables|route|enableFirewall|connectivity'),
 ('watchdog', r'Watchdog|Guard|guard|keepAlive|KeepAlive|heartbeat|Daemon'),
 ('cn_keywords', r'设置|开发者|调试|开发者选项|刷机|解锁|恢复出厂|USB调试|限制|禁用|拦截'),
])
COMP = [(k, re.compile(v, re.I)) for k, v in PATTERNS.items()]

hits = collections.Counter()
lines = collections.defaultdict(list)
files_scanned = 0

def scan_file(path, kind):
    global files_scanned
    try:
        with open(path, 'r', errors='ignore') as f:
            txt = f.read()
    except Exception:
        return
    files_scanned += 1
    fl = txt.splitlines()
    for name, rx in COMP:
        for i, ln in enumerate(fl):
            if rx.search(ln):
                hits[name] += 1
                if len(lines[name]) < 4000:
                    lines[name].append(f'{path}:{i+1}: {ln.strip()[:300]}')

for root in (ROOT_JADX, ROOT_APK):
    if not os.path.isdir(root):
        continue
    for dp, dn, fn in os.walk(root):
        for f in fn:
            p = os.path.join(dp, f)
            if f.endswith(('.java', '.kt', '.smali', '.xml', '.json', '.properties', '.txt')):
                scan_file(p, dp)

with open(os.path.join(OUT, 'summary.txt'), 'w') as f:
    f.write(f'files_scanned={files_scanned}\n')
    for k in PATTERNS:
        f.write(f'{k}: {hits[k]}\n')
    f.write('\n== jadx dir exists: %s / apktool dir exists: %s\n' % (os.path.isdir(ROOT_JADX), os.path.isdir(ROOT_APK)))

for k, v in lines.items():
    with open(os.path.join(OUT, f'hits_{k}.txt'), 'w') as f:
        f.write('\n'.join(v))

# --- copy focus sources (class/file names likely related to control logic) ---
FOCUS_RX = re.compile(r'(fastboot|adb|usb|developer|setting|policy|admin|guard|kiosk|lock|control|permission|disab|forbid|restrict|su|root|shell|command|superior|zy/ai|launcher)', re.I)
copied = 0
for root in (ROOT_JADX, ROOT_APK):
    if not os.path.isdir(root):
        continue
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if not f.endswith(('.java', '.smali')):
                continue
            if not FOCUS_RX.search(f) and not FOCUS_RX.search(dp):
                continue
            src = os.path.join(dp, f)
            if os.path.getsize(src) > 400_000:
                continue
            rel = os.path.relpath(src, root).replace('/', '__')
            dst = os.path.join(FOCUS, ('jadx__' if root == ROOT_JADX else 'smali__') + rel)
            try:
                with open(src, 'r', errors='ignore') as a, open(dst, 'w') as b:
                    b.write(a.read())
                copied += 1
            except Exception:
                pass
print('files_scanned', files_scanned, 'focus_copied', copied)
for k in PATTERNS:
    print(f'{k}: {hits[k]}')
