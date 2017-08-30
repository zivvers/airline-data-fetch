# combine Docker Outside of Docker (DOOD) capabilities
# with Selenium from miniconda image
FROM continuumio/miniconda
MAINTAINER Ziv Dreyfuss ziv@uchicago.edu

# we need to temporarily include backport repositories to install openjdk 8 and docker
RUN echo 'deb http://cdn-fastly.deb.debian.org/debian jessie-backports main' > /etc/apt/sources.list.d/jessie-backports.list && \
     apt-get -qqy update && \
         apt-get install --no-install-recommends -t jessie-backports -qqy openjdk-8-jre-headless ca-certificates-java 'docker.io'  && \
             rm /etc/apt/sources.list.d/jessie-backports.list && \
                 apt-get -qqy clean && \
                     rm -rf /var/lib/apt/lists/*

# install sudo in anticipation of less-privledged user
RUN apt-get -qqy update && \
    apt-get -qqy install sudo

# make less-privleged user
ENV CONDA_CALLER=ana

RUN useradd -s /bin/bash $CONDA_CALLER

# give CONDA_CALLER sudo privledges
RUN echo "$CONDA_CALLER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/notebook

# install Selenium!
RUN conda install -yqc conda-forge selenium

USER $CONDA_CALLER
WORKDIR /home/$CONDACALLER
