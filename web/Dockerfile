# custom base image for trigger products
FROM aswincsekar/test-base:phusion
RUN apt-get update

RUN pip3 install --upgrade pip==20.1.1
RUN pip3 install --upgrade setuptools
RUN apt-get update && apt-get install -y software-properties-common cmake ffmpeg acoustid-fingerprinter libsasl2-dev python3-dev libldap2-dev libssl-dev

RUN \
  echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && \
  add-apt-repository -y ppa:webupd8team/java && \
  apt-get update && \
  apt-get install -y oracle-java8-installer python-regex && \
  rm -rf /var/lib/apt/lists/* && \
  rm -rf /var/cache/oracle-jdk8-installer

ENV JAVA_HOME /usr/lib/jvm/java-8-oracle
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.en
ENV LC_ALL=en_US.UTF-8

RUN pip3 install "opencv-contrib-python==3.3.0.10"

# Install dependencies.
COPY requirements /usr/src/app/requirements

WORKDIR /usr/src/app


RUN pip3 install --no-cache-dir -r requirements/production.txt

RUN pip3 install --upgrade botocore

COPY ./.aws /root/.aws

# Copy files into the container
COPY . /usr/src/app
