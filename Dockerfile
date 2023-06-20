FROM python:3.9-alpine

ENV PYTHONUNBUFFERED 1

#RUN apt-get update \
#  # dependencies for building Python packages
##  && apt-get install -y build-essential \
#  # all the bluetooth libs
##  && apt-get install -y bluez \
#  && apt-get install -y bluez libcap2-bin libbluetooth3 libbluetooth-dev \
#  # cleaning up unused files
#  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
#  && rm -rf /var/lib/apt/lists/*


RUN addgroup --system tiltbridge \
    && adduser --system --ingroup tiltbridge tiltbridge


# Add piwheels (and our custom wheels!) to pip.conf to (slightly) speed up builds
COPY ./docker/pip.conf /etc/pip.conf

# Requirements are installed here to ensure they will be cached.
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

#COPY --chown=tiltbridge:tiltbridge ./docker/entrypoint /entrypoint
#RUN sed -i 's/\r$//g' /entrypoint
#RUN chmod +x /entrypoint


COPY --chown=tiltbridge:tiltbridge ./docker/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start


COPY --chown=tiltbridge:tiltbridge . /app

# Add the django user to the container's dialout group
#RUN usermod -a -G dialout tiltbridge
RUN addgroup dialout tiltbridge

# Correct the permissions for /app/log
#RUN chown tiltbridge /app/log/

# Fix Bluetooth permissions
RUN setcap cap_net_raw,cap_net_admin+eip /usr/local/bin/python3.9

USER tiltbridge

WORKDIR /app

ENTRYPOINT ["/start"]
