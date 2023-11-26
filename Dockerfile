FROM python:3.10

RUN mkdir /operator
ADD mysql_operator.py /operator/
ADD requirements.txt /operator/
ADD dunkel_tech /operator/
WORKDIR /operator
RUN pip install -r requirements.txt

CMD kopf run mysql_operator.py --verbose
