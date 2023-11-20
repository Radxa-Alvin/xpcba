#/usr/bin/python3
import os
import pwd
import subprocess
from subprocess import PIPE

from string import Template


def run(cmd, user_name='rock', cwd='/tmp'):
    pwnam = pwd.getpwnam(user_name)
    env = os.environ.copy()
    env.update({
        'PWD': cwd,
        'HOME': pwnam.pw_dir,
        'USER': pwnam.pw_name,
        'LOGNAME': pwnam.pw_name
    })
    # report_ids('starting ' + cmd)
    process = subprocess.Popen(
        cmd.split(' '), cwd=cwd, env=env, stdout=PIPE, stderr=PIPE,
        preexec_fn=demote(pwnam.pw_uid, pwnam.pw_gid)
    )
    result = process.wait()
    # report_ids('finished ' + cmd)
    print('result', result)


def demote(user_uid, user_gid):
    def result():
        report_ids('starting demotion')
        os.setgid(user_gid)
        os.setuid(user_uid)
        report_ids('finished demotion')
    return result


def report_ids(msg):
    print('uid, gid = %d, %d; %s' % (os.getuid(), os.getgid(), msg))


tpl = Template('''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>INFO</title>
    <style>
    .vertical-container {
        height: 300px;
        display: -webkit-flex;
        display:         flex;
        -webkit-align-items: center;
                align-items: center;
        -webkit-justify-content: center;
                justify-content: center;
    }
    </style>
</head>
<body>
    <div class="vertical-container">
        <div>
            <h1>$msg</h1>
        </div>
    </div>
</body>
</html>
''')


def show_msg(msg):
    msg_html = '/tmp/msg.html'
    position = '--window-position=600,400'
    window_size = '--window-size=600,400'
    with open(msg_html, 'w') as f:
        f.write(tpl.substitute(msg=msg))
    run(f'chromium {position} {window_size} --app=file://{msg_html}')
    os.remove(msg_html)


if __name__ == '__main__':
    show_msg('hello world')
