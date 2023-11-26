FROM python:3.10

RUN mkdir /operator
ADD mysql_operator.py /operator/
ADD requirements.txt /operator/
WORKDIR /operator
RUN pip install -r requirements.txt

ADD dunkel_tech /operator/dunkel_tech/

CMD kopf run mysql_operator.py --verbose
