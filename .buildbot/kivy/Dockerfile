# A container for buildbot
FROM ubuntu:bionic AS kivy
# FROM ubuntu:20.04 AS buildbot-bionic

RUN apt-get update

RUN apt-get -y install sudo

RUN apt-get install -yq python-setuptools \
    python-setuptools libssl-dev libpq-dev python-prctl python-dev \
    python-dev python-virtualenv python-pip virtualenv \
    libssl-dev \
    python-dev \
    python3-virtualenv \
    python3-pip \

RUN sudo wget -0 "/usr/local/bin/travis2bash.sh" "https://git.bitmessage.org/Bitmessage/buildbot-scripts/raw/branch/master/travis2bash.sh"

RUN sudo chmod a+rx "/usr/local/bin/travis2bash.sh"
