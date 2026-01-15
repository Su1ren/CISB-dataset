#! /bin/bash 
echo "obtain compilers now"
cp /etc/apt/sources.list /etc/apt/sources.list.bak

# get apt-key from ubuntu
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 40976EAF437D05B5
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 3B4FE6ACC0B21F32

echo  "deb http://dk.archive.ubuntu.com/ubuntu/ focal main universe"  >> /etc/apt/sources.list
echo  "deb http://dk.archive.ubuntu.com/ubuntu/ bionic main universe" >> /etc/apt/sources.list
echo  "deb http://dk.archive.ubuntu.com/ubuntu/ xenial main universe" >> /etc/apt/sources.list
echo  'deb http://dk.archive.ubuntu.com/ubuntu/ trusty main universe' >> /etc/apt/sources.list
echo  'deb http://archive.ubuntu.com/ubuntu/ jammy main universe' >> /etc/apt/sources.list

# get clang-17 from llvm repo
echo "deb [arch=amd64] https://apt.llvm.org/jammy/ llvm-toolchain-jammy-17 main" | tee /etc/apt/sources.list.d/llvm.list

# import the GPG key
wget -qO- https://apt.llvm.org/llvm-snapshot.gpg.key | tee /etc/apt/trusted.gpg.d/llvm.asc

apt-get update
apt-get install clang-12 clang-14 gcc-4.4 gcc-4.9 gcc-7 gcc-12 -y
apt update
apt install clang-11 clang-17 -y

# get gcc-4.1.2 binary from a repo
git clone https://github.com/Su1ren/gcc-4.1.2.git
ln -s /cisb_docker/CISB-dataset/gcc-4.1.2/bin/gcc-4.1 /usr/bin

# config bpf toolchain
apt install libbpfcc-dev libbpf-dev -y
ln -sf /usr/include/$(uname -m)-linux-gnu/asm /usr/include/asm

# old gcc runtime
ln -s /usr/lib/x86_64-linux-gnu/crt1.o ./
ln -s /usr/lib/x86_64-linux-gnu/crti.o ./
ln -s /usr/lib/x86_64-linux-gnu/crtn.o ./
ln -s /usr/lib/x86_64-linux-gnu/crt1.o ./reproduction_material
ln -s /usr/lib/x86_64-linux-gnu/crti.o ./reproduction_material
ln -s /usr/lib/x86_64-linux-gnu/crtn.o ./reproduction_material