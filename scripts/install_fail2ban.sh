#!/bin/bash
# Install and configure fail2ban
DEBIAN_FRONTEND=noninteractive apt-get install -y fail2ban -q

# Configure sshd jail
cat > /etc/fail2ban/jail.local << 'EOF'
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
bantime = 3600
findtime = 600
EOF

systemctl enable fail2ban
systemctl restart fail2ban
sleep 2
fail2ban-client status sshd
