FROM nginx:1.15
# RUN apt-get update
# RUN apt-get -y install certbot git-all

# RUN mkdir -p /tmp/certbot/public_html/.well-known/acme-challenge/
# RUN mkdir -p /usr/share/letsencrypt/.well-known/acme-challenge/

RUN rm /etc/nginx/conf.d/default.conf
COPY conf/proxy.conf /etc/nginx/conf.d/default.conf
# COPY ./hello.html /tmp/certbot/public_html/.well-known/acme-challenge/hello.html

# ARG CACHEBUST=6
# RUN rm -rf /etc/letsencrypt
# RUN git clone https://faiz-tessact:"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"@github.com/tessact/trigger-backend-certbot.git /etc/letsencrypt/


# RUN certbot certonly -m faiz@tessact.com --webroot -w /tmp/certbot/public_html/ -d trigger-one.tessact.com --agree-tos
#RUN certbot renew --dry-run --agree-tos
# WORKDIR /etc/letsencrypt/
# RUN git checkout trigger-one
