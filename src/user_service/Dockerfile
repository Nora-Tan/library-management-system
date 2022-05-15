FROM centos:7
WORKDIR /src
RUN yum install -y python3

COPY ./user_service/requirements.txt ./requirements.txt 
RUN pip3 install -r requirements.txt -i https://pypi.douban.com/simple/


ENV nameko_username=tan_admin nameko_password=Tan789 rabbitmq_host=rabbitmq
COPY . .

WORKDIR /src/user_service
CMD sh -c "nameko run user --broker amqp://$nameko_username:$nameko_password@$rabbitmq_host"