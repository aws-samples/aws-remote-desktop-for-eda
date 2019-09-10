#@IgnoreInspection BashAddShebang
#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

echo hello

function install_prereqs {
  sudo yum -y upgrade
  sudo yum -y install xhost wget
  sudo yum -y groupinstall "GNOME Desktop"
  gui_inst_rc=$?
  if [[ "$gui_inst_rc" = "1" ]]; then
    sudo yum -y groupinstall "Server with GUI"
  fi
  sudo yum -y upgrade
}

function install_dcv {
  mkdir /tmp/dcv-inst.d
  pushd /tmp/dcv-inst.d
  rpm --import https://s3-eu-west-1.amazonaws.com/nice-dcv-publish/NICE-GPG-KEY
  wget https://d1uj6qtbmh3dt5.cloudfront.net/server/nice-dcv-2017.4-6898-el7.tgz
  tar xvf nice-dcv-2017.4-6898-el7.tgz
  cd nice-dcv-2017.4-6898-el7/
  yum -y install nice-dcv-server-2017.4.6898-1.el7.x86_64.rpm nice-xdcv-2017.4.210-1.el7.x86_64.rpm nice-dcv-gltest-2017.4.216-1.el7.x86_64.rpm
  popd
}

function add_user {

  user_name=${user_name}
  user_pass=${user_pass}

  groupadd ${user_name}
  useradd ${user_name} -m -g ${user_name}
  echo "${user_name}:${user_pass}" | chpasswd
  echo "Created user ${user_name}"

}

function cr_post_reboot {

if [[ ! -d /opt/dcv-install ]]; then
  mkdir -p /opt/dcv-install
fi

cat << EOF > /opt/dcv-install/post_reboot.sh
#!/usr/bin/env bash

function stop_disable_svc() {
  systemctl stop \$1
  systemctl disable \$1
}

function cr_dcv_session(){
  dcv create-session --type=virtual --owner ${user_name} --user ${user_name} virt
}

stop_disable_svc firewalld
stop_disable_svc libvirtd
systemctl set-default graphical.target
DISPLAY=:0 XAUTHORITY=\$(ps aux | grep "X.*\\-auth" | grep -v grep | awk -F"-auth " '{print \$2}' | awk '{print \$1}') xhost | grep "SI:localuser:dcv$"
ls_dcv_sessions=\$(dcv list-sessions 2>&1)
while [[ "\$ls_dcv_sessions" = "There are no sessions available" ]]; do
  echo "No DCV session available, creating a session..."
  cr_dcv_session
  ls_dcv_sessions=\$(dcv list-sessions 2>&1)
  sleep 5
done

my_wait_handle="${my_wait_handle}"

if [[ ! -f /tmp/wait-handle-sent ]]; then
  exit 0
else
  wait_handle_status=\$(cat /tmp/wait-handle-sent)
  if [[ \${wait_handle_status} == "true" ]]; then
    rm /tmp/wait-handle-sent
    exit 0
  elif [[ \${wait_handle_status} == "false" && \${my_wait_handle} != "" ]] ; then
    echo "Sending success to wait handle"
    curl -X PUT -H 'Content-Type:' --data-binary '{ "Status" : "SUCCESS",  "Reason" : "instance launched",  "UniqueId" : "inst001",  "Data" : "instance launched."}' "\${my_wait_handle}"
    echo "true" > /tmp/wait-handle-sent
  fi
fi

EOF

chmod 744 /opt/dcv-install/post_reboot.sh

}

function cr_service {

cat << EOF > /etc/systemd/system/post-reboot.service
[Unit]
Description=Post reboot service

[Service]
ExecStart=/opt/dcv-install/post_reboot.sh

[Install]
WantedBy=multi-user.target
EOF

chmod 664 /etc/systemd/system/post-reboot.service
systemctl daemon-reload
systemctl enable post-reboot.service

}

function stop_disable_svc() {
  systemctl stop $1
  systemctl disable $1
}


function main {

install_prereqs
install_dcv
add_user
cr_post_reboot
cr_service

systemctl set-default graphical.target
systemctl enable dcvserver
echo "false" > /tmp/wait-handle-sent
stop_disable_svc firewalld
stop_disable_svc libvirtd
reboot

}

main
