FROM centos:7
WORKDIR /src
RUN yum install -y python3

COPY ./inventory_service/requirements.txt ./requirements.txt 
RUN pip3 install -r requirements.txt -i https://pypi.douban.com/simple/


ENV nameko_username=tan_admin nameko_password=Tan789 rabbitmq_host=rabbitmq
COPY . .

WORKDIR /src/inventory_service
CMD sh -c "nameko run inventory --broker amqp://$nameko_username:$nameko_password@$rabbitmq_host"