#@IgnoreInspection BashAddShebang
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.
#

echo hello

function install_prereqs {
  sudo yum -y groupinstall "GNOME Desktop"
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
  mkdir /opt/dcv-install
fi

cat << EOF > /opt/dcv-install/post_reboot.sh
#!/usr/bin/env bash

function stop_disable_svc() {
  systemctl stop \$1
  systemctl disable \$1
}

stop_disable_svc firewalld
stop_disable_svc libvirtd
systemctl isolate multi-user.target
systemctl isolate graphical.target
DISPLAY=:0 XAUTHORITY=\$(ps aux | grep "X.*\\-auth" | grep -v grep | awk -F"-auth " '{print \$2}' | awk '{print \$1}') xhost | grep "SI:localuser:dcv$"
dcv create-session --type=virtual --owner ${user_name} --user ${user_name} virt
dcv list-sessions

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

systemctl enable dcvserver
echo "false" > /tmp/wait-handle-sent
stop_disable_svc firewalld
stop_disable_svc libvirtd
reboot

}

main


