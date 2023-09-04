FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
 	sudo \
	systemd \
	openssh-server \
	git bsdmainutils tshark tcpdump net-tools && \
	apt-get clean

# Create admin_user with password and SSH access
RUN useradd -rm -d /home/admin -s /bin/bash admin && \
    echo 'admin:adminVlux' | chpasswd && \
    mkdir /home/admin/.ssh && \
    chmod 700 /home/admin/.ssh && \
    echo 'root:rootVlux' | chpasswd

# Copy public key for remote_user
COPY id_rsa.pub /home/admin/.ssh/authorized_keys

# Set permissions for remote_user SSH directory and authorized_keys file
RUN chown admin:admin -R /home/admin/.ssh && \
    chmod 600 /home/admin/.ssh/authorized_keys
RUN echo "PermitRootLogin yes" | sudo tee -a /etc/ssh/sshd_config

RUN echo "admin ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
RUN sudo mkdir /run/sshd

# Create denied and allowd users group
RUN groupadd disabled_users

# Deny ssh on disabled_users group
RUN echo "Match Group disabled_users\nDenyUsers *"  >> /etc/ssh/sshd_config

# Set the working directory to the cloned repository
WORKDIR /app

# Copy docker entrypoint
COPY docker-entrypoint.sh .
COPY traffic.py .
# Set entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]

# Run slave.py
CMD ["python", "slave.py"]
