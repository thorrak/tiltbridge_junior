FROM python:3.9-alpine

ENV PYTHONUNBUFFERED 1

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

# Add libcap so we can use setcap to allow the tiltbridge user to use bluetooth
RUN apk --no-cache add libcap bluez

COPY --chown=tiltbridge:tiltbridge ./docker/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start


COPY --chown=tiltbridge:tiltbridge . /app

# Add the django user to the container's dialout group
RUN addgroup tiltbridge dialout
RUN addgroup tiltbridge lp


# Correct the permissions for /app/log
#RUN chown tiltbridge /app/log/

# Fix Bluetooth permissions
RUN setcap cap_net_raw,cap_net_admin+eip /usr/local/bin/python3.9

USER tiltbridge

WORKDIR /app

ENTRYPOINT ["/entrypoint"]
