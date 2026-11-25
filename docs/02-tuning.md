# Kernel Tuning (Linux)

## Apply

```bash
sudo cp config/99-hydra.conf /etc/sysctl.d/99-hydra.conf
sudo sysctl --system
sudo iptables -t raw -A PREROUTING -p tcp --dport 80 -j NOTRACK
sudo iptables -t raw -A PREROUTING -p tcp --dport 443 -j NOTRACK
Revert
Bash
sudo rm -f /etc/sysctl.d/99-hydra.conf
sudo sysctl --system
sudo iptables -t raw -F