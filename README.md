# xpcba

xpcba（暂称）是万莫斯统一测试套件

## 缘起

为什么我们需要一套新的测试工具？目前我们在产测时使用多种测试工具，在开发和维护上需花费不少时间成本，且会随着平台的增多而增加。另外目前所使用的工具拓展性不佳。

## 优点

1. 多接口支持，可使用 adb 、eth 或 wifi 连接 设备端 与 客户端；
2. 多平台支持，客户端可使用 Windows 或 Linux 的 PC，或者 ROCK Pi；
3. 设备系统要求低，设备端可运行任意系统，只需支持 Python 3 即可；
4. 工具拓展性良好，可给测试任务添加钩子，如录音回传播放，如上传测试日志；
5. 测试程序要求低，可使用 C 或 Shell 或 Python 编写测试程序，只需符合约定即可；
6. 测试任务易分配，每个测试项相互独立，测试任务可分配给多人编写；
7. 测试程序易复用，使用配置文件描述板子，修改配置文件可复用部分程序；
8. 客户端可 Hack，测试时可修改设备端程序，此可用于小修改而不用重烧录固件；

## 缺点

1. 在最初编写测试程序需花费不少时间；
2. 尚没用于大规模生产中，可行性待验证；
3. 工具处于试验中，可能会有 bug；
4. 熟悉新工具需花费时间；

## 进度

1. 基本设计已完成，可使用命令行测试，GUI 还没编写；
2. 上传日志服务端还没开始编写；

## 运行

1. 设备端

   拷贝 core 目录至设备，运行 server.py

   ```bash
   $ python3 core/server.py
   ```

2. 客户端

   ```bash
   $ adb forward tcp:6688 tcp:6688
   $ python3 core/client.py  # 测试交互是否成功
   ```

   目前提供了 ui/cli.py，可作为测试的入口

   ```bash
   $ python3 ui/cli.py -b vc098
   ```

   此会读取 `conf/vc098.json` 的测试项，进入测试并打印测试结果。

## 生成测试镜像

1. 正常生成Debian CLI镜像，需要tmux
2. 运行以下命令：

   ````bash
   #!/bin/bash

   # On host: apt install multipath-tools qemu-user-static

   SOURCE_IMG="radxa-zero2_debian_bullseye_cli.img"
   # To view test result via monitor
   #TEST_ENV="getty@tty1"
   # or via serial
   # Need to update `ttyAML0` to real serial device
   TEST_ENV="serial-getty@ttyAML0"
   PRODUCT="rs102"

   # Make a backup
   cp "$SOURCE_IMG" xpcba.img

   # Mount image
   ROOT_DEV=$(sudo kpartx xpcba.img | tail -n 1 | cut -d ' ' -f 1)
   sudo kpartx -a xpcba.img
   mkdir ./mnt
   sudo mount /dev/mapper/$ROOT_DEV ./mnt

   # Set up auto login
   SYSTEMD_OVERRIDE=./mnt/etc/systemd/system/$TEST_ENV.service.d
   sudo mkdir -p $SYSTEMD_OVERRIDE
   cat << EOF | sudo tee $SYSTEMD_OVERRIDE/override.conf
   [Service]
   ExecStart=
   EOF
   if grep -q "serial" <<< $TEST_ENV
   then
       AUTOLOGIN="ExecStart=-/sbin/agetty --autologin root -o '-p -- \\\\u' --noclear %I \$TERM"
   else
       AUTOLOGIN="ExecStart=-/sbin/agetty --autologin root -o '-p -- \\\\u' --keep-baud 115200,57600,38400,9600 %I \$TERM"
   fi
   sudo tee -a $SYSTEMD_OVERRIDE/override.conf <<< $AUTOLOGIN

   # Download xpcba
   sudo git clone --depth 1 -b master http://gitlab.vamrs.com/xpcba/xpcba.git ./mnt/xpcba

   # Set up xpcba auto start
   cat << EOF | sudo tee -a ./mnt/root/.bashrc
   dmesg -n 1
   tmux new-session -d python3 /xpcba/core/server.py
   tmux new-session python3 /xpcba/ui/cli.py --board $PRODUCT --sku d4e16 --via local
   EOF

   # Delete root password so auto login won't ask for password
   sudo chroot ./mnt/ passwd --delete root

   # Clean up
   sudo umount ./mnt
   rm -rf ./mnt
   sudo kpartx -d xpcba.img
   ````

## 约定

1. 配置文件

   ui/config.json 为全局配置文件，conf 存放项目配置文件，如 vc098.json；

2. 测试程序

   bin 存放可运行文件或测试脚本，以项目名为文件夹组织。

   <del> 为了兼容 rkpcba，工具沿用了rkpcba 的交互格式，</del>程序在测试完成时需打印以下格式信息，

      ```text
      <msg>,<PASS|FAIL>,<ERR_CODE>
      ```

   如：

      ```text
      <bt_test>,<PASS>,<0>
      <ddr_test: size:256MB>,<FAIL>,<-54>
      ```

3. 参考程序

   可参考 `misc/rs309.sh` 去编写测试时的临时脚本，和对比它正式运行时的 `conf/rs309.json` 配置文件。
